"""scrapers/cspdcl.py — Chhattisgarh State Power Companies tender scraper.

Source: https://cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=1

These are GENUINELY separate tenders from eproc.cgstate.gov.in — the three
CG power companies (CSPDCL distribution, CSPGCL generation, CSPTCL
transmission) publish on their own ASP.NET portal, not the central state
portal.

DOM structure (confirmed 2026-06-20):
  table#MainContent_GVTenderDetails.TableBG is the tender GridView (73 rows).
  Column layout:
    [0] Sr.No  [1] Issuing Office  [2] Tender Notice No.  [3] Scope of Work
    [4] Estimated Cost (Rs.)  [5] Closing Date & Time  [6] Opening Date
    [7] S.no (internal ID)  [8] LINK  [9] open time  [10] Subm time
    [11] View Tender Document (anchors with __doPostBack PDF paths)
    [12+] Remark/RFx ID
  Document links are javascript:__doPostBack('...$lb/SERNO/Type/File.pdf','').
  Path after '$lb' → reconstruct as https://cspdcl.co.in/cseb/<path>.
"""
from __future__ import annotations

import logging
import os
import re
import warnings
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import core

logger = logging.getLogger(__name__)

_PORTAL_TEMPLATE = "https://cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag={flag}"
_BASE_URL   = "https://cspdcl.co.in/cseb"
_FLAGS = tuple(
    int(value) for value in os.getenv(
        "CSPDCL_PARAMFLAGS", "1,2,3,4,5,6,7,8,9,10,11,12"
    ).split(",") if value.strip().isdigit()
)
_MAX_PAGES = max(1, int(os.getenv("CSPDCL_MAX_PAGES_PER_FLAG", "20")))
_HEADERS    = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_CG_DISTRICTS = [
    "raipur", "bilaspur", "durg", "bhilai", "korba", "bastar", "raigarh",
    "rajnandgaon", "jagdalpur", "ambikapur", "janjgir", "champa", "dhamtari",
    "mahasamund", "kanker", "kondagaon", "narayanpur", "bijapur", "sukma",
    "dantewada", "bemetara", "balod", "gariaband", "balodabazar", "mungeli",
    "surguja", "balrampur", "surajpur", "jashpur", "korea", "sakti",
    "sarangarh", "manendragarh", "kabirdham", "kawardha",
]

_SECTOR_MAP = {
    "Electrical & Energy": [
        "transformer", "cable", "substation", "meter", "distribution", "solar",
        "rooftop", "capacitor", "conductor", "lt ab", "inverter", "electrical",
        "electric", "power", "dtr", "transmission", "crgo", "bess", "battery",
        "ups", "generator", "feeder",
    ],
    "Civil Infrastructure": [
        "road", "building", "construction", "civil", "compound wall", "fencing",
        "hostel", "room", "repair", "maintenance", "cleaning", "sweeping",
        "approach", "drainage",
    ],
    "IT Services": [
        "software", "it ", "computer", "server", "network", "portal", "erp",
        "sap", "application", "facility management", "fms", "database",
        "migration", "eitc",
    ],
    "Transport": [
        "vehicle", "car", "jeep", "pool vehicle", "hiring of",
    ],
}


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Electrical & Energy"  # default: it's a power company portal


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _CG_DISTRICTS:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return None


def _doc_url_from_postback(href: str) -> str | None:
    """Extract PDF URL from javascript:__doPostBack('...','') href attribute."""
    m = re.search(r"__doPostBack\('([^']+)'", href)
    if not m:
        return None
    # arg = "ctl00$MainContent$GVTenderDetails$ctl14$lb/136785/A. NIT/NIT_TD103946.pdf"
    arg = m.group(1)
    idx = arg.find("$lb")
    if idx < 0:
        return None
    path = arg[idx + 3:]  # "/136785/A. NIT/NIT_TD103946.pdf"
    if not path.startswith("/"):
        return None
    return _BASE_URL + quote(path, safe="/.")


def _request(session: requests.Session, method: str, url: str,
             *, data: dict | None = None) -> requests.Response | None:
    try:
        r = session.request(
            method, url, headers=_HEADERS, data=data, timeout=35, verify=True)
        r.raise_for_status()
        return r
    except requests.exceptions.SSLError:
        logger.warning("cspdcl: SSL verify failed — retrying without verify")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                r = session.request(
                    method, url, headers=_HEADERS, data=data,
                    timeout=35, verify=False)
                r.raise_for_status()
                return r
            except Exception as exc:
                logger.warning("cspdcl: fetch failed (no-verify) — %s", exc)
                return None
    except Exception as exc:
        logger.warning("cspdcl: fetch failed — %s", exc)
        return None


