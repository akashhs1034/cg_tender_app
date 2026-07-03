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
# searching state + district names, which match buyer/location text). To
# approximate the full CG/UP firehose we sweep the state names plus EVERY
# district (defined above), so bids tagged only to a district are still caught.
_SEARCH_TERMS = (
    [("Chhattisgarh", "Chhattisgarh"), ("Chattisgarh", "Chhattisgarh")]
    + [(d.title(), "Chhattisgarh") for d in _DISTRICT_CG]
    + [("Uttar Pradesh", "Uttar Pradesh")]
    + [(d.title(), "Uttar Pradesh") for d in _DISTRICT_UP]
)


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


def _token_from_html(html: str) -> str | None:
    for pat in (r'name="csrf-token"\s+content="([^"]+)"',
                r'csrf_bd_gem_nk["\']?\s*[:=]\s*["\']([^"\']+)',
                r'"csrf_token"\s*:\s*"([^"]+)"'):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


def _csrf_token(sess: requests.Session) -> str | None:
    """Load /all-bids to obtain the CSRF token + session cookies (plain HTTP)."""
    try:
        r = sess.get(f"{_BASE}/all-bids", timeout=30)
    except Exception as e:
        print(f"   gem: could not load all-bids — {e}")
        return None
    return _token_from_html(r.text)


def _browser_bootstrap(sess: requests.Session) -> str | None:
    """Open /all-bids in a real Chromium (Playwright) to clear anti-bot, then
    copy its cookies into the requests session and return the CSRF token.

    GeM increasingly serves a JS/anti-bot challenge to plain HTTP clients; a
    real browser from an Indian residential IP passes it. Set GEM_USE_BROWSER=0
    to disable. Silently returns None if Playwright isn't available."""
    if os.getenv("GEM_USE_BROWSER", "1") in ("0", "false", "False"):
        return None
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=_HEADERS["User-Agent"],
                                      locale="en-IN")
            page = ctx.new_page()
            page.goto(f"{_BASE}/all-bids", timeout=60000,
                      wait_until="domcontentloaded")
            page.wait_for_timeout(3500)   # let any JS challenge settle
            html = page.content()
            token = _token_from_html(html)
            # carry the browser's cleared cookies into the requests session
            for c in ctx.cookies():
                try:
                    sess.cookies.set(c["name"], c["value"],
                                     domain=c.get("domain"), path=c.get("path", "/"))
                except Exception:
                    pass
            browser.close()
            if token:
                print("   gem: browser bootstrap OK (anti-bot cleared)")
            return token
    except Exception as e:
        print(f"   gem: browser bootstrap failed — {e}")
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
    # The all-bids-data endpoint intermittently 404/timeouts on some requests
    # even when the term is valid; a short retry recovers those.
    last_exc = None
    for attempt in range(3):
        try:
            r = sess.post(_DATA_EP, data=payload, timeout=30,
                          headers={"X-Requested-With": "XMLHttpRequest",
                                   "Referer": f"{_BASE}/all-bids"})
            r.raise_for_status()
            return r.json().get("response", {}).get("response", {}).get("docs", []) or []
        except Exception as e:
            last_exc = e
            if attempt < 2:
                time.sleep(1.2 * (attempt + 1))
    e = last_exc
    if True:
        print(f"   gem: search {term!r} p{page} failed — {e}")
        return []


def scrape() -> list[dict]:
    """Fetch ongoing GeM bids relevant to CG/UP via the JSON bid API."""
    sess = _make_session()
    records: list[dict] = []
    seen: set[str] = set()

    # Prefer a real browser session (clears anti-bot on residential IPs); fall
    # back to plain HTTP token fetch.
    token = _browser_bootstrap(sess)
    if not token:
        for _ in range(3):
            token = _csrf_token(sess)
            if token:
                break
            time.sleep(1)
    if not token:
        print("   gem: WARNING — could not obtain CSRF token; GeM unavailable "
              "(blocked IP or anti-bot — run from an Indian residential IP)")
        return []

    # Per-term page depth. GEM_MAX_PAGES caps total effort; with the full
    # district sweep, default to a few pages each.
    max_pages = max(1, min(_MAX_PG, int(os.getenv("GEM_PAGES_PER_TERM", "3"))))
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
