"""cg_jobs.py — CG government job advertisements.

Sources:
  - psc.cg.gov.in/Advertisement.php  (Chhattisgarh PSC)
  - vyapam.cgstate.gov.in             (currently unreachable — returns [])
"""
from __future__ import annotations

import re
import logging

import requests
from bs4 import BeautifulSoup

import core

logger = logging.getLogger(__name__)

_CGPSC_URL = "https://psc.cg.gov.in/Advertisement.php"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _parse_title(link_text: str) -> str:
    m = re.search(r"_ADVERTISEMENT", link_text, re.I)
    raw = link_text[: m.start()] if m else link_text
    title = raw.replace("_", " ").strip()
    title = re.sub(r"[-\s]+\d{4}$", "", title).strip()
    return title.title()


def _scrape_cgpsc() -> list[dict]:
    try:
        resp = requests.get(_CGPSC_URL, timeout=20, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("cgpsc: failed to fetch page — %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
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

        dm = re.search(r"\((\d{2}-\d{2}-\d{4})\)\s*$", text.strip())
        deadline_raw = dm.group(1) if dm else None

        pdf_url = href if href.startswith("http") else "https://psc.cg.gov.in/" + href.lstrip("/")

        rec = core.job_record(
            title=title,
            department="Chhattisgarh Public Service Commission",
            state="Chhattisgarh",
            deadline=deadline_raw,
            document_url=pdf_url,
            apply_link=pdf_url,
            source_portal="https://psc.cg.gov.in/Advertisement.php",
        )
        if rec["source_id"] not in seen:
            seen.add(rec["source_id"])
            out.append(rec)

    logger.info("cgpsc: %d advertisements found", len(out))
    return out


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
