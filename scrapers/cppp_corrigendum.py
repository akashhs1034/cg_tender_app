"""
scrapers/cppp_corrigendum.py — CPPP tender-amendment (corrigendum) scraper.

Why this matters: a corrigendum changes a live tender (new dates, specs, EMD).
Missing one can disqualify a bid — so contractors need to know the moment a
tender they're tracking is amended. The big platforms (Tender Tiger, BidAssist)
all surface this; this scraper closes that gap for CG + UP.

Source: https://eprocure.gov.in/cppp/latestactivecorrigendumsnew/mmpdata
The listing loads WITHOUT a CAPTCHA (the CAPTCHA only guards the search form),
exactly like the active-tenders view, and carries a 'State Name' column we
filter on.

Listing columns:
  0 Sl.No | 1 e-Published Date | 2 Bid Submission Closing Date |
  3 Tender Opening Date | 4 Title/Ref (+ corrigendum detail link) |
  5 State Name | 6 (tender detail link)

Standalone:  python -m scrapers.cppp_corrigendum
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_LIST = "https://eprocure.gov.in/cppp/latestactivecorrigendumsnew/mmpdata"
_TARGET_STATES = {"Uttar Pradesh", "Chhattisgarh"}
_MAX_PAGES = int(os.getenv("CORRIG_MAX_PAGES", "40"))
_DELAY = 0.3

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://eprocure.gov.in/cppp/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _iso(raw: str) -> str | None:
    d = core.parse_date(raw)
    return d.isoformat() if d else None


def corrigendum_record(*, title, state, published_date, closing_date,
                       opening_date, corrigendum_url, tender_url) -> dict:
    title = (title or "Tender Corrigendum").strip()[:300]
    return {
        "source_id": core.make_source_id(title, state, published_date),
        "title": title,
        "state": (state or "").strip() or None,
        "published_date": _iso(published_date),
        "closing_date": _iso(closing_date),
        "opening_date": _iso(opening_date),
        "corrigendum_url": (corrigendum_url or "").strip() or None,
        "tender_url": (tender_url or "").strip() or None,
        "source_portal": "eprocure.gov.in/cppp",
        "scraped_at": core._now_iso(),
    }


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    out = []
    for row in table.find_all("tr")[1:]:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue
        state = tds[5].get_text(strip=True)
        if state not in _TARGET_STATES:
            continue
        corr_a = tds[4].find("a")
        tend_a = tds[6].find("a") if len(tds) > 6 else None
        out.append(corrigendum_record(
            title=tds[4].get_text(strip=True),
            state=state,
            published_date=tds[1].get_text(strip=True),
            closing_date=tds[2].get_text(strip=True),
            opening_date=tds[3].get_text(strip=True),
            corrigendum_url=(corr_a["href"] if corr_a and corr_a.get("href") else ""),
            tender_url=(tend_a["href"] if tend_a and tend_a.get("href") else ""),
        ))
    return out


def scrape() -> list[dict]:
    """Paginate the CPPP corrigendum listing; return CG/UP amendment records."""
    sess = requests.Session()
    sess.headers.update(_HEADERS)
    records: list[dict] = []
    seen: set[str] = set()

    for page in range(_MAX_PAGES):
        url = _LIST if page == 0 else f"{_LIST}?page={page}"
        try:
            r = sess.get(url, timeout=30)
            r.raise_for_status()
            batch = _parse_page(r.text)
        except Exception as e:
            print(f"   cppp_corrigendum: page {page} failed — {e}")
            continue
        for rec in batch:
            if rec["source_id"] not in seen:
                seen.add(rec["source_id"])
                records.append(rec)
        time.sleep(_DELAY)

    print(f"   cppp_corrigendum: {len(records)} CG/UP corrigendum records ready")
    if not records:
        print("   cppp_corrigendum: WARNING — 0 records; portal may have changed")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    found = scrape()
    print(f"\n{'-'*70}\n  {len(found)} total corrigendums — CG/UP\n{'-'*70}")
    for r in found[:5]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<16}: {v}")
