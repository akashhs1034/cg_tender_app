"""cg_jobs.py — CG government job advertisements.

Sources:
  - psc.cg.gov.in/Advertisement.php  (Chhattisgarh PSC)
  - vyapam.cgstate.gov.in             (currently unreachable — returns [])
"""
from __future__ import annotations

import os
import re
import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

import core

logger = logging.getLogger(__name__)

_CGPSC_URL = "https://psc.cg.gov.in/Advertisement.php"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_MAX_AGE_DAYS = int(os.getenv("CGPSC_MAX_AGE_DAYS", "180"))


def _parse_title(link_text: str) -> str:
    m = re.search(r"_ADVERTISEMENT", link_text, re.I)
    raw = link_text[: m.start()] if m else link_text
    title = raw.replace("_", " ").strip()
    title = re.sub(r"[-\s]+\d{4}$", "", title).strip()
    return title.title()


def _parse_advertisements(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        if "ADVERTISEMENT" not in text.upper():
            continue
        if "CORRIGENDUM" in text.upper():
            continue
        if ".pdf" not in href.lower():
            continue

        title = _parse_title(text)

        # The date in the advertisement link is the PUBLICATION date, not the
        # application last-date. Storing it as `deadline` made the pipeline's
        # expired-row cleanup delete valid notices the day after they appeared.
        # Keep it as published_date; leave deadline unknown so nothing is
        # dropped on a misread date.
        dm = re.search(r"\((\d{2}-\d{2}-\d{4})\)\s*$", text.strip())
        published_raw = dm.group(1) if dm else None
        published = core.parse_date(published_raw)
        if published and (date.today() - published).days > _MAX_AGE_DAYS:
            continue

        pdf_url = href if href.startswith("http") else "https://psc.cg.gov.in/" + href.lstrip("/")

        rec = core.job_record(
            title=title,
            department="Chhattisgarh Public Service Commission",
            state="Chhattisgarh",
            published_date=published_raw,
            deadline=None,
            document_url=pdf_url,
            apply_link=pdf_url,
            source_portal="https://psc.cg.gov.in/Advertisement.php",
        )
        if rec["source_id"] not in seen:
            seen.add(rec["source_id"])
            out.append(rec)

    logger.info("cgpsc: %d advertisements found", len(out))
    return out


def _scrape_cgpsc() -> list[dict]:
    try:
        resp = requests.get(_CGPSC_URL, timeout=20, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("cgpsc: failed to fetch page — %s", exc)
        return []
    return _parse_advertisements(resp.text)


def scrape() -> list[dict]:
    records = _scrape_cgpsc()
    if not records:
        logger.warning("cg_jobs: 0 records returned — portal may be down or restructured")
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = scrape()
    total = len(records)
    print(f"\n{'-' * 68}")
    print(f"  {total} total records — CG Jobs")
    print(f"{'-' * 68}")
    for r in records[:3]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
