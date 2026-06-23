"""
scrapers/samvad.py — Chhattisgarh Samvad (DPR e-RO portal) scraper.

samvad.cg.nic.in is the state's official advertising / Release-Order body. Unlike
the static dprcg.gov.in archive, it is actively updated and exposes TWO useful,
CAPTCHA-free feeds:

1. scrape_tenders()        -> Samvad's OWN procurement (PR / printing / agency
   RFPs) from SamvadTenderNotification.aspx. Recent (e.g. RFPs dated 2026).
   Returned as core.tender_record() for the main `tenders` table.

2. scrape_published_ads()  -> "Published Advertisements": the government tender
   NOTICES that Samvad placed in CG NEWSPAPERS, each carrying the newspaper name
   + publish date (e.g. "NAVBHARAT-RAIPUR 23/06/2026"). This is the official
   digital record of newspaper tender ads — exactly the offline/newspaper-tender
   gap. Returned as data_engine.offline_tender_record() for `offline_tenders`.

Standalone:  python -m scrapers.samvad
"""

from __future__ import annotations

import os
import re
import sys
import warnings
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core          # noqa: E402
import data_engine   # noqa: E402

warnings.simplefilter("ignore")

_BASE  = "https://samvad.cg.nic.in/"
_HOME  = _BASE + "Default.aspx"
_TENDERS = _BASE + "SamvadTenderNotification.aspx"
_MAX_AGE_DAYS = int(os.getenv("SAMVAD_MAX_AGE_DAYS", "120"))
_HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36")}

_DATE_RE = re.compile(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}")
# An advertisement is a tender (not recruitment/result/plain notice) if its
# title/type carries one of these signals.
_TENDER_KW = ["tender", "निविदा", "e-tender", "nit", "construction", "rfp", "eoi",
              "quotation", "auction", "bid", "e-auction", "expression of interest"]


def _get(url):
    try:
        r = requests.get(url, headers=_HEADERS, timeout=30, verify=False)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"   samvad: fetch failed {url} — {e}")
        return None


def _recent(d: date | None) -> bool:
    return (d is None) or ((date.today() - d).days <= _MAX_AGE_DAYS)


# ── Feed 1: Samvad's own tenders ──────────────────────────────────────────────
def scrape_tenders() -> list[dict]:
    r = _get(_TENDERS)
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        if "Tender_Uploades" not in a["href"]:
            continue
        par = a.find_parent(["tr", "li", "div"])
        ctx = par.get_text(" ", strip=True) if par else a.get_text(" ", strip=True)
        m = _DATE_RE.search(ctx)
        pub = core.parse_date(m.group(0)) if m else None
        if not _recent(pub):
            continue
        title = unquote(a["href"].split("/")[-1]).rsplit(".", 1)[0].strip()
        title = re.sub(r"[_]+", " ", title).strip()
        if not title or len(title) < 5:
            title = a.get_text(" ", strip=True) or "Chhattisgarh Samvad Tender"
        rec = core.tender_record(
            title=title[:300],
            state="Chhattisgarh",
            organization="Chhattisgarh Samvad (DPR e-RO Portal)",
            category="Printing & Advertising",
            deadline=None,
            document_url=urljoin(_BASE, a["href"]),
            description=(f"Published {pub.isoformat()}" if pub else None),
            source_portal="samvad.cg.nic.in",
        )
        if rec["source_id"] not in seen:
            seen.add(rec["source_id"])
            out.append(rec)
    print(f"   samvad tenders: {len(out)} recent Samvad procurement tenders")
    return out


# ── Feed 2: government tender ads published in newspapers via Samvad ───────────
def _parse_advert_detail(html: str):
    """Return (newspapers:list[str], latest_date:date|None) from a detail page."""
    soup = BeautifulSoup(html, "html.parser")
    papers, dates = [], []
    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) >= 3 and _DATE_RE.search(tds[-1]) and "-" in tds[1]:
            papers.append(tds[1])
            d = core.parse_date(_DATE_RE.search(tds[-1]).group(0))
            if d:
                dates.append(d)
    return papers, (max(dates) if dates else None)


def scrape_published_ads() -> list[dict]:
    r = _get(_HOME)
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    out, seen = [], set()
    links = []
    for a in soup.find_all("a", href=True):
        if "ViewPublishMatter" not in a["href"]:
            continue
        par = a.find_parent(["tr", "li", "div"])
        ctx = (par.get_text(" ", strip=True) if par else a.get_text(" ", strip=True))
        links.append((a.get_text(" ", strip=True), a["href"], ctx))

    for title_raw, href, ctx in links[:30]:
        low = f"{title_raw} {ctx}".lower()
        if not any(kw in low or kw in f"{title_raw} {ctx}" for kw in _TENDER_KW):
            continue   # skip recruitment / result / plain-notice adverts
        url = urljoin(_BASE, href)
        det = _get(url)
        papers, pub = _parse_advert_detail(det.text) if det else ([], None)
        if not _recent(pub):
            continue
        # advertiser = title before the trailing " - <type>"
        advertiser = re.split(r"\s+[-–]\s+", title_raw)[0].strip() or "Government Department"
        # district from the first paper's edition city ("NAVBHARAT - RAIPUR")
        district = None
        if papers:
            mcity = re.split(r"\s+[-–]\s+", papers[0])
            if len(mcity) > 1:
                district = mcity[-1].strip().title()
        paper_names = ", ".join(sorted({re.split(r"\s+[-–]\s+", p)[0].strip().title()
                                        for p in papers})) or None
        # keep ads distinct even when advertiser+date repeat (encrypted advt_no)
        advt = re.search(r"advt_no=([^&]+)", href)
        uniq = advt.group(1)[:10] if advt else title_raw[:12]
        rec = data_engine.offline_tender_record(
            title=f"{advertiser} — Tender (newspaper notice)"[:300],
            organization=advertiser,
            district=district,
            state="Chhattisgarh",
            published_date=(pub.isoformat() if pub else None),
            newspaper=paper_names,
            document_url=url,
            description=f"Govt tender advertisement published via CG Samvad ({uniq})",
        )
        rec["source_portal"] = "samvad.cg.nic.in (newspaper ad)"
        rec["source_id"] = core.make_source_id(advertiser, "samvad-ad", uniq)
        if rec["source_id"] not in seen:
            seen.add(rec["source_id"])
            out.append(rec)
    print(f"   samvad ads: {len(out)} newspaper tender advertisements (CG Samvad)")
    return out


def scrape() -> list[dict]:
    """Convenience: main-table tenders only (offline ads pushed separately)."""
    return scrape_tenders()


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("== Samvad own tenders ==")
    for t in scrape_tenders()[:6]:
        print(f"  • {t['title'][:64]}")
    print("\n== Newspaper tender advertisements ==")
    for a in scrape_published_ads()[:8]:
        print(f"  • [{a.get('district')}] {a['organization'][:34]} | {a.get('newspaper')} | {a.get('published_date')}")
