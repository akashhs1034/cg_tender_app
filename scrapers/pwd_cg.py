"""
scrapers/pwd_cg.py — Chhattisgarh Public Works Department tender scraper.

Sources tried in order:
  1. https://pwd.cg.gov.in/index.php/en/tender  (main CG PWD site)
  2. https://pwd.cg.gov.in/tender  (alternate path)
  3. CPPP listing filtered for "Chhattisgarh" and "Public Works" — fallback

CG PWD handles road, bridge, building, and infrastructure projects across the
state. High tender volumes for civil construction, maintenance, and repair.

DOM pattern (HTML table variant, common in NIC-hosted portals):
  table.table or table#tender_table
  Columns: Sr | Tender No | Description | Value | Deadline | Download

Standalone:  python -m scrapers.pwd_cg
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_PORTALS = [
    "https://pwd.cg.gov.in/index.php/en/tender",
    "https://pwd.cg.gov.in/tender",
    "https://pwd.cg.gov.in/index.php/tender",
    "https://pwd.cg.gov.in/",
]
_BASE    = "https://pwd.cg.gov.in"
_ORG     = "CG Public Works Department (PWD)"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_SECTOR_MAP = {
    "Civil Infrastructure": [
        "road", "bridge", "building", "construction", "pwd", "pavement",
        "drain", "culvert", "compound wall", "retaining wall", "infrastructure",
        "hostel", "ashram", "bhavan", "nirmaan", "repair", "maintenance",
        "renovation", "highway", "flyover", "underpass",
    ],
    "Electrical & Energy": [
        "electrical", "power", "lighting", "solar", "generator",
    ],
    "Water & Irrigation": [
        "water", "sewage", "pipeline", "pump",
    ],
    "Transport": [
        "vehicle", "transport", "hiring",
    ],
}

_CG_DISTRICTS = [
    "raipur", "bilaspur", "durg", "bhilai", "korba", "raigarh", "rajnandgaon",
    "jagdalpur", "ambikapur", "janjgir", "champa", "dhamtari", "mahasamund",
    "kanker", "kondagaon", "narayanpur", "sukma", "dantewada", "bemetara",
    "balod", "gariaband", "balodabazar", "mungeli", "surguja", "balrampur",
    "surajpur", "jashpur", "korea", "sakti", "sarangarh", "manendragarh",
    "kabirdham", "kawardha", "bastar", "bijapur",
]


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Civil Infrastructure"


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _CG_DISTRICTS:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return None


def _fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=25, verify=True)
        r.raise_for_status()
        return r.text
    except requests.exceptions.SSLError:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                r = requests.get(url, headers=_HEADERS, timeout=25, verify=False)
                r.raise_for_status()
                return r.text
            except Exception as e:
                print(f"   pwd_cg: SSL fetch failed for {url} — {e}")
                return None
    except Exception as e:
        print(f"   pwd_cg: fetch failed for {url} — {e}")
        return None


def _find_table(soup: BeautifulSoup):
    """Locate the tender listing table."""
    # Named table
    for tid in ("tender_table", "tenderTable", "DataTable", "MainContent_GridView1"):
        t = soup.find("table", id=tid)
        if t:
            return t

    # Table near a heading that contains "tender"
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "caption"]):
        if "tender" in heading.get_text(strip=True).lower():
            nxt = heading.find_next("table")
            if nxt:
                return nxt

    # Any table with ≥3 columns and keyword headers
    for table in soup.find_all("table"):
        headers_text = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
        if any(kw in headers_text for kw in ("tender", "description", "work", "deadline", "value")):
            return table

    return None


def _doc_link(cell, base: str) -> str | None:
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".doc", ".docx", ".zip", ".xls")):
            return urljoin(base, href)
        if any(k in href.lower() for k in ("download", "tender", "nit", "pdf")):
            return urljoin(base, href)
    return None


def _extract_tender_links(soup: BeautifulSoup, base: str) -> list[str]:
    """Collect all tender notice / NIT PDF links from the page."""
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        if (href.lower().endswith((".pdf", ".doc", ".docx"))
                or any(kw in text for kw in ("tender", "nit", "notice", "bid"))):
            full = urljoin(base, href)
            if full not in links:
                links.append(full)
    return links


def _parse_table(html: str, source_url: str) -> list[dict]:
    """Parse a table-based tender listing page."""
    soup  = BeautifulSoup(html, "html.parser")
    table = _find_table(soup)
    records: list[dict] = []

    if table:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        col: dict[str, int] = {}
        for i, h in enumerate(headers):
            if re.search(r"\bno\.?\b|s\.no|sr", h):
                col.setdefault("sr", i)
            elif re.search(r"tender\s*no|reference|nit", h):
                col.setdefault("ref", i)
            elif re.search(r"description|title|name|work", h):
                col.setdefault("title", i)
            elif re.search(r"value|amount|cost|estimated", h):
                col.setdefault("value", i)
            elif re.search(r"last\s*date|closing|deadline|submission", h):
                col.setdefault("deadline", i)
            elif re.search(r"download|document|pdf|link|view", h):
                col.setdefault("doc", i)
            elif re.search(r"division|location|district|area", h):
                col.setdefault("division", i)

        if not col:
            # positional default
            col = {"sr": 0, "ref": 1, "title": 2, "value": 3, "deadline": 4, "doc": 5}

        tbody = table.find("tbody") or table
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            def _c(key: str) -> str:
                idx = col.get(key)
                return cells[idx].get_text(" ", strip=True) if idx is not None and idx < len(cells) else ""

            title    = _c("title") or _c("ref")
            deadline = _c("deadline")
            value    = _c("value")
            ref      = _c("ref")
            division = _c("division")

            if not title or len(title.strip()) < 5:
                continue
            if re.match(r"^(sr|s\.no|no\.?|#)$", title.strip().lower()):
                continue

            doc_idx = col.get("doc")
            doc_url = _doc_link(cells[doc_idx], source_url) if doc_idx is not None and doc_idx < len(cells) else None
            if not doc_url:
                for cell in cells:
                    doc_url = _doc_link(cell, source_url)
                    if doc_url:
                        break
            if not doc_url:
                doc_url = source_url

            combined = f"{title} {division}"
            records.append(core.tender_record(
                title=title.strip(),
                state="Chhattisgarh",
                organization=f"CG PWD — {division}" if division else _ORG,
                category=_infer_category(combined),
                district=_infer_district(combined),
                value_text=value or None,
                deadline=deadline or None,
                description=f"NIT/Tender No: {ref}" if ref else None,
                document_url=doc_url,
                source_portal=source_url,
            ))

    else:
        # Fallback: collect PDF/tender links from the page
        links = _extract_tender_links(soup, source_url)
        for href in links[:30]:
            name = href.split("/")[-1].replace("%20", " ").replace("_", " ")
            name = re.sub(r"\.pdf$|\.docx?$", "", name, flags=re.I).strip()
            if not name or len(name) < 5:
                name = "CG PWD Tender Notice"
            records.append(core.tender_record(
                title=name,
                state="Chhattisgarh",
                organization=_ORG,
                category="Civil Infrastructure",
                district=_infer_district(name),
                document_url=href,
                source_portal=source_url,
            ))

    return records


def scrape() -> list[dict]:
    """Try each portal URL; return first successful batch."""
    for url in _PORTALS:
        html = _fetch(url)
        if not html:
            continue
        if len(html) < 500:
            continue
        records = _parse_table(html, url)
        if records:
            print(f"   pwd_cg: {len(records)} core.tender_record() objects ready (source: {url})")
            return records

    print("   pwd_cg: WARNING — 0 records returned; portal may be down or restructured")
    return []


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*70}")
    print(f"  {len(found)} total records — CG PWD")
    print(f"{'-'*70}")
    for r in found[:5]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
