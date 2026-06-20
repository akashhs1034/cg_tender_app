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


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


def _is_target_state(state_cell: str) -> bool:
    s = state_cell.strip().lower()
    return any(t.lower() in s for t in _STATES)


def _has_priority_kw(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _PRIORITY_KW)


def _parse_table(html: str, default_state: str = "") -> list[dict]:
    """Extract rows from the GeM bid listing table."""
    soup = BeautifulSoup(html, "html.parser")
    rows_out = []

    # Try the standard GeM table structure
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not headers:
            continue

        # Map header names to column indices
        col = {}
        for i, h in enumerate(headers):
            if "bid no" in h or "bid number" in h:
                col["bid_no"] = i
            elif "category" in h:
                col["category"] = i
            elif "end date" in h or "bid validity" in h or "validity" in h:
                col["deadline"] = i
            elif "dept" in h or "department" in h or "ministry" in h:
                col["dept"] = i
            elif "state" in h:
                col["state"] = i
            elif "start" in h:
                col["start"] = i
            elif "emd" in h:
                col["emd"] = i
            elif "value" in h or "amount" in h:
                col["value"] = i

        if not col:
            continue

        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue

            def _cell(key):
                idx = col.get(key)
                if idx is None or idx >= len(cells):
                    return ""
                return cells[idx].get_text(strip=True)

            bid_no   = _cell("bid_no")
            cat      = _cell("category")
            deadline = _cell("deadline")
            dept     = _cell("dept") or "Government of India"
            state_v  = _cell("state") or default_state
            emd      = _cell("emd")
            val      = _cell("value")

            if not bid_no:
                continue

            # State filter
            if not _is_target_state(state_v):
                continue

            # Link from first anchor in bid_no cell
            idx = col.get("bid_no", 0)
            a = cells[idx].find("a") if idx < len(cells) else None
            href = a["href"] if a and a.get("href") else ""
            url = (href if href.startswith("http") else f"{_BASE}{href}") if href else f"{_BASE}/all-bids"

            combined = f"{cat} {dept} {state_v}"
            actual_state = ("Chhattisgarh" if "chhattisgarh" in state_v.lower() or "cg" == state_v.strip().lower()
                            else "Uttar Pradesh" if "uttar" in state_v.lower() or "up" == state_v.strip().lower()
                            else state_v)

            rows_out.append(core.tender_record(
                title=cat or f"GeM Bid {bid_no}",
                state=actual_state,
                organization=dept,
                category=_infer_category(combined),
                district=_infer_district(combined, actual_state),
                value_text=val or None,
                emd=emd or None,
                deadline=deadline or None,
                description=f"GeM Bid No: {bid_no}",
                document_url=url,
                source_portal="gem.gov.in",
            ))

    return rows_out


def _fetch_page(sess: requests.Session, page: int, keyword: str = "", state: str = "") -> str | None:
    params: dict = {"pageNo": page}
    if keyword:
        params["searchBid"] = keyword
    if state:
        params["state"] = state
    try:
        r = sess.get(_LIST, params=params, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"   gem: page {page} kw={keyword!r} state={state!r} failed — {e}")
        return None


def scrape() -> list[dict]:
    """
    Fetch GeM bids for CG and UP matching priority logistics/transport/coal keywords.
    Returns list of core.tender_record() dicts.
    """
    sess = _make_session()
    records: list[dict] = []
    seen_ids: set[str] = set()

    # Strategy 1: search by keyword for CG and UP
    search_pairs = [
        ("transport", "Chhattisgarh"),
        ("coal", "Chhattisgarh"),
        ("vehicle hiring", "Chhattisgarh"),
        ("manpower", "Chhattisgarh"),
        ("transport", "Uttar Pradesh"),
        ("vehicle hiring", "Uttar Pradesh"),
        ("manpower", "Uttar Pradesh"),
        ("construction", "Chhattisgarh"),
    ]

    for kw, state in search_pairs:
        for pg in range(1, min(_MAX_PG // len(search_pairs) + 1, 6)):
            html = _fetch_page(sess, pg, keyword=kw, state=state)
            if not html:
                break
            batch = _parse_table(html, default_state=state)
            if not batch:
                break  # no more rows
            for rec in batch:
                sid = rec["source_id"]
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    records.append(rec)
            time.sleep(_DELAY)

    # Strategy 2: general listing without keyword filter, state-filtered
    if len(records) < 20:
        for state in ("Chhattisgarh", "Uttar Pradesh"):
            for pg in range(1, min(_MAX_PG, 10)):
                html = _fetch_page(sess, pg, state=state)
                if not html:
                    break
                batch = _parse_table(html, default_state=state)
                if not batch:
                    break
                for rec in batch:
                    if rec["source_id"] not in seen_ids:
                        seen_ids.add(rec["source_id"])
                        records.append(rec)
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
