"""
scrapers/cg_dept_sites.py — generic scraper for Chhattisgarh department portals.

One defensive engine, many sites. Each department below is a plain NIC/HTML
site that publishes tenders/NITs either as an HTML table or as a page full of
PDF links. Rather than hand-write a brittle DOM scraper per department, we run
the same two-stage extractor over every configured site:

  1. find a tender listing <table> (named id, heading-adjacent, or keyword
     headers) and parse its rows, OR
  2. fall back to harvesting every NIT/tender/PDF link on the page.

Anything that fails (DNS, SSL, restructure) returns [] for that site and never
breaks the others or the pipeline. Add a new CG department by appending one
dict to _SITES — no new module required.

Currently configured:
  • CG Water Resources Department (WRD / Jal Sansadhan) — cgwrd.in / wrd.cg.gov.in
  • res.cg.gov.in                                        — CG state department portal
  • Balrampur district                                   — balrampur.gov.in

Standalone:  python -m scrapers.cg_dept_sites
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
}

_CG_DISTRICTS = [
    "raipur", "bilaspur", "durg", "bhilai", "korba", "raigarh", "rajnandgaon",
    "jagdalpur", "ambikapur", "janjgir", "champa", "dhamtari", "mahasamund",
    "kanker", "kondagaon", "narayanpur", "sukma", "dantewada", "bemetara",
    "balod", "gariaband", "balodabazar", "mungeli", "surguja", "balrampur",
    "surajpur", "jashpur", "korea", "sakti", "sarangarh", "manendragarh",
    "kabirdham", "kawardha", "bastar", "bijapur",
]

_SECTOR_MAP = {
    "Water & Irrigation": [
        "water", "irrigation", "dam", "canal", "pipeline", "nala", "anicut",
        "barrage", "reservoir", "weir", "sluice", "embankment", "jal", "sansadhan",
        "lift irrigation", "tubewell", "borewell", "pump", "sewage",
    ],
    "Civil Infrastructure": [
        "road", "bridge", "building", "construction", "pwd", "pavement",
        "drain", "culvert", "compound wall", "retaining wall", "infrastructure",
        "hostel", "ashram", "bhavan", "nirmaan", "repair", "maintenance",
        "renovation",
    ],
    "Electrical & Energy": [
        "electrical", "power", "lighting", "solar", "generator", "substation",
        "transformer",
    ],
    "Transport": ["vehicle", "transport", "hiring", "fleet"],
}

# name-id, human name, state, org label, default category, [candidate urls]
_SITES = [
    {
        "source_id": "cg_wrd",
        "name": "CG Water Resources Department",
        "state": "Chhattisgarh",
        "org": "CG Water Resources Department (Jal Sansadhan Vibhag)",
        "category": "Water & Irrigation",
        "urls": [
            "https://cgwrd.in/tender",
            "https://cgwrd.in/tenders",
            "https://cgwrd.in/en/tender",
            "https://cgwrd.in/",
            "https://wrd.cg.gov.in/tender",
            "https://wrd.cg.gov.in/",
        ],
    },
    {
        "source_id": "res_cg",
        "name": "res.cg.gov.in (CG Department Portal)",
        "state": "Chhattisgarh",
        "org": "Government of Chhattisgarh",
        "category": "Civil Infrastructure",
        "urls": [
            "https://res.cg.gov.in/tender",
            "https://res.cg.gov.in/tenders",
            "https://res.cg.gov.in/en/tender",
            "https://res.cg.gov.in/index.php/en/tender",
            "https://res.cg.gov.in/",
        ],
    },
    {
        "source_id": "balrampur_cg",
        "name": "Balrampur District (CG)",
        "state": "Chhattisgarh",
        "org": "District Administration, Balrampur (CG)",
        "category": "Civil Infrastructure",
        "district": "Balrampur",
        "urls": [
            "https://balrampur.gov.in/en/notice_category/tenders/",
            "https://balrampur.gov.in/en/tenders/",
            "https://balrampur.gov.in/notice_category/tenders/",
            "https://balrampur.gov.in/en/",
        ],
    },
]


def _infer_category(text: str, default: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return default


def _infer_district(text: str, fallback: str | None = None) -> str | None:
    t = text.lower()
    for d in _CG_DISTRICTS:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return fallback


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
            except Exception:
                return None
    except Exception:
        return None


def _find_table(soup: BeautifulSoup):
    for tid in ("tender_table", "tenderTable", "DataTable",
                "MainContent_GridView1", "gvtender"):
        t = soup.find("table", id=tid)
        if t:
            return t
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "caption"]):
        if "tender" in heading.get_text(strip=True).lower():
            nxt = heading.find_next("table")
            if nxt:
                return nxt
    for table in soup.find_all("table"):
        headers_text = " ".join(
            th.get_text(strip=True).lower() for th in table.find_all("th"))
        if any(kw in headers_text
               for kw in ("tender", "description", "work", "deadline",
                          "value", "nit", "closing")):
            return table
    return None


def _doc_link(cell, base: str) -> str | None:
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".doc", ".docx", ".zip", ".xls",
                                  ".xlsx")):
            return urljoin(base, href)
        if any(k in href.lower()
               for k in ("download", "tender", "nit", "pdf", "uploads",
                         "s3waas")):
            return urljoin(base, href)
    return None


def _extract_tender_links(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    """Harvest (title, url) for every notice/PDF link on the page."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        low_href, low_text = href.lower(), text.lower()
        is_doc = low_href.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx"))
        is_notice = any(kw in low_text
                        for kw in ("tender", "nit", "notice", "bid",
                                   "निविदा", "e-tender", "quotation"))
        if not (is_doc or is_notice):
            continue
        # Drop budgets / SOR / RTI / charters that look like tender PDFs.
        if not core.is_probable_tender_link(text, href):
            continue
        full = urljoin(base, href)
        if full in seen:
            continue
        seen.add(full)
        title = text
        if not title or len(title) < 5:
            title = (href.split("/")[-1].replace("%20", " ")
                     .replace("_", " ").replace("-", " "))
            title = re.sub(r"\.(pdf|docx?|xlsx?)$", "", title, flags=re.I).strip()
        out.append((title, full))
    return out


