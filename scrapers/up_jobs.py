"""up_jobs.py — UP government job advertisements.

Sources:
  - uppsc.up.nic.in  (Uttar Pradesh PSC — homepage What's New notices)
  - upsssc.gov.in    (UPSSSC — delegated to scrapers/up_upsssc.py)
"""
from __future__ import annotations

import re
import logging
import os

from playwright.sync_api import sync_playwright

import core

logger = logging.getLogger(__name__)

_UPPSC_URL = "https://uppsc.up.nic.in/"
_HEADLESS = os.getenv("UP_JOBS_HEADLESS", "1") != "0"

_SKIP = re.compile(
    r"(list of selected|result(?:s)?\b|corrigendum|interview schedule|admit card)",
    re.I,
)


def _parse_notices(items: list[dict]) -> list[dict]:
    seen_advt: dict[str, dict] = {}
    for it in items:
        full = it.get("full", "")
        if _SKIP.search(full):
            continue

        m_advt = re.search(r"ADVT[\s.]*NO[\s.:]*([A-Z0-9/\-]+)", full, re.I)
        if not m_advt:
            continue
        advt_no = m_advt.group(1).strip()

        m_title = re.search(
            r"ADVT[\s.]*NO[\s.:]*[A-Z0-9/\-]+[,\s]+(.+?)(?:\.\.|\s*Visible)",
            full, re.I,
        )
        exam_name = (
            m_title.group(1).strip().rstrip("-.").strip().title()
            if m_title
            else advt_no
        )

        m_date = re.search(r"Visible upto\s*:\s*(\d{2}/\d{2}/\d{4})", full, re.I)
        deadline_raw = m_date.group(1) if m_date else None

        if advt_no not in seen_advt:
            href = it["links"][0]["h"] if it.get("links") else None
            seen_advt[advt_no] = core.job_record(
                title=f"{exam_name} [{advt_no}]",
                department="Uttar Pradesh Public Service Commission",
                state="Uttar Pradesh",
                deadline=deadline_raw,
                document_url=href,
                apply_link=href,
                description=f"Advertisement No. {advt_no}",
                source_portal="https://uppsc.up.nic.in",
            )

    return list(seen_advt.values())


def _scrape_uppsc() -> list[dict]:
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=_HEADLESS)
            page = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            ).new_page()
            page.goto(_UPPSC_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            items = page.evaluate(r"""() => {
                const out = [];
                document.querySelectorAll('li').forEach(li => {
                    const full = li.textContent.trim();
                    if (!full.includes('ADVT') && !full.includes('Advt')) return;
                    const links = [...li.querySelectorAll('a[href]')].map(a => ({
                        t: a.textContent.trim(),
                        h: a.href
                    }));
                    out.push({full, links});
                });
                return out;
            }""")
            browser.close()

        records = _parse_notices(items)
        logger.info("uppsc: %d unique advertisements found", len(records))
        return records
    except Exception as exc:
        logger.warning("uppsc: scrape failed — %s", exc)
        return []


def _scrape_upsssc() -> list[dict]:
    from scrapers.up_upsssc import scrape as upsssc_scrape
    return upsssc_scrape()


def scrape() -> list[dict]:
    jobs: list[dict] = []
    jobs += _scrape_uppsc()
    jobs += _scrape_upsssc()
    if not jobs:
        logger.warning("up_jobs: 0 records returned — both UPPSC and UPSSSC scrapers failed")
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = scrape()
    total = len(records)
    print(f"\n{'-' * 68}")
    print(f"  {total} total records — UP Jobs")
    print(f"{'-' * 68}")
    for r in records[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
