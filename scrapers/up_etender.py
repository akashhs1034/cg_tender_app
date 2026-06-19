"""
scrapers/up_etender.py — Playwright scraper for etender.up.nic.in (NIC GePNIC portal).

Live-inspection findings
------------------------
• Portal is at /nicgep/app (Apache Tapestry framework).
• The "Active Tenders" / "Tenders by Closing Date" listing pages require CAPTCHA
  input to render results — not scriptable without an OCR/AI service.
• The homepage shows the ~10 latest tenders as anchor links with IDs starting
  "DirectLink" and session-specific sp= tokens in their hrefs.
• Each link leads to a full detail page with: Organisation Chain, Tender ID,
  Title, Tender Value in ₹, Location, Bid Submission End Date, Product Category.
• No CAPTCHA is required to view individual detail pages.

Navigation sequence
-------------------
  1. GET  https://etender.up.nic.in/nicgep/app  → wait networkidle
  2. Collect all a[id^="DirectLink"] hrefs (the 10 latest tender links)
  3. For each: GET detail page → page.evaluate(_DETAIL_JS)

Value parsing
-------------
• "Tender Value in ₹" uses Indian comma notation (e.g. "31,18,640").
• We strip commas to get the absolute INR amount, passed as value_text to
  core.tender_record() which calls parse_value_to_lakhs() internally.

Env vars (optional)
-------------------
  UP_ETENDER_HEADLESS – set to "0" to watch the browser (default headless)

Standalone:  python -m scrapers.up_etender
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import core  # noqa: E402

BASE_URL = "https://etender.up.nic.in"
HOME_URL = f"{BASE_URL}/nicgep/app"

_HEADLESS = os.getenv("UP_ETENDER_HEADLESS", "1") != "0"
_TIMEOUT = 45_000

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

_SECTOR_MAP = {
    "Civil Infrastructure": [
        "road", "bridge", "building", "construction", "pwd", "pavement",
        "drain", "culvert", "infrastructure", "bhavan", "nirmaan",
    ],
    "Electrical & Energy": [
        "electrical", "power", "solar", "energy", "substation",
        "transformer", "transmission", "distribution", "led", "light",
        "mast", "street light",
    ],
    "Water & Irrigation": [
        "water", "irrigation", "dam", "canal", "pipeline", "sewage",
        "borewell", "pump", "overhead tank", "sanitation",
    ],
    "Medical Procurement": [
        "medical", "medicine", "drug", "hospital", "health", "equipment",
        "ppe", "surgical", "ambulance",
    ],
    "Municipal Projects": [
        "municipal", "nagar", "nigam", "ward", "solid waste", "urban",
    ],
    "IT Services": [
        "software", "it ", "computer", "server", "network", "portal",
        "application", "e-governance",
    ],
    "Transport": ["transport", "vehicle", "fleet", "bus", "railway"],
}


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, keywords in _SECTOR_MAP.items():
        if any(k in t for k in keywords):
            return cat
    return "Civil Infrastructure"


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _UP_DISTRICTS:
        if re.search(r'\b' + re.escape(d) + r'\b', t):
            return d.title()
    return None


# Extracts key fields from a NIC GePNIC tender detail page.
# Scans all <td> elements for exact label matches and returns the next sibling's text.
# Works for both 2-cell and 4-cell rows (Critical Dates section uses 4-cell rows).
_DETAIL_JS = r"""
() => {
    const find = (label) => {
        for (const td of document.querySelectorAll('td')) {
            if (td.innerText.trim() === label) {
                const sib = td.nextElementSibling;
                return sib ? sib.innerText.trim() : '';
            }
        }
        return '';
    };
    return {
        tender_id:  find('Tender ID'),
        tender_ref: find('Tender Reference Number'),
        org_chain:  find('Organisation Chain'),
        title:      find('Title'),
        value_inr:  find('Tender Value in ₹'),
        location:   find('Location'),
        deadline:   find('Bid Submission End Date'),
        category:   find('Product Category'),
        url:        window.location.href
    };
}
"""


def scrape() -> list[dict]:
    """Return core.tender_record() dicts from etender.up.nic.in. Returns [] on failure."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("   up_etender: playwright not installed — run: pip install playwright && playwright install chromium")
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

            # Step 1 — load homepage (shows the latest ~10 tenders as DirectLinks)
            page.goto(HOME_URL, wait_until="networkidle", timeout=_TIMEOUT)

            # Step 2 — collect all DirectLink hrefs pointing to tender detail pages
            links: list[str] = page.evaluate(r"""
                () => [...document.querySelectorAll('a[id^="DirectLink"]')]
                       .map(a => a.getAttribute('href'))
                       .filter(h => h && h.includes('sp='))
            """)
            print(f"   up_etender: {len(links)} tender links on homepage")

            # Step 3 — visit each detail page and extract structured fields
            for href in links:
                try:
                    detail_url = BASE_URL + href if href.startswith("/") else href
                    page.goto(detail_url, wait_until="networkidle", timeout=_TIMEOUT)
                    d = page.evaluate(_DETAIL_JS)

                    title = d.get("title", "").strip()
                    if not title:
                        continue

                    # Take the last unit in the organisation chain (most specific)
                    org_chain = d.get("org_chain", "")
                    org = org_chain.split("||")[-1].strip() if org_chain else "Government of Uttar Pradesh"

                    # Indian comma notation → strip commas → absolute INR string
                    raw_value = d.get("value_inr", "").replace(",", "").strip()
                    value_text = raw_value if raw_value and raw_value not in ("NA", "-", "") else None

                    # "24-Jun-2026 02:00 PM" → pass just the date portion
                    raw_deadline = d.get("deadline", "").strip()
                    deadline = raw_deadline.split(" ")[0] if raw_deadline and raw_deadline != "NA" else None

                    category_raw = d.get("category", "").strip()
                    combined = f"{title} {d.get('location', '')} {org}"

                    records.append(core.tender_record(
                        title=title,
                        state="Uttar Pradesh",
                        organization=org,
                        category=category_raw if category_raw and category_raw != "NA" else _infer_category(combined),
                        district=_infer_district(combined),
                        value_text=value_text,
                        deadline=deadline,
                        document_url=d.get("url") or detail_url,
                        source_portal="etender.up.nic.in",
                    ))
                except Exception as e:
                    print(f"   up_etender: skipped detail page — {e}")

            browser.close()

    except Exception as exc:
        print(f"   up_etender: error — {exc}")

    print(f"   up_etender: {len(records)} core.tender_record() objects ready")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*72}")
    print(f"  {len(found)} total records extracted from etender.up.nic.in")
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
