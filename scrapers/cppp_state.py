"""
scrapers/cppp_state.py — State tender scraper for eprocure.gov.in/cppp.

No Playwright. No CAPTCHA. Uses requests + BeautifulSoup.

CAPTCHA situation
-----------------
The state search form (/mmpdata) requires an image CAPTCHA to apply a state
filter — and the server actually validates it.  However, the unfiltered paginated
listing loads without any CAPTCHA.  We therefore:
  1. Paginate /latestactivetendersnew/mmpdata?page=N  (no CAPTCHA required)
  2. Collect rows where the 'State Name' column matches TARGET_STATE
  3. Follow each matching row's detail link (/cppp/tendersfullviewmmp/<token>)
     to get the full tender metadata
  4. Return core.tender_record() objects

Detail page structure
---------------------
Tables use a (label | ':' | value) or (l1 | ':' | v1 | l2 | ':' | v2) pattern.
Key fields extracted:
  Organisation Name, Tender Title, Product Category, EMD, Location,
  Bid Submission End Date, Tender Document URL (points to state portal)

Value
-----
CPPP does not expose the estimated tender value in its state listing view.
EMD (Earnest Money Deposit) is available and stored in the 'emd' field;
value_text / value_lakhs remain None.

Env vars (optional)
-------------------
  CPPP_STATE     – state name to filter for (default: "Uttar Pradesh")
  CPPP_MAX_PAGES – listing pages to scan; each page has 10 rows (default: 100)

Standalone:  python -m scrapers.cppp_state
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

_BASE_LIST = "https://eprocure.gov.in/cppp/latestactivetendersnew/mmpdata"
_BASE_URL  = "https://eprocure.gov.in"

_TARGET_STATE = os.getenv("CPPP_STATE", "Uttar Pradesh")
_MAX_PAGES    = int(os.getenv("CPPP_MAX_PAGES", "100"))
_DELAY        = 0.3  # seconds between listing page fetches

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_UP_DISTRICTS = [
    "lucknow", "kanpur", "agra", "varanasi", "prayagraj", "allahabad",
    "meerut", "ghaziabad", "noida", "mathura", "aligarh", "bareilly",
    "moradabad", "saharanpur", "gorakhpur", "faizabad", "ayodhya",
    "jhansi", "muzaffarnagar", "rampur", "shahjahanpur", "firozabad",
    "jaunpur", "mirzapur", "hapur", "etawah", "amroha", "mau",
    "bulandshahr", "sambhal", "sultanpur", "azamgarh", "badaun",
    "unnao", "rae bareli", "sitapur", "lakhimpur", "bahraich",
    "ballia", "gonda", "basti", "deoria", "kushinagar", "maharajganj",
    "siddharthnagar", "shrawasti", "balrampur", "chitrakoot", "banda",
    "fatehpur", "hamirpur", "mahoba", "lalitpur", "amethi", "ambedkar nagar",
]

_CG_DISTRICTS = [
    "raipur", "bilaspur", "durg", "bhilai", "korba", "bastar", "raigarh",
    "rajnandgaon", "jagdalpur", "ambikapur", "janjgir", "champa", "dhamtari",
    "mahasamund", "kanker", "kondagaon", "narayanpur", "bijapur", "sukma",
    "dantewada", "bemetara", "balod", "gariaband", "balodabazar", "mungeli",
    "surguja", "balrampur", "surajpur", "jashpur", "korea", "sakti",
    "sarangarh", "manendragarh", "kabirdham", "kawardha",
]

_DISTRICTS_BY_STATE: dict[str, list[str]] = {
    "Uttar Pradesh": _UP_DISTRICTS,
    "Chhattisgarh": _CG_DISTRICTS,
}

_SECTOR_MAP = {
    "Civil Infrastructure": [
        "road", "bridge", "building", "construction", "pwd", "pavement",
        "drain", "culvert", "compound wall", "infrastructure", "nirmaan",
    ],
    "Electrical & Energy": [
        "electrical", "power", "solar", "energy", "substation",
        "transformer", "transmission", "distribution", "led", "light",
    ],
    "Water & Irrigation": [
        "water", "irrigation", "dam", "canal", "pipeline", "sewage",
        "borewell", "pump", "overhead tank", "sanitation",
    ],
    "Medical Procurement": [
        "medical", "medicine", "drug", "hospital", "health", "equipment",
        "surgical", "ambulance",
    ],
    "Municipal Projects": [
        "municipal", "nagar", "nigam", "ward", "solid waste", "urban",
    ],
    "IT Services": [
        "software", "it ", "computer", "server", "network", "portal",
    ],
    "Transport": ["transport", "vehicle", "fleet", "bus", "railway"],
}


def _infer_category(text: str, portal_category: str = "") -> str:
    if portal_category and portal_category.lower() not in ("na", "", "select"):
        return portal_category
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Civil Infrastructure"


def _infer_district(text: str, state: str) -> str | None:
    candidates = _DISTRICTS_BY_STATE.get(state, _UP_DISTRICTS)
    t = text.lower()
    for d in candidates:
        if re.search(r'\b' + re.escape(d) + r'\b', t):
            return d.title()
    return None


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": _UA,
        "Referer": _BASE_LIST,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def _parse_listing_page(html: str, target_state: str) -> list[dict]:
    """Extract rows matching target_state from one listing page."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    results = []
    for row in table.find_all("tr")[1:]:  # skip header
        tds = row.find_all("td")
        if len(tds) < 6:
            continue
        state_name = tds[5].get_text(strip=True)
        if state_name != target_state:
            continue
        link_tag = tds[4].find("a")
        results.append({
            "deadline_raw": tds[2].get_text(strip=True),
            "detail_href": link_tag["href"] if link_tag else "",
        })
    return results


