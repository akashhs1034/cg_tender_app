"""
data_engine.py — unified, fault-isolated ingestion facade.

One resilient entry point in front of every portal scraper, so a caller (the
ingest cron, an ad-hoc refresh, a test) gets combined results with **per-source
isolation**: if GeM times out or a portal changes its HTML, that source returns
0 and is reported — it never aborts the whole run.

Sources wrapped:
  * State e-Procurement — CG e-Proc, UP e-Tender, CPPP (CG + UP), PWD-CG
  * Utilities / PSUs    — CSPDCL, UPPCL, SECL
  * National GeM        — gem.gov.in custom bids
  * Jobs                — CG PSC/Vyapam, UP PSC/UPSSSC
  * OFFLINE e-papers    — keyword-matrix scaffold (see below)

────────────────────────────────────────────────────────────────────────────
HONESTY NOTE about the offline e-paper scanner
────────────────────────────────────────────────────────────────────────────
`scan_epapers()` is a **scaffold**, not a magic data source. It contains the
real, working part — a Hindi+English keyword matrix and a defensive record
shaper (`extract_epaper_tenders`) that turns a block of e-paper *text* into
canonical tender records. What it deliberately does NOT do is invent data:
`iter_epaper_pages()` yields nothing until you wire in a genuine text source
(an OCR pipeline over e-paper page images, or a licensed publisher feed).

So out of the box `scan_epapers()` returns `[]` and says so. That is correct
behaviour — better an honest zero than fabricated tenders a contractor might
bid real money against.
"""

from __future__ import annotations

import datetime as _dt
import re as _re
from typing import Callable, Iterable

import core


# ──────────────────────────────────────────────────────────────────────────────
# Part A — fault-isolated facade over the live scrapers
# ──────────────────────────────────────────────────────────────────────────────
def _safe_run(fn: Callable[[], list]) -> tuple[list, str]:
    """Run a scraper; never raise. Returns (records, status_message)."""
    try:
        out = fn() or []
        if not isinstance(out, list):
            return [], f"unexpected return type {type(out).__name__}"
        return out, "ok"
    except Exception as exc:
        return [], f"FAILED — {type(exc).__name__}: {exc}"


def _tender_scrapers() -> list[tuple[str, Callable[[], list]]]:
    from scrapers import (cg_eproc, up_etender, cppp_state, cspdcl,
                          secl, pwd_cg, uppcl, gem)

    import os as _os

    def _cppp_cg():
        prev = _os.environ.get("CPPP_STATE")
        _os.environ["CPPP_STATE"] = "Chhattisgarh"
        try:
            import importlib
            import scrapers.cppp_state as _c
            importlib.reload(_c)
            return _c.scrape()
        finally:
            if prev is None:
                _os.environ.pop("CPPP_STATE", None)
            else:
                _os.environ["CPPP_STATE"] = prev

    return [
        ("cg_eproc",   cg_eproc.scrape),
        ("up_etender", up_etender.scrape),
        ("cppp_up",    cppp_state.scrape),
        ("cppp_cg",    _cppp_cg),
        ("cspdcl",     cspdcl.scrape),
        ("secl",       secl.scrape),
        ("pwd_cg",     pwd_cg.scrape),
        ("uppcl",      uppcl.scrape),
        ("gem",        gem.scrape),
    ]


def _job_scrapers() -> list[tuple[str, Callable[[], list]]]:
    from scrapers import cg_jobs, cg_vyapam, up_jobs, up_upsssc
    return [
        ("cg_jobs",   cg_jobs.scrape),
        ("cg_vyapam", cg_vyapam.scrape),
        ("up_jobs",   up_jobs.scrape),
        ("up_upsssc", up_upsssc.scrape),
    ]


def collect_all(include_epapers: bool = True) -> dict:
    """Run every source with isolation. Returns combined results + a report.

    {
      "tenders": [...], "jobs": [...],
      "report": {source_name: {"count": int, "status": str}, ...},
    }
    """
    tenders: list[dict] = []
    jobs: list[dict] = []
    report: dict[str, dict] = {}

    for name, fn in _tender_scrapers():
        recs, status = _safe_run(fn)
        tenders += recs
        report[name] = {"count": len(recs), "status": status}

    for name, fn in _job_scrapers():
        recs, status = _safe_run(fn)
        jobs += recs
        report[name] = {"count": len(recs), "status": status}

    if include_epapers:
        recs, status = _safe_run(scan_epapers)
        tenders += recs
        report["epaper_offline"] = {"count": len(recs), "status": status}

    return {"tenders": tenders, "jobs": jobs, "report": report}


# ──────────────────────────────────────────────────────────────────────────────
# Part B — offline e-paper keyword-matrix scanner (scaffold)
# ──────────────────────────────────────────────────────────────────────────────
# A hit on ANY of these in a text block flags it as a probable tender notice.
# Mixed Hindi + English because regional e-papers print both.
EPAPER_KEYWORDS = [
    # Hindi
    "निविदा", "ई-निविदा", "निविदा सूचना", "टेंडर", "निविदा आमंत्रण",
    "कलेक्टर कार्यालय", "नगर निगम", "नगर पालिका", "लोक निर्माण विभाग",
    "जल संसाधन", "ग्राम पंचायत", "कार्यपालन अभियंता",
    # English
    "tender notice", "notice inviting tender", "nit no", "e-tender",
    "e-procurement", "pwd", "public works", "executive engineer",
    "collector office", "municipal corporation", "gram panchayat",
    "invitation for bid", "quotation",
]

