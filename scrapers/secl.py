"""
scrapers/secl.py — South Eastern Coalfields Limited (SECL) tender scraper.

Source:  https://www.secl-cil.in/website/Tender/TenderList.aspx
         (ASP.NET WebForms, no JS required for initial listing)

SECL is a Coal India subsidiary operating in Chhattisgarh and Madhya Pradesh.
Its tenders are highly relevant for coal transportation, dumper/truck hiring,
mining operations, railway siding, and industrial services.

DOM structure:
  table#ctl00_ContentPlaceHolder1_GridView1  (or similar ContentPlaceHolder ID)
  Columns:
    Sr. No. | Tender Ref. | Tender Title / Description | Last Date | EMD | Download

Fallback: if GridView not found, try any <table> with a "tender" header row.

Standalone:  python -m scrapers.secl
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_PORTAL   = "https://www.secl-cil.in/website/Tender/TenderList.aspx"
_BASE_URL = "https://www.secl-cil.in"

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


def _find_grid(soup: BeautifulSoup):
    """Find the tender table in the page."""
    # Primary: ASP.NET GridView with known partial ID
    for table in soup.find_all("table"):
        tid = table.get("id", "")
        if "Grid" in tid or "GridView" in tid or "tender" in tid.lower():
            return table

    # Fallback: first table with a header containing "tender" or "description"
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if any(h in ("tender", "description", "title", "scope") for h in headers):
            return table

    # Last resort: largest table on the page
    tables = soup.find_all("table")
    return max(tables, key=lambda t: len(t.find_all("tr")), default=None) if tables else None


def _doc_url(cell, base=_BASE_URL) -> str | None:
    """Extract first download/PDF link from a table cell."""
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".doc", ".docx", ".zip", ".xls", ".xlsx")):
            return urljoin(base, href)
        if any(kw in href.lower() for kw in ("download", "document", "tender", "pdf")):
            return urljoin(base, href)
    return None


def scrape() -> list[dict]:
    """Return core.tender_record() dicts from SECL tender listing."""
    html = _fetch_html()
    if not html:
        print("   secl: 0 records returned — portal may be down")
        return []

    soup = BeautifulSoup(html, "html.parser")
    grid = _find_grid(soup)
    if not grid:
        print("   secl: tender table not found — portal may have restructured")
        return []

    # Determine column order from headers
    headers = [th.get_text(strip=True).lower() for th in grid.find_all("th")]
    col: dict[str, int] = {}
    for i, h in enumerate(headers):
        if any(x in h for x in ("sr", "s.no", "sno", "no.")):
            col.setdefault("sr", i)
        elif any(x in h for x in ("ref", "no", "number", "nit", "tender no")):
            col.setdefault("ref", i)
        elif any(x in h for x in ("title", "description", "scope", "work", "name")):
            col.setdefault("title", i)
        elif any(x in h for x in ("last", "closing", "deadline", "date")):
            col.setdefault("deadline", i)
        elif "emd" in h:
            col.setdefault("emd", i)
        elif any(x in h for x in ("download", "document", "pdf", "link")):
            col.setdefault("doc", i)
        elif any(x in h for x in ("division", "area", "location", "unit")):
            col.setdefault("division", i)
        elif any(x in h for x in ("value", "amount", "estimated", "cost")):
            col.setdefault("value", i)

    # Default positions if headers not matched (positional fallback)
    if not col:
        col = {"sr": 0, "ref": 1, "title": 2, "deadline": 3, "emd": 4, "doc": 5}

    records: list[dict] = []
    tbody = grid.find("tbody") or grid
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        def _c(key: str, default="") -> str:
            idx = col.get(key)
            if idx is None or idx >= len(cells):
                return default
            return cells[idx].get_text(" ", strip=True)

        sr = _c("sr")
        if sr and not re.match(r"^\d+$", sr.strip()):
            continue  # header repeat or non-data row

        ref      = _c("ref")
        title    = _c("title")
        deadline = _c("deadline")
        emd      = _c("emd")
        division = _c("division")
        value    = _c("value")

        if not title or len(title) < 5:
            continue

        # Get document URL from link cell or any cell
        doc_url = None
        doc_idx = col.get("doc")
        if doc_idx is not None and doc_idx < len(cells):
            doc_url = _doc_url(cells[doc_idx])
        if not doc_url:
            for cell in cells:
                doc_url = _doc_url(cell)
                if doc_url:
                    break
        if not doc_url:
            doc_url = _PORTAL

        combined = f"{title} {division}"
        records.append(core.tender_record(
            title=title,
            state="Chhattisgarh",
            organization=f"SECL — {division}" if division else "South Eastern Coalfields Ltd (SECL)",
            category=_infer_category(combined),
            district=_infer_district(combined),
            value_text=value or None,
            emd=emd or None,
            deadline=deadline or None,
            description=f"Tender Ref: {ref}" if ref else None,
            document_url=doc_url,
            source_portal="secl-cil.in",
        ))

    print(f"   secl: {len(records)} core.tender_record() objects ready")
    if not records:
        print("   secl: WARNING — 0 records returned; portal may be down or restructured")
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