def _parse_page(html: str, site: dict, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = _find_table(soup)
    records: list[dict] = []
    default_district = site.get("district")

    if table:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        col: dict[str, int] = {}
        for i, h in enumerate(headers):
            if re.search(r"tender\s*no|reference|nit", h):
                col.setdefault("ref", i)
            elif re.search(r"description|title|name|work|subject", h):
                col.setdefault("title", i)
            elif re.search(r"value|amount|cost|estimated", h):
                col.setdefault("value", i)
            elif re.search(r"last\s*date|closing|deadline|submission", h):
                col.setdefault("deadline", i)
            elif re.search(r"download|document|pdf|link|view", h):
                col.setdefault("doc", i)
        if not col:
            col = {"ref": 1, "title": 2, "value": 3, "deadline": 4, "doc": 5}

        tbody = table.find("tbody") or table
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            def _c(key: str) -> str:
                idx = col.get(key)
                return (cells[idx].get_text(" ", strip=True)
                        if idx is not None and idx < len(cells) else "")

            title = _c("title") or _c("ref")
            if not title or len(title.strip()) < 5:
                continue
            if re.match(r"^(sr|s\.no|no\.?|#)$", title.strip().lower()):
                continue

            doc_idx = col.get("doc")
            doc_url = (_doc_link(cells[doc_idx], source_url)
                       if doc_idx is not None and doc_idx < len(cells) else None)
            if not doc_url:
                for cell in cells:
                    doc_url = _doc_link(cell, source_url)
                    if doc_url:
                        break
            reference = _c("ref")
            if not doc_url:
                row_id = reference or core.make_source_id(
                    site["source_id"], title, _c("deadline"))
                separator = "&" if "?" in source_url else "?"
                doc_url = (
                    f"{source_url}{separator}opporta_tender="
                    f"{quote(row_id, safe='')}"
                )

            combined = f"{title} {site['org']}"
            records.append(core.tender_record(
                title=title.strip(),
                state=site["state"],
                organization=site["org"],
                category=_infer_category(combined, site["category"]),
                district=_infer_district(combined, default_district),
                value_text=_c("value") or None,
                deadline=_c("deadline") or None,
                tender_no=reference or None,
                description=(f"NIT/Tender No: {reference}"
                             if reference else None),
                document_url=doc_url,
                source_portal=source_url,
                source_name=site["name"],
            ))
    else:
        for title, href in _extract_tender_links(soup, source_url)[:40]:
            if not title or len(title) < 5:
                continue
            combined = f"{title} {site['org']}"
            records.append(core.tender_record(
                title=title[:300],
                state=site["state"],
                organization=site["org"],
                category=_infer_category(combined, site["category"]),
                district=_infer_district(combined, default_district),
                document_url=href,
                source_portal=source_url,
                source_name=site["name"],
            ))

    return records


def _scrape_site(site: dict) -> list[dict]:
    """Try each candidate URL for one department; return first non-empty batch."""
    for url in site["urls"]:
        html = _fetch(url)
        if not html or len(html) < 500:
            continue
        records = _parse_page(html, site, url)
        if records:
            print(f"   cg_dept_sites[{site['source_id']}]: "
                  f"{len(records)} records (source: {url})")
            return records
    print(f"   cg_dept_sites[{site['source_id']}]: 0 records "
          f"(portal may be down or restructured)")
    return []


def scrape_selected(*source_ids: str) -> list[dict]:
    """Scrape selected configured CG department sites. Never raises."""
    wanted = set(source_ids)
    records: list[dict] = []
    for site in _SITES:
        if wanted and site["source_id"] not in wanted:
            continue
        try:
            records += _scrape_site(site)
        except Exception as exc:  # per-site isolation
            print(f"   cg_dept_sites[{site.get('source_id')}]: failed safely — "
                  f"{type(exc).__name__}: {exc}")
    print(f"   cg_dept_sites: {len(records)} total core.tender_record() ready")
    return records


def scrape_balrampur() -> list[dict]:
    """Collect Balrampur district notices without duplicating WRD/RES scrapers."""
    return scrape_selected("balrampur_cg")


def scrape() -> list[dict]:
    """Scrape every configured CG department site. Never raises."""
    return scrape_selected()


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                   errors="replace")
    found = scrape()
    print(f"\n{'-' * 70}\n  {len(found)} total records — CG department sites\n{'-' * 70}")
    for r in found[:6]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
