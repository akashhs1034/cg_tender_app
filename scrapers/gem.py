"""
scrapers/gem.py — Government e-Marketplace (gem.gov.in) bid scraper.

Targets:  https://bidplus.gem.gov.in/all-bids
Strategy: paginate the public bid listing, filter rows for CG / UP states and
          priority keywords (transport, logistics, coal, manpower, vehicle, etc.)
          — no login required for the public listing view.

DOM structure (confirmed pattern, may shift on GeM redesigns):
  GET https://bidplus.gem.gov.in/bidlists?searchBid=<kw>&state=<state>&pageNo=<n>
  Returns an HTML table inside <div class="table-responsive">:
    thead: Bid No. | Category | Bid Validity Date | Dept. Name | Quantity | StartDate | EndDate | EMD
  Or the generic listing with a table where columns are positional.

Fallback:  if the filtered search fails, fetch the un-filtered listing and
           post-filter client-side on state column.

Standalone:  python -m scrapers.gem
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

_BASE    = "https://bidplus.gem.gov.in"
_LIST    = f"{_BASE}/bidlists"
_DELAY   = 0.35  # seconds between requests
_MAX_PG  = int(os.getenv("GEM_MAX_PAGES", "30"))

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": f"{_BASE}/all-bids",
}

# States and high-priority keywords for this user's focus
_STATES  = ["Chhattisgarh", "Uttar Pradesh", "Chattisgarh", "CG", "UP"]
_PRIORITY_KW = [
    "transport", "transportation", "logistics", "vehicle hiring", "truck",
    "dumper", "coal", "loading", "unloading", "mining", "manpower",
    "security", "housekeeping", "warehousing", "freight", "material handling",
    "road", "construction", "electrical", "supply",
]

_SECTOR_MAP = {
    "Coal & Mining": ["coal", "mining", "cil", "secl", "nmdc", "mineral", "dumper", "loading", "unloading"],
    "Transport": ["transport", "vehicle", "truck", "bus", "fleet", "freight", "logistics", "material handling", "hauling"],
    "Manpower Supply": ["manpower", "security", "housekeeping", "labour", "workforce", "sweeping", "cleaning"],
    "Civil Infrastructure": ["road", "construction", "civil", "bridge", "building", "infrastructure", "maintenance"],
    "Electrical & Energy": ["electrical", "solar", "power", "transformer", "substation", "meter", "cable"],
    "Warehousing": ["warehouse", "storage", "depot", "godown"],
    "IT Services": ["software", "it ", "computer", "server", "network", "portal"],
}

_DISTRICT_CG = [
    "raipur", "bilaspur", "durg", "korba", "raigarh", "rajnandgaon",
    "jagdalpur", "ambikapur", "janjgir", "mahasamund", "dhamtari", "kanker",
    "kondagaon", "narayanpur", "sukma", "dantewada", "bemetara", "balod",
    "gariaband", "balodabazar", "mungeli", "surguja", "balrampur", "surajpur",
    "jashpur", "korea", "sakti", "sarangarh", "manendragarh", "kabirdham",
]
_DISTRICT_UP = [
    "lucknow", "kanpur", "agra", "varanasi", "prayagraj", "meerut", "ghaziabad",
    "noida", "mathura", "aligarh", "bareilly", "moradabad", "saharanpur",
    "gorakhpur", "jhansi", "faizabad", "ayodhya", "muzaffarnagar",
    "rampur", "shahjahanpur", "firozabad", "jaunpur", "mirzapur",
    "bulandshahr", "sambhal", "sultanpur", "azamgarh", "unnao",
]


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Government Supply"


def _infer_district(text: str, state: str) -> str | None:
    t = text.lower()
    candidates = _DISTRICT_CG if "chhattisgarh" in state.lower() or state == "CG" else _DISTRICT_UP
    for d in candidates:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return None


_DATA_EP = f"{_BASE}/all-bids-data"

# Location search terms (GeM bids are national; we pull CG/UP-relevant ones by
# searching state + major district names, which match buyer/location text).
_SEARCH_TERMS = [
    ("Chhattisgarh", "Chhattisgarh"), ("Raipur", "Chhattisgarh"),
    ("Bilaspur", "Chhattisgarh"),     ("Durg", "Chhattisgarh"),
    ("Korba", "Chhattisgarh"),        ("Bastar", "Chhattisgarh"),
    ("Uttar Pradesh", "Uttar Pradesh"), ("Lucknow", "Uttar Pradesh"),
    ("Kanpur", "Uttar Pradesh"),      ("Varanasi", "Uttar Pradesh"),
    ("Prayagraj", "Uttar Pradesh"),   ("Gorakhpur", "Uttar Pradesh"),
]


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


def _csrf_token(sess: requests.Session) -> str | None:
    """Load /all-bids to obtain the CSRF token + session cookies."""
    try:
        r = sess.get(f"{_BASE}/all-bids", timeout=30)
    except Exception as e:
        print(f"   gem: could not load all-bids — {e}")
        return None
    for pat in (r'name="csrf-token"\s+content="([^"]+)"',
                r'csrf_bd_gem_nk["\']?\s*[:=]\s*["\']([^"\']+)',
                r'"csrf_token"\s*:\s*"([^"]+)"'):
        m = re.search(pat, r.text)
        if m:
            return m.group(1)
    return None


def _first(v):
    """GeM returns most fields as single-element lists."""
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _fetch_bids(sess: requests.Session, token: str, term: str, page: int) -> list[dict]:
    import json
    payload = {
        "payload": json.dumps({
            "page": page,
            "param": {"searchBid": term, "searchType": "fullText"},
            "filter": {"bidStatusType": "ongoing_bids", "byEndDate": {}},
        }),
        "csrf_bd_gem_nk": token,
    }
    try:
        r = sess.post(_DATA_EP, data=payload, timeout=30,
                      headers={"X-Requested-With": "XMLHttpRequest",
                               "Referer": f"{_BASE}/all-bids"})
        r.raise_for_status()
        return r.json().get("response", {}).get("response", {}).get("docs", []) or []
    except Exception as e:
        print(f"   gem: search {term!r} p{page} failed — {e}")
        return []


def scrape() -> list[dict]:
    """Fetch ongoing GeM bids relevant to CG/UP via the JSON bid API."""
    sess = _make_session()
    records: list[dict] = []
    seen: set[str] = set()

    token = None
    for _ in range(3):
        token = _csrf_token(sess)
        if token:
            break
        time.sleep(1)
    if not token:
        print("   gem: WARNING — could not obtain CSRF token; GeM unavailable")
        return []

    max_pages = max(1, min(_MAX_PG // len(_SEARCH_TERMS) + 1, 5))
    for term, state in _SEARCH_TERMS:
        for page in range(1, max_pages + 1):
            docs = _fetch_bids(sess, token, term, page)
            if not docs:
                break
            for doc in docs:
                bid_no = _first(doc.get("b_bid_number"))
                if not bid_no or bid_no in seen:
                    continue
                seen.add(bid_no)
                item = (_first(doc.get("b_category_name"))
                        or _first(doc.get("bd_category_name")) or "GeM Bid")
                dept = (_first(doc.get("ba_official_details_deptName"))
                        or _first(doc.get("ba_official_details_minName"))
                        or "Government e-Marketplace")
                qty  = _first(doc.get("b_total_quantity"))
                end  = _first(doc.get("final_end_date_sort"))
                bid_id = _first(doc.get("b_id")) or doc.get("id")
                title = f"{str(item).title()} (Qty {qty})" if qty else str(item).title()
                records.append(core.tender_record(
                    title=title,
                    state=state,
                    organization=str(dept),
                    category=_infer_category(f"{item} {dept}"),
                    district=_infer_district(f"{item} {dept} {term}", state),
                    deadline=end,
                    description=f"GeM Bid No: {bid_no}",
                    document_url=f"{_BASE}/showbidDocument/{bid_id}",
                    source_portal="gem.gov.in",
                ))
            time.sleep(_DELAY)

    print(f"   gem: {len(records)} core.tender_record() objects ready")
    if not records:
        print("   gem: WARNING — 0 records returned; GeM portal may have restructured")
    return records


if __name__ == "__main__":
    import io as _io, logging as _log
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _log.basicConfig(level=_log.INFO, format="%(message)s")

    found = scrape()
    print(f"\n{'-'*70}")
    print(f"  {len(found)} total records — GeM")
    print(f"{'-'*70}")
    for r in found[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
