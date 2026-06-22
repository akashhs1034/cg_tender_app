"""
scrapers/cppp_central.py — CG/UP-located CENTRAL government tenders from CPPP.

eprocure.gov.in/cppp publishes two CAPTCHA-free listings:
  * /latestactivetendersnew/mmpdata   -> state-portal-integrated tenders
                                         (already scraped by cppp_state)
  * /latestactivetendersnew/cpppdata  -> CENTRAL ministry / PSU tenders
                                         (CPWD, MES, AIIMS, IITs, Railways/IRCON,
                                          NTPC, coalfields, BSF…)

The cpppdata listing has NO 'State Name' column, but a large share of these
central tenders are for works/supplies physically located in CG or UP (military
stations, AIIMS Raipur/Gorakhpur, IIT Kanpur/BHU, CPWD divisions, NTPC plants).
Competitors surface these; we were missing them. This scraper paginates the
listing (no CAPTCHA) and keeps rows whose title/organisation mentions a CG or UP
location, tagging the inferred state.

Standalone:  python -m scrapers.cppp_central
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_LIST = "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"
_MAX_PAGES = int(os.getenv("CPPP_CENTRAL_MAX_PAGES", "80"))
_DELAY = 0.25

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://eprocure.gov.in/cppp/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Location keywords -> state. Word-boundary matched to avoid false positives
# (e.g. "agra" must not match inside another word). Distinctive names only.
_CG_KW = [
    "chhattisgarh", "raipur", "bilaspur", "durg", "bhilai", "korba", "raigarh",
    "rajnandgaon", "jagdalpur", "ambikapur", "bastar", "dhamtari", "mahasamund",
    "kanker", "jashpur", "surguja", "dantewada", "kondagaon", "balod",
]
_UP_KW = [
    "uttar pradesh", "lucknow", "kanpur", "varanasi", "prayagraj", "allahabad",
    "agra", "meerut", "gorakhpur", "bareilly", "jhansi", "noida", "ghaziabad",
    "aligarh", "moradabad", "saharanpur", "ayodhya", "mathura", "sonbhadra",
    "sultanpur", "gonda", "bahraich", "jaunpur", "azamgarh", "muzaffarnagar",
    "firozabad", "etawah", "rae bareli", "raebareli", "fatehpur", "banda",
    "bijnor", "amroha", "hardoi", "unnao", "sitapur", "barabanki",
]
_CG_RE = re.compile(r"\b(" + "|".join(map(re.escape, _CG_KW)) + r")\b", re.I)
_UP_RE = re.compile(r"\b(" + "|".join(map(re.escape, _UP_KW)) + r")\b", re.I)


def _infer_state(text: str) -> str | None:
    if _CG_RE.search(text):
        return "Chhattisgarh"
    if _UP_RE.search(text):
        return "Uttar Pradesh"
    return None


def _iso(raw: str) -> str | None:
    d = core.parse_date(raw)
    return d.isoformat() if d else None


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    out: list[dict] = []
    for row in table.find_all("tr")[1:]:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue
        title_cell = tds[4]
        org = tds[5].get_text(" ", strip=True)
        a = title_cell.find("a")
        # The anchor text is the work title; trailing text is ref/tender-id.
        title = (a.get_text(" ", strip=True) if a else title_cell.get_text(" ", strip=True))
        full_cell = title_cell.get_text(" ", strip=True)
        haystack = f"{full_cell} {org}"

        state = _infer_state(haystack)
        if not state:
            continue

        doc_url = a["href"] if (a and a.get("href")) else _LIST
        # tender ref/id is the part of the cell after the title
        ref = full_cell.replace(title, "").strip(" /") or None

        out.append(core.tender_record(
            title=title or full_cell,
            state=state,
            organization=org or "Central Government / PSU",
            category=None,
            deadline=tds[2].get_text(" ", strip=True),
            description=(f"Tender Ref: {ref}" if ref else None),
            document_url=doc_url,
            source_portal="eprocure.gov.in/cppp (central)",
        ))
    return out


def scrape() -> list[dict]:
    """Paginate cpppdata; return CG/UP-located central tender records."""
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
            print(f"   cppp_central: page {page} failed — {e}")
            continue
        if not batch and page > 2:
            # No CG/UP hits on this page is normal; keep going a bit, but if the
            # table itself is empty (end of listing) stop.
            soup = BeautifulSoup(r.text, "html.parser")
            if not soup.find("table"):
                break
        for rec in batch:
            if rec["source_id"] not in seen:
                seen.add(rec["source_id"])
                records.append(rec)
        time.sleep(_DELAY)

    print(f"   cppp_central: {len(records)} CG/UP-located central tenders "
          f"(scanned up to {_MAX_PAGES} pages)")
    if not records:
        print("   cppp_central: WARNING — 0 records; listing may have changed")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    found = scrape()
    from collections import Counter
    print(f"\n{'-'*70}\n  {len(found)} CG/UP central tenders\n{'-'*70}")
    print("  by state:", dict(Counter(r["state"] for r in found)))
    for r in found[:8]:
        print(f"\n  [{r['state']}] {r['title'][:64]}")
        print(f"     {r['organization']}  | closes {r['deadline']}")