# Authority hints used to attribute an organization to a flagged block.
_AUTHORITY_HINTS = [
    ("लोक निर्माण विभाग", "Public Works Department (PWD)"),
    ("public works", "Public Works Department (PWD)"),
    ("pwd", "Public Works Department (PWD)"),
    ("नगर निगम", "Municipal Corporation"),
    ("municipal", "Municipal Corporation"),
    ("कलेक्टर", "Collector Office"),
    ("collector", "Collector Office"),
    ("जल संसाधन", "Water Resources Department"),
    ("ग्राम पंचायत", "Gram Panchayat"),
    ("gram panchayat", "Gram Panchayat"),
    ("कार्यपालन अभियंता", "Office of the Executive Engineer"),
    ("executive engineer", "Office of the Executive Engineer"),
]

_NIT_RE = _re.compile(r"(?:NIT|Tender|निविदा)\s*(?:No\.?|क्र\.?|संख्या)?\s*[:\-]?\s*"
                      r"([A-Za-z0-9/\-]{3,40})", _re.IGNORECASE)


def _guess_state(text: str) -> str | None:
    low = text.lower()
    if "chhattisgarh" in low or "छत्तीसगढ़" in text or "raipur" in low or "रायपुर" in text:
        return "Chhattisgarh"
    if "uttar pradesh" in low or "उत्तर प्रदेश" in text or "lucknow" in low or "लखनऊ" in text:
        return "Uttar Pradesh"
    return None


def _guess_org(text: str) -> str | None:
    low = text.lower()
    for hint, org in _AUTHORITY_HINTS:
        if hint in low or hint in text:
            return org
    return None


def extract_epaper_tenders(text: str, source: str = "e-paper",
                           published_date=None) -> list[dict]:
    """Scan a block of e-paper TEXT for tender notices -> canonical records.

    Splits on blank lines / clear separators, flags any block containing a
    keyword-matrix hit, and shapes it via core.tender_record(). Purely textual
    and fully defensive — bad input yields []. It will only ever return records
    for text that genuinely contains tender keywords (no fabrication).
    """
    out: list[dict] = []
    try:
        text = str(text or "")
        if not text.strip():
            return out
        pub = None
        if published_date:
            d = core.parse_date(published_date)
            pub = d.isoformat() if d else None

        # Break the page into candidate notice blocks.
        blocks = _re.split(r"\n\s*\n|(?:_{4,})|(?:={4,})|(?:\*{4,})", text)
        for block in blocks:
            b = block.strip()
            if len(b) < 25:
                continue
            low = b.lower()
            if not any(kw in b or kw in low for kw in EPAPER_KEYWORDS):
                continue

            # Title = first substantive line of the flagged block.
            first_line = next((ln.strip() for ln in b.splitlines() if ln.strip()), "")
            title = (first_line or "Tender Notice (e-paper)")[:300]

            nit_m = _NIT_RE.search(b)
            nit = nit_m.group(1) if nit_m else None

            rec = core.tender_record(
                title=title,
                state=_guess_state(b),
                organization=_guess_org(b),
                category=None,
                description=b[:500],
                requirements=(f"NIT/Ref: {nit}" if nit else None),
                deadline=None,
                source_portal=f"offline:{source}",
            )
            if pub:
                rec["scraped_at"] = pub
            out.append(rec)
    except Exception:
        # Defensive: malformed input must never crash the ingest run.
        return out
    return out


def iter_epaper_pages() -> Iterable[tuple[str, str, object]]:
    """Yield (text, source_name, published_date) for each e-paper page.

    *** This is the integration seam. ***  Out of the box it yields NOTHING,
    because there is no licensed e-paper text feed wired in yet. To activate
    offline ingestion, plug a real source in here, e.g.:

        for page in my_ocr_pipeline(today_epaper_pdf):
            yield page.text, page.publication, page.date

    Until then `scan_epapers()` honestly returns [] rather than inventing data.
    """
    return iter(())


def scan_epapers() -> list[dict]:
    """Run the e-paper scanner over whatever `iter_epaper_pages` provides."""
    records: list[dict] = []
    pages = 0
    for text, source, pub in iter_epaper_pages():
        pages += 1
        records += extract_epaper_tenders(text, source, pub)
    if pages == 0:
        print("   data_engine.scan_epapers: no e-paper source wired "
              "(iter_epaper_pages yielded 0 pages) — returning 0 records honestly.")
    else:
        print(f"   data_engine.scan_epapers: {pages} page(s) scanned, "
              f"{len(records)} candidate tender(s).")
    return records


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import io as _io
    import sys as _sys
    _sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding="utf-8", errors="replace")

    # Demo the e-paper extractor on a tiny synthetic sample (proves the matrix
    # works without pretending it is live data).
    sample = """
    नगर निगम रायपुर
    निविदा सूचना क्रमांक: NIT/2026/114
    सड़क निर्माण कार्य हेतु ई-निविदा आमंत्रित की जाती है।

    ____________________

    Office of the Executive Engineer, PWD Lucknow
    Tender Notice No: 22/2026-27
    Construction of community building. e-Procurement applies.
    """
    demo = extract_epaper_tenders(sample, source="demo-epaper", published_date="2026-06-22")
    print(f"e-paper extractor demo -> {len(demo)} record(s):")
    for r in demo:
        print(f"  • [{r.get('state')}] {r.get('title')}  ({r.get('organization')})")

    print("\nLive scan (no source wired):")
    print(f"  scan_epapers() -> {len(scan_epapers())} records")
