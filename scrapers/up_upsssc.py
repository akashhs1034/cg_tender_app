"""up_upsssc.py — UPSSSC recruitment scraper.

Source : http://45.118.50.83/AllNotifications.aspx
         (Uttar Pradesh Subordinate Services Selection Commission)
Note   : upsssc.gov.in is a thin redirect shell; the real portal is
         on the raw IP 45.118.50.83 — accessed over plain HTTP.
Apply  : http://45.118.50.83/ (UPSSSC application portal)
"""
from __future__ import annotations

import logging
import os
import re

from playwright.sync_api import sync_playwright

import core

logger = logging.getLogger(__name__)

# Primary: raw IP (the real app server). Fallback: official domain in case the
# IP changes and the hostname starts routing correctly in future.
_LISTING_URLS = [
    "http://45.118.50.83/AllNotifications.aspx",
    "https://upsssc.gov.in/AllNotifications.aspx",
]
_APPLY_PORTAL = "http://45.118.50.83/"
_HEADLESS     = os.getenv("UP_UPSSSC_HEADLESS", "1") != "0"

# Skip non-recruitment notices: calendars, form templates, syllabus
_SKIP = re.compile(r"(कैलेण्डर|अधियाचन का प्रारूप|syllabus|answer\s*key)", re.I)

# Extract advt number from Hindi notice text.
# Handles: "संख्या-07-परीक्षा/2026", "संख्या-18(5)/2016", "संख्या-18 (5)/2016"
# (?:[-/]\S+)? is optional and backtracks so the mandatory /YYYY still matches.
_RE_ADVT = re.compile(
    r"संख्या[-\s]*([0-9]+\s*(?:\([0-9]+\))?(?:[-/]\S+)?/[0-9]{4})",
    re.U,
)

# Single JS pass: collect all ViewPdf notice links with their nearby Visible-upto dates
_EXTRACT_JS = r"""() => {
    const rDate = /Visible\s+upto\s*:\s*(\d{2}\/\d{2}\/\d{4})/i;
    const seen  = new Set();
    const items = [];

    document.querySelectorAll('a[href*="ViewPdf.aspx"]').forEach(a => {
        const href = a.href;
        const text = a.innerText.replace(/\s+/g, ' ').trim();
        if (!text.includes('संख्या')) return;  // "संख्या"
        if (seen.has(href)) return;
        seen.add(href);

        // Walk up DOM (max 5 levels, stop if container > 350 chars to stay item-local)
        let dateStr = null;
        let el = a.parentElement;
        for (let i = 0; i < 5; i++) {
            if (!el) break;
            const t = el.innerText || '';
            if (t.length < 350) {
                const m = rDate.exec(t);
                if (m) { dateStr = m[1]; break; }
            }
            el = el.parentElement;
        }
        items.push({ t: text, h: href, d: dateStr });
    });
    return items;
}"""


def _parse_advt_no(text: str) -> str | None:
    m = _RE_ADVT.search(text)
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(1))


def _parse_notices(raw: list[dict]) -> list[dict]:
    seen_advt: dict[str, dict] = {}
    for it in raw:
        text  = it["t"]
        href  = it["h"]
        date  = it["d"]

        if _SKIP.search(text):
            continue

        advt_no = _parse_advt_no(text)
        if not advt_no:
            continue

        if advt_no in seen_advt:
            continue

        title = text[:295].rstrip(".")
        seen_advt[advt_no] = core.job_record(
            title=title,
            department="Uttar Pradesh Subordinate Services Selection Commission",
            state="Uttar Pradesh",
            deadline=date,
            document_url=href,
            apply_link=_APPLY_PORTAL,
            description=f"Advertisement No. {advt_no}",
            source_portal="https://upsssc.gov.in",
        )

    return list(seen_advt.values())


def scrape() -> list[dict]:
    raw: list[dict] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=_HEADLESS)
            page = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124"
                ),
                ignore_https_errors=True,
            ).new_page()

            for url in _LISTING_URLS:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(4000)
                    raw = page.evaluate(_EXTRACT_JS)
                    if raw:
                        logger.info("upsssc: fetched from %s (%d raw links)", url, len(raw))
                        break
                    logger.warning("upsssc: %s loaded but returned 0 links — trying next", url)
                except Exception as exc:
                    logger.warning("upsssc: %s failed — %s — trying next", url, exc)

            browser.close()
    except Exception as exc:
        logger.warning("upsssc: browser launch failed — %s", exc)
        return []

    records = _parse_notices(raw)
    logger.info("upsssc: %d unique advertisements found (from %d raw links)", len(records), len(raw))
    if not records:
        logger.warning("upsssc: 0 records returned — portal may be down or restructured")
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = scrape()
    total = len(records)
    print(f"\n{'-' * 68}")
    print(f"  {total} total records — UPSSSC")
    print(f"{'-' * 68}")
    for r in records[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
