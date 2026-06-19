"""cg_vyapam.py — CG Vyapam recruitment scraper.

Source : vyapamcg.cgstate.gov.in (Chhattisgarh Professional Examination Board)
Note   : Old domain vyapam.cgstate.gov.in is dead; portal moved to vyapamcg.
Apply  : All Vyapam exams share a single application portal —
         vyapamprofile.cgstate.gov.in/online/
"""
from __future__ import annotations

import logging
import os

from playwright.sync_api import sync_playwright

import core

logger = logging.getLogger(__name__)

_LISTING_URL  = "https://vyapamcg.cgstate.gov.in/Posts?tag=ONLINE%20APPLICATION"
_APPLY_PORTAL = "https://vyapamprofile.cgstate.gov.in/online/"
_HEADLESS     = os.getenv("CG_VYAPAM_HEADLESS", "1") != "0"

# Walk up from each <a PostID=*ONLINE> to find the parent that also contains
# a DD/MM/YYYY date — that gives us (title, date, detailUrl) in one pass.
_EXTRACT_JS = r"""() => {
    const re = /PostID=([A-Z0-9]+ONLINE)/i;
    const seen = new Set();
    const items = [];
    document.querySelectorAll('a[href]').forEach(a => {
        const m = a.href.match(re);
        if (!m) return;
        const code = m[1].toUpperCase();
        if (seen.has(code)) return;
        seen.add(code);
        let el = a.parentElement;
        for (let i = 0; i < 6; i++) {
            if (!el) break;
            const txt = el.innerText.trim();
            const dm = txt.match(/(\d{2}\/\d{2}\/\d{4})/);
            if (dm) {
                items.push({
                    examCode : code.replace('ONLINE', ''),
                    title    : a.innerText.trim(),
                    date     : dm[1],
                    detailUrl: a.href
                });
                break;
            }
            el = el.parentElement;
        }
    });
    return items;
}"""


def scrape() -> list[dict]:
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=_HEADLESS)
            page = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120"
                ),
                ignore_https_errors=True,
            ).new_page()
            page.goto(_LISTING_URL, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(4000)
            items = page.evaluate(_EXTRACT_JS)
            browser.close()
    except Exception as exc:
        logger.warning("cg_vyapam: scrape failed — %s", exc)
        return []

    out: list[dict] = []
    for it in items:
        title = it["title"][:295].strip() or f"CG Vyapam {it['examCode']} Recruitment"
        rec = core.job_record(
            title=title,
            department="CG Vyapam",
            state="Chhattisgarh",
            deadline=it["date"],
            description=f"Exam Code: {it['examCode']}",
            document_url=it["detailUrl"],
            apply_link=_APPLY_PORTAL,
            source_portal="https://vyapamcg.cgstate.gov.in",
        )
        out.append(rec)

    logger.info("cg_vyapam: %d recruitment exams found", len(out))
    if not out:
        logger.warning("cg_vyapam: 0 records returned — portal may be down or restructured")
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = scrape()
    total = len(records)
    print(f"\n{'-' * 68}")
    print(f"  {total} total records — CG Vyapam")
    print(f"{'-' * 68}")
    for r in records[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