def _parse_detail(html: str) -> dict:
    """Extract tender fields from a /tendersfullviewmmp/ detail page."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) == 3 and cells[1] == ":":
                fields[cells[0]] = cells[2]
            elif len(cells) == 6 and cells[1] == ":" and cells[4] == ":":
                fields[cells[0]] = cells[2]
                fields[cells[3]] = cells[5]

    return fields


def scrape() -> list[dict]:
    """Paginate CPPP state listing, collect TARGET_STATE rows, return core.tender_record() dicts."""
    sess = _make_session()
    raw: list[dict] = []   # (deadline_raw, detail_href)

    print(f"   cppp_state: scanning up to {_MAX_PAGES} pages for '{_TARGET_STATE}' tenders…")
    for page_num in range(_MAX_PAGES):
        url = _BASE_LIST if page_num == 0 else f"{_BASE_LIST}?page={page_num}"
        try:
            resp = sess.get(url, timeout=30)
            resp.raise_for_status()
            page_rows = _parse_listing_page(resp.text, _TARGET_STATE)
            raw.extend(page_rows)
        except Exception as e:
            print(f"   cppp_state: page {page_num} failed — {e}")
        time.sleep(_DELAY)

    print(f"   cppp_state: {len(raw)} {_TARGET_STATE} rows found across {_MAX_PAGES} pages")

    records: list[dict] = []
    seen_hrefs: set[str] = set()

    for item in raw:
        href = item["detail_href"]
        if not href or href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        try:
            det_resp = sess.get(href, timeout=30)
            det_resp.raise_for_status()
            f = _parse_detail(det_resp.text)

            title = f.get("Tender Title", "").strip()
            if not title:
                continue

            org = f.get("Organisation Name", "Government of " + _TARGET_STATE).strip()
            category_raw = f.get("Product Category", "").strip()
            emd_raw = f.get("EMD", "").replace("₹", "").replace(",", "").strip()
            location = f.get("Location", "").strip()
            deadline_str = (
                f.get("Bid Submission End Date", item["deadline_raw"]).split(" ")[0]
            )

            doc_url = f.get("Tender Document", href).strip()
            if not doc_url or doc_url.lower() in ("na", ""):
                doc_url = href

            combined = f"{title} {location} {org}"

            records.append(core.tender_record(
                title=title,
                state=_TARGET_STATE,
                organization=org,
                category=_infer_category(combined, category_raw),
                district=_infer_district(combined, _TARGET_STATE),
                value_text=None,
                emd=f"₹ {emd_raw}" if emd_raw else None,
                deadline=deadline_str,
                document_url=doc_url,
                source_portal="eprocure.gov.in/cppp",
            ))
            time.sleep(0.2)

        except Exception as e:
            print(f"   cppp_state: detail fetch failed — {e}")

    print(f"   cppp_state: {len(records)} core.tender_record() objects ready")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*72}")
    print(f"  {len(found)} total records — CPPP state={_TARGET_STATE}")
    print(f"{'-'*72}")
    for r in found[:3]:
        print(
            f"\n  source_id   : {r.get('source_id', '')}"
            f"\n  title       : {r.get('title', '')}"
            f"\n  organization: {r.get('organization', '')}"
            f"\n  deadline    : {r.get('deadline', '')}"
            f"\n  emd         : {r.get('emd', '')}"
            f"\n  category    : {r.get('category', '')}"
            f"\n  district    : {r.get('district', '')}"
            f"\n  document_url: {r.get('document_url', '')}"
        )