def _parse_grid(html: str, source_url: str) -> list[dict]:
    """Parse one page of a CSPDCL regional GridView."""
    soup = BeautifulSoup(html, "html.parser")
    grid = soup.find("table", id="MainContent_GVTenderDetails")
    if not grid:
        return []

    # recursive=False so nested doc-link rows inside cells aren't counted.
    container = grid.find("tbody") or grid
    rows = container.find_all("tr", recursive=False)

    records: list[dict] = []
    for row in rows:
        cells = row.find_all("td", recursive=False)
        if len(cells) < 6:
            continue
        sr = cells[0].get_text(strip=True)
        if not sr.isdigit():
            continue  # header row or malformed

        org       = cells[1].get_text(strip=True)
        tender_no = cells[2].get_text(strip=True)
        title     = cells[3].get_text(" ", strip=True)
        value_raw = cells[4].get_text(strip=True)
        # "09/07/2026  01:30PM" → keep only the date part
        deadline  = cells[5].get_text(strip=True).split()[0] if len(cells) > 5 else None

        if not title or len(title) < 5:
            continue

        # First __doPostBack PDF link in the "View Tender Document" cell
        doc_url: str | None = None
        if len(cells) > 11:
            for a in cells[11].find_all("a", href=True):
                doc_url = _doc_url_from_postback(a["href"])
                if doc_url:
                    break

        combined = f"{title} {org}"
        fallback_id = tender_no or core.make_source_id(org, title, deadline)
        fallback_url = (
            f"{source_url}&opporta_tender={quote(fallback_id, safe='')}"
        )
        records.append(core.tender_record(
            title=title,
            state="Chhattisgarh",
            organization=org or "CSPDCL / CG Power Companies",
            category=_infer_category(combined),
            district=_infer_district(combined),
            tender_no=tender_no or None,
            value_text=value_raw or None,
            deadline=deadline,
            description=f"Tender Notice No. {tender_no}",
            # A shared feed URL would make the deduplicator collapse every row
            # lacking a PDF into one tender. Preserve a stable row identity.
            document_url=doc_url or fallback_url,
            source_name="CSPDCL / Chhattisgarh State Power Companies",
            source_portal=source_url,
            source_type="department_site",
        ))
    return records

def _postback_for_page(soup: BeautifulSoup,
                       wanted_page: int) -> tuple[str, str] | None:
    """Return (__EVENTTARGET, __EVENTARGUMENT) for the next GridView page."""
    for anchor in soup.find_all("a", href=True):
        match = re.search(
            r"__doPostBack\('([^']+)','Page\$(\d+)'\)", anchor["href"])
        if match and int(match.group(2)) == wanted_page:
            return match.group(1), f"Page${wanted_page}"
    return None


def _hidden_form_fields(soup: BeautifulSoup) -> dict[str, str]:
    fields: dict[str, str] = {}
    for element in soup.select("form input[type=hidden][name]"):
        fields[element["name"]] = element.get("value", "")
    return fields


def scrape() -> list[dict]:
    """Collect every configured CSPDCL region and all GridView pages."""
    session = requests.Session()
    all_records: list[dict] = []
    successful_feeds = 0

    for flag in _FLAGS:
        source_url = _PORTAL_TEMPLATE.format(flag=flag)
        response = _request(session, "GET", source_url)
        if response is None:
            continue
        successful_feeds += 1
        page_number = 1

        while response is not None and page_number <= _MAX_PAGES:
            page_records = _parse_grid(response.text, source_url)
            all_records.extend(page_records)

            soup = BeautifulSoup(response.text, "html.parser")
            postback = _postback_for_page(soup, page_number + 1)
            if postback is None:
                break
            target, argument = postback
            payload = _hidden_form_fields(soup)
            payload["__EVENTTARGET"] = target
            payload["__EVENTARGUMENT"] = argument
            response = _request(
                session, "POST", response.url, data=payload)
            page_number += 1

    records = core.merge_duplicate_records(all_records, "tender")
    logger.info(
        "cspdcl: %d unique records from %d/%d regional feeds",
        len(records), successful_feeds, len(_FLAGS),
    )
    if not records:
        logger.warning(
            "cspdcl: 0 records returned — portal may be down or restructured")
    return records


if __name__ == "__main__":
    import io
    import sys
    import logging as _logging
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _logging.basicConfig(level=_logging.INFO, format="%(message)s")

    found = scrape()
    print(f"\n{'-' * 68}")
    print(f"  {len(found)} total records — CSPDCL")
    print(f"{'-' * 68}")
    for r in found[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
