"""
scrapers/dprcg.py — Chhattisgarh DPR / Jansampark / Samvad tender scraper.

Source: https://dprcg.gov.in/all-tender-list  (Directorate of Public Relations,
a.k.a. Jansampark / Chhattisgarh Samvad — the body that places government
advertisements and runs PR/printing/empanelment procurement).

The listing is a simple HTML list: each entry is a Hindi title + a PDF link under
/public/uploads/tenders/<unix-ts>_<hash>.pdf, where <unix-ts> is the upload time.

IMPORTANT — recency filter: this listing is an ARCHIVE going back to 2022, so we
keep ONLY tenders uploaded within DPRCG_MAX_AGE_DAYS (default 120) to avoid
flooding the app with long-closed notices. When DPR posts a fresh tender it is
captured automatically on the next ingest; until then this honestly returns few
or zero records rather than stale data.

Standalone:  python -m scrapers.dprcg
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_LIST = "https://dprcg.gov.in/all-tender-list"
_BASE = "https://dprcg.gov.in"
_MAX_AGE_DAYS = int(os.getenv("DPRCG_MAX_AGE_DAYS", "120"))

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
}

_SIZE_RE = re.compile(r"\[\s*[\d.]+\s*[KMG]B\s*\]", re.I)
_TS_RE   = re.compile(r"/(\d{10})_")


def _clean_title(text: str) -> str:
    return _SIZE_RE.sub("", str(text or "")).strip(" –-·|").strip()


def scrape() -> list[dict]:
    """Return recent DPR/Samvad tender records (within the recency window)."""
    try:
        r = requests.get(_LIST, headers=_HEADERS, timeout=30, verify=False)
        r.raise_for_status()
    except Exception as e:
        print(f"   dprcg: fetch failed — {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    records: list[dict] = []
    seen: set[str] = set()
    today = date.today()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/uploads/tenders/" not in href:
            continue
        m = _TS_RE.search(href)
        pub = None
        if m:
            try:
                pub = datetime.fromtimestamp(int(m.group(1))).date()
            except (ValueError, OSError):
                pub = None
        # Recency gate — skip archived/long-closed tenders.
        if pub and (today - pub).days > _MAX_AGE_DAYS:
            continue

        parent = a.find_parent(["li", "div", "tr", "td"])
        title = _clean_title(a.get_text(" ", strip=True)) or \
                _clean_title(parent.get_text(" ", strip=True) if parent else "")
        if not title or len(title) < 6:
            continue

        rec = core.tender_record(
            title=title,
            state="Chhattisgarh",
            organization="Directorate of Public Relations (Jansampark) / CG Samvad",
            category="Printing & Advertising",
            deadline=None,
            document_url=urljoin(_BASE, href),
            description=(f"Published {pub.isoformat()}" if pub else None),
            source_portal="dprcg.gov.in",
        )
        if rec["source_id"] not in seen:
            seen.add(rec["source_id"])
            records.append(rec)

    print(f"   dprcg: {len(records)} recent DPR/Samvad tenders "
          f"(within {_MAX_AGE_DAYS} days)")
    if not records:
        print("   dprcg: 0 recent — DPR's published list has nothing within the "
              "window right now (newest postings are older); will catch new ones.")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    found = scrape()
    print(f"\n{'-'*70}\n  {len(found)} DPR/Samvad tenders\n{'-'*70}")
    for rec in found[:8]:
        print(f"  • {rec['title'][:70]}  | {rec.get('document_url','')[:55]}")