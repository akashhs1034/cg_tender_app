"""
scrapers/cg_eproc.py  —  Playwright scraper for eproc.cgstate.gov.in (CHiPS/CHEPS portal).

Live-inspection findings
------------------------
• Root URL redirects to /CHEPS/security/getSignInAction.do (login page).
• The "Open Tender" table on that page is EMPTY on first load; the
  "LOAD LIVE DATA" button submits a hidden form (POST loadAlldata=Y) that
  causes the server to render ~460 live tender rows inside <marquee id="marqu">.
• Tender rows alternate with 1-cell organisation-header rows.
• The description column is truncated in the visible text but the FULL title
  lives in <span class="tooltiptext"> which is CSS-hidden, so `innerText`
  returns "". We use `textContent` instead.
• PAC (Probable Amount of Contract) is in absolute rupees; core's
  parse_value_to_lakhs() converts it when the value is >= 100 000.
• No direct GET URL exists for individual tenders (portal is POST/session
  based), so document_url is a best-effort parameterised link.

Navigation sequence
-------------------
  1. GET  https://eproc.cgstate.gov.in/  → wait networkidle
  2. CLICK input[value="LOAD LIVE DATA"] → wait networkidle
  3. page.evaluate() extracts all rows in one JS round-trip

Env vars (optional)
-------------------
  CG_EPROC_MAX_ROWS  – cap on rows harvested (default 500, 0 = no limit)
  CG_EPROC_HEADLESS  – set to "0" to watch the browser (default headless)

Standalone:  python -m scrapers.cg_eproc
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import core  # noqa: E402

PORTAL_URL = "https://eproc.cgstate.gov.in/"
BASE_URL = "https://eproc.cgstate.gov.in"

_MAX_ROWS = int(os.getenv("CG_EPROC_MAX_ROWS", "500"))
_HEADLESS = os.getenv("CG_EPROC_HEADLESS", "1") != "0"
_TIMEOUT = 60_000   # ms

# JS that extracts every tender row in a single round-trip.
# Uses textContent (not innerText) on the tooltip span because the span is
# CSS-hidden and innerText returns "" for hidden elements.
_EXTRACT_JS = r"""
() => {
    const out = [];
    let org = '';
    for (const row of document.querySelectorAll('#marqu table tr')) {
        const cells = row.querySelectorAll('td');
        if (cells.length === 1) {
            org = cells[0].innerText.trim();
        } else if (cells.length === 7) {
            const tooltip = cells[4].querySelector('span.tooltiptext');
            const title = tooltip
                ? tooltip.textContent.trim()
                : cells[4].innerText.trim();
            const dh = row.getAttribute('data-href') || '';
            const m  = dh.match(/viewRfq\((\d+),(\d+)\)/);
            out.push({
                org:        org,
                tender_no:  cells[1].innerText.trim(),
                deadline:   cells[3].innerText.trim(),
                pac:        cells[5].innerText.trim(),
                title:      title,
                rfq_id:     m ? m[1] : '',
                rfq_part:   m ? m[2] : '1'
            });
        }
    }
    return out;
}
"""

# ---------------------------------------------------------------------------
# District / sector inference
# ---------------------------------------------------------------------------
_CG_DISTRICTS = [
    "raipur", "bilaspur", "durg", "bhilai", "korba", "bastar", "raigarh",
    "rajnandgaon", "jagdalpur", "ambikapur", "janjgir", "champa", "dhamtari",
    "mahasamund", "kanker", "kondagaon", "narayanpur", "bijapur", "sukma",
    "dantewada", "bemetara", "balod", "gariaband", "balodabazar", "mungeli",
    "surguja", "balrampur", "surajpur", "jashpur", "korea", "sakti",
    "sarangarh", "manendragarh", "kabirdham", "kawardha",
]

_SECTOR_MAP = {
    "Civil Infrastructure": [
        "road", "bridge", "building", "construction", "pwd", "pavement",
        "drain", "culvert", "compound wall", "retaining", "infrastructure",
        "hostel", "ashram", "bhavan", "nirmaan",
    ],
    "Electrical & Energy": [
        "electrical", "power", "solar", "energy", "substation",
        "transformer", "transmission", "distribution", "cspdcl", "creda",
    ],
    "Water & Irrigation": [
        "water", "irrigation", "dam", "canal", "pipeline", "nala",
        "borewell", "pump", "sewage", "overhead tank",
    ],
    "Medical Procurement": [
        "medical", "medicine", "drug", "hospital", "health", "cgmsc",
        "equipment", "ppe", "surgical", "ambulance",
    ],
    "Coal & Mining": [
        "coal", "mining", "secl", "cil", "nmdc", "quarry", "mineral",
        "re-engineering",
    ],
    "Municipal Projects": [
        "municipal", "nagar", "nigam", "ward", "solid waste", "urban",
        "street light",
    ],
    "Transport": ["transport", "vehicle", "fleet", "bus", "railway"],
    "IT Services": [
        "software", "it ", "computer", "server", "network", "portal",
        "application", "e-governance",
    ],
}


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, keywords in _SECTOR_MAP.items():
        if any(k in t for k in keywords):
            return cat
    return "Civil Infrastructure"


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _CG_DISTRICTS:
        if re.search(r'\b' + re.escape(d) + r'\b', t):
            return d.title()
    return None


def _rfq_url(rfq_id: str, rfq_part: str = "1") -> str:
    return (
        f"{BASE_URL}/CHEPS/business/rfq.action"
        f"?rfqId={rfq_id}&rfqPartNumber={rfq_part}"
        f"&methodName=viewRfq&documentStatus=AAS&openRfqFlag=Y"
    )


# ---------------------------------------------------------------------------
# Public sync entry point
# ---------------------------------------------------------------------------
def scrape() -> list[dict]:
    """Return a list of core.tender_record() dicts.  Returns [] on any failure."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("   cg_eproc: playwright not installed — run: pip install playwright && playwright install chromium")
        return []

    records: list[dict] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=_HEADLESS)
            page = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-IN",
            ).new_page()

            # Step 1 – load portal (redirects to CHEPS login/home page)
            page.goto(PORTAL_URL, wait_until="networkidle", timeout=_TIMEOUT)

            # Step 2 – click "LOAD LIVE DATA" to trigger the form POST that
            #           populates the marquee tender table
            page.locator('input[value="LOAD LIVE DATA"]').first.click()
            page.wait_for_load_state("networkidle", timeout=_TIMEOUT)

            # Step 3 – extract all rows in one JavaScript round-trip
            raw_rows: list[dict] = page.evaluate(_EXTRACT_JS)
            print(f"   cg_eproc: {len(raw_rows)} raw tender rows from portal")

            browser.close()

        # Step 4 – convert to core.tender_record() objects
        limit = _MAX_ROWS if _MAX_ROWS else len(raw_rows)
        for row in raw_rows[:limit]:
            title = row.get("title", "").strip()
            if not title or title == "-":
                continue

            pac = row.get("pac", "")
            value_text = None if pac in ("NA", "N/A", "-", "") else pac
            combined = f"{title} {row.get('org', '')}"

            records.append(core.tender_record(
                title=title,
                state="Chhattisgarh",
                organization=row.get("org") or "Government of Chhattisgarh",
                category=_infer_category(combined),
                district=_infer_district(combined),
                value_text=value_text,
                deadline=row.get("deadline"),
                document_url=_rfq_url(row.get("rfq_id", ""), row.get("rfq_part", "1")),
                source_portal="eproc.cgstate.gov.in",
            ))

    except Exception as exc:
        print(f"   cg_eproc: error — {exc}")

    print(f"   cg_eproc: {len(records)} core.tender_record() objects ready")
    if not records:
        print("   cg_eproc: WARNING — 0 records returned, portal may be down or restructured")
    return records


# ---------------------------------------------------------------------------
# Standalone smoke-test:  python -m scrapers.cg_eproc
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*72}")
    print(f"  {len(found)} total records extracted from eproc.cgstate.gov.in")
    print(f"{'-'*72}")
    for r in found[:3]:
        print(
            f"\n  source_id   : {r.get('source_id', '')}"
            f"\n  title       : {r.get('title', '')}"
            f"\n  organization: {r.get('organization', '')}"
            f"\n  deadline    : {r.get('deadline', '')}"
            f"\n  value_lakhs : {r.get('value_lakhs', '')}"
            f"\n  category    : {r.get('category', '')}"
            f"\n  district    : {r.get('district', '')}"
            f"\n  document_url: {r.get('document_url', '')}"
        )
