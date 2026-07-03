"""
scrapers/secl.py — South Eastern Coalfields Limited (SECL) tender scraper.

Source:  https://secl-cil.in/tenders
         (server-rendered DataTables; static HTTP is sufficient)

SECL is a Coal India subsidiary operating in Chhattisgarh and Madhya Pradesh.
Its tenders are highly relevant for coal transportation, dumper/truck hiring,
mining operations, railway siding, and industrial services.

NOTE (2026 site rebuild): SECL retired the old ASP.NET GridView portal
(/website/Tender/TenderList.aspx now 302-redirects to /index) and replaced it
with a plain-HTML listing at /tenders. Tenders live in three tables:
    table#example   — active e-Tenders / NITs  (the biddable notices)
    table#example1  — work-order extensions / corrigenda (tender-related)
    table#example2  — cancellations / debarments / LOA forfeitures (skipped;
                      administrative notices, not biddable tenders)
Each row is: Subject (title + embedded "dtd. DD.MM.YYYY") | download PDF link
under /writereaddata/<hash-or-filename>.

Standalone:  python -m scrapers.secl
"""

from __future__ import annotations

import re
import sys
import warnings
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_PORTAL   = "https://secl-cil.in/tenders"
_BASE_URL = "https://secl-cil.in"

# Tables holding biddable notices. 'example2' (cancellations/debarments/LOA
# forfeitures) is deliberately excluded — those are administrative, not tenders.
_TENDER_TABLE_IDS = ("example", "example1")

# Notice date embedded in the subject, e.g. "dtd. 19.06.2026" or "dated 8.5.2026".
_DATE_RE = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.secl-cil.in/",
}

_SECTOR_MAP = {
    "Coal & Mining": [
        "coal", "mining", "quarry", "overburden", "ob removal", "loading",
        "unloading", "excavation", "blast", "drilling", "colliery", "pit",
        "railway siding", "siding",
    ],
    "Transport": [
        "transport", "vehicle", "truck", "dumper", "tipper", "fleet",
        "hiring", "hauling", "freight", "logistics", "movement",
    ],
    "Manpower Supply": [
        "manpower", "security", "guard", "housekeeping", "labour", "workforce",
        "sweeping", "cleaning", "sanitation",
    ],
    "Civil Infrastructure": [
        "road", "construction", "civil", "building", "colony", "repair",
        "maintenance", "compound wall", "drain", "culvert",
    ],
    "Electrical & Energy": [
        "electrical", "power", "substation", "transformer", "cable",
        "motor", "pump", "hoist",
    ],
    "Manufacturing": [
        "supply", "purchase", "procurement", "equipment", "machinery",
        "spare", "explosive", "detonator",
    ],
}

_CG_DISTRICTS = [
    "korba", "raipur", "bilaspur", "raigarh", "janjgir", "champa",
    "mungeli", "korea", "ambikapur", "surguja", "surajpur", "jashpur",
    "balrampur", "bemetara", "durg", "rajnandgaon", "kabirdham",
]


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Coal & Mining"  # default: it's SECL


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _CG_DISTRICTS:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return None


def _fetch_html() -> str | None:
    # Try static HTTP first (fast)
    for verify in (True, False):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = requests.get(_PORTAL, headers=_HEADERS, timeout=30, verify=verify)
                r.raise_for_status()
                html = r.text
                # Accept only if it looks like it has table data
                if "<table" in html.lower() and len(html) > 3000:
                    return html
        except Exception:
            pass

    # Playwright fallback — ASP.NET portal may need JS to render the grid
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": _HEADERS["User-Agent"]})
            page.goto(_PORTAL, wait_until="networkidle", timeout=40000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
            return html if html and len(html) > 3000 else None
    except Exception as e:
        print(f"   secl: playwright fallback failed — {e}")
        return None


def _notice_date(subject: str) -> date | None:
    """Parse the notice date embedded in a subject line (dd.mm.yyyy)."""
    m = _DATE_RE.search(subject or "")
    if not m:
        return None
    dd, mm, yy = m.groups()
    try:
        return date(int(yy), int(mm), int(dd))
    except ValueError:
        return None


def scrape() -> list[dict]:
    """Return core.tender_record() dicts from the SECL /tenders listing."""
    html = _fetch_html()
    if not html:
        print("   secl: 0 records returned — portal may be down")
        return []

    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    seen: set[str] = set()

    for tid in _TENDER_TABLE_IDS:
        table = soup.find("table", id=tid)
        if not table:
            continue
        body = table.find("tbody") or table
        for row in body.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Column 0 = subject (title + embedded date); last col = download link.
            subject = cells[0].get_text(" ", strip=True)
            if not subject or len(subject) < 8:
                continue

            doc_url = None
            for a in row.find_all("a", href=True):
                doc_url = urljoin(_BASE_URL, a["href"])
                break

            pub = _notice_date(subject)
            rec = core.tender_record(
                title=subject[:300],
                state="Chhattisgarh",
                organization="South Eastern Coalfields Ltd (SECL)",
                category=_infer_category(subject),
                district=_infer_district(subject),
                deadline=None,
                published_date=pub.isoformat() if pub else None,
                description=(f"SECL tender notice dated {pub.isoformat()}"
                             if pub else "SECL tender notice"),
                document_url=doc_url or _PORTAL,
                source_portal="secl-cil.in",
            )
            if rec["source_id"] not in seen:
                seen.add(rec["source_id"])
                records.append(rec)

    print(f"   secl: {len(records)} core.tender_record() objects ready")
    if not records:
        print("   secl: WARNING — 0 records returned; portal may be down or "
              "restructured (expected tables #example / #example1 at /tenders)")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*70}")
    print(f"  {len(found)} total records — SECL")
    print(f"{'-'*70}")
    for r in found[:5]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
