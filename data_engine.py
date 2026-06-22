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


_CG_CITY_HINTS = ("raipur", "रायपुर", "bilaspur", "बिलासपुर", "durg", "दुर्ग",
                  "bhilai", "भिलाई", "korba", "कोरबा", "raigarh", "रायगढ़",
                  "rajnandgaon", "jagdalpur", "जगदलपुर", "ambikapur", "अंबिकापुर",
                  "bastar", "बस्तर", "dhamtari", "mahasamund", "kanker", "chhattisgarh",
                  "छत्तीसगढ़")
_UP_CITY_HINTS = ("lucknow", "लखनऊ", "kanpur", "कानपुर", "varanasi", "वाराणसी",
                  "prayagraj", "प्रयागराज", "allahabad", "agra", "आगरा",
                  "gorakhpur", "गोरखपुर", "noida", "नोएडा", "ghaziabad", "गाज़ियाबाद",
                  "meerut", "मेरठ", "bareilly", "aligarh", "jhansi", "झांसी",
                  "ayodhya", "अयोध्या", "uttar pradesh", "उत्तर प्रदेश")


def _guess_state(text: str) -> str | None:
    low = str(text or "").lower()
    if any(h in low or h in str(text or "") for h in _CG_CITY_HINTS):
        return "Chhattisgarh"
    if any(h in low or h in str(text or "") for h in _UP_CITY_HINTS):
        return "Uttar Pradesh"
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Part C — district-wise newspaper / e-paper directory (real, stable portals)
# ──────────────────────────────────────────────────────────────────────────────
# Only real, stable e-paper PORTAL landing pages. Each portal has its own
# district/edition picker — we link the portal and tell the user which edition
# to open, rather than fabricating 100+ fragile per-district deep links.
NEWSPAPER_DIRECTORY: dict[str, list[dict]] = {
    "Chhattisgarh": [
        {"name": "Dainik Bhaskar", "url": "https://epaper.bhaskar.com",
         "note": "Largest CG circulation — daily निविदा/NIT display ads across all districts."},
        {"name": "Patrika (Rajasthan Patrika)", "url": "https://epaper.patrika.com",
         "note": "Strong Raipur, Bilaspur, Durg, Bastar editions; many municipal & PWD NITs."},
        {"name": "Nava Bharat", "url": "https://www.enavabharat.com/epaper/",
         "note": "Established CG Hindi daily; collector-office & gram-panchayat tenders."},
        {"name": "Deshbandhu", "url": "https://www.deshbandhu.co.in",
         "note": "Raipur-rooted CG daily; state govt & local body tender notices."},
        {"name": "Haribhoomi", "url": "https://epaper.haribhoomi.com",
         "note": "Wide CG coverage; PWD, irrigation & nagar nigam advertisements."},
        {"name": "Nai Dunia", "url": "https://epaper.naidunia.com",
         "note": "CG/MP Hindi daily; district administration tender ads."},
        {"name": "Dainik Jagran", "url": "https://epaper.jagran.com",
         "note": "National Hindi daily with CG editions; government NITs."},
    ],
    "Uttar Pradesh": [
        {"name": "Dainik Jagran", "url": "https://epaper.jagran.com",
         "note": "Largest UP circulation — NIT/निविदा ads in every district edition."},
        {"name": "Amar Ujala", "url": "https://epaper.amarujala.com",
         "note": "Very strong UP coverage; PWD, Jal Nigam, Nagar Nigam & Vikas Pradhikaran tenders."},
        {"name": "Hindustan (Hindi)", "url": "https://epaper.livehindustan.com",
         "note": "Deep UP district editions; collector-office & local-body NITs."},
        {"name": "Dainik Bhaskar", "url": "https://epaper.bhaskar.com",
         "note": "Growing UP editions; government & municipal tender ads."},
        {"name": "Rajasthan Patrika", "url": "https://epaper.patrika.com",
         "note": "Select UP editions; PWD and urban-body tender notices."},
    ],
}


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
# Part D — Gemini-Vision e-paper extractor (page image / PDF -> offline tenders)
# ──────────────────────────────────────────────────────────────────────────────
_VISION_MODEL = "gemini-flash-latest"

_EPAPER_VISION_PROMPT = """You are reading a scanned PAGE of an Indian newspaper / e-paper from the state of Chhattisgarh or Uttar Pradesh. The text may be in Hindi (Devanagari) or English, printed in dense columns.

Find EVERY GOVERNMENT TENDER NOTICE printed on this page. These are advertisements headed with words like "निविदा सूचना", "ई-निविदा", "Tender Notice", "Notice Inviting Tender", "NIT", "Invitation for Bids", "कोटेशन", "Quotation" — usually issued by a government office such as PWD / लोक निर्माण विभाग, Collector / कलेक्टर कार्यालय, Nagar Nigam / Nagar Palika / नगर निगम, Jal Sansadhan / जल संसाधन / PHED, Gram Panchayat, Janpad, Executive Engineer / कार्यपालन अभियंता, RES, CGMSC, etc.

Ignore commercial ads, matrimonials, news articles and editorials — ONLY government tender / quotation notices.

For EACH tender notice found, extract (translate Hindi VALUES to clean English where natural, but keep proper nouns/numbers as printed):
- work: short description of the work / supply / service
- office: full issuing office / department
- district: the CG/UP district it pertains to, if printed
- nit_no: NIT / tender / निविदा number / reference
- value: estimated cost exactly as printed (e.g. "Rs 45.50 Lakh")
- emd: earnest money deposit if printed
- published_date / closing_date / opening_date: in YYYY-MM-DD if clearly derivable, else as printed
- portal: any e-procurement website URL printed in the notice

Return ONLY a JSON array, no markdown fences. Each element exactly:
{"work":"", "office":"", "district":"", "nit_no":"", "value":"", "emd":"", "published_date":"", "closing_date":"", "opening_date":"", "portal":""}
Use null for any field not printed. If there are NO government tender notices on this page, return [].
Do NOT invent or guess tenders — extract only what is actually printed on the page."""


def _gemini_vision_json(file_bytes: bytes, mime_type: str, prompt: str | None = None):
    """POST a page image / PDF to Gemini and return parsed JSON (list/dict).

    Returns (data, status). Mirrors bid_engine's REST call: direct endpoint +
    X-goog-api-key header (the SDK mishandles the 'AQ.' key format), thinking
    disabled for speed/quota. Records errors into core's AI-error channel so the
    UI can surface quota/key problems honestly.
    """
    import os
    import base64
    import json

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        core.record_ai_error("no api key configured")
        return None, "no_key"

    actual = (mime_type or "image/jpeg").lower()
    if "pdf" not in actual and "image" not in actual:
        actual = "image/jpeg"

    try:
        import requests
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{_VISION_MODEL}:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": key},
            json={"contents": [{"parts": [
                {"inline_data": {"mime_type": actual,
                                 "data": base64.b64encode(file_bytes).decode()}},
                {"text": prompt or _EPAPER_VISION_PROMPT},
            ]}], "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}}},
            timeout=180,
        )
        resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        core.clear_ai_error()
        return data, "ok"
    except Exception as exc:
        core.record_ai_error(exc)
        return None, f"error:{type(exc).__name__}"


def offline_tender_record(*, title, organization=None, district=None, state=None,
                          nit_no=None, value_text=None, emd=None,
                          published_date=None, closing_date=None, opening_date=None,
                          newspaper=None, document_url=None, description=None,
                          added_by=None) -> dict:
    """Shape one extracted notice into an `offline_tenders`-table record."""
    def _s(x):
        x = str(x).strip() if x is not None else ""
        return x or None
    def _iso(x):
        d = core.parse_date(x)
        return d.isoformat() if d else None

    title = (_s(title) or "Tender Notice (newspaper)")[:300]
    org   = _s(organization)
    nit   = _s(nit_no)
    pub   = published_date
    return {
        "source_id":      core.make_source_id(title, org or _s(newspaper) or "",
                                              nit or pub or ""),
        "title":          title,
        "state":          _s(state),
        "district":       _s(district),
        "organization":   org,
        "nit_no":         nit,
        "category":       "Offline / Newspaper Tender",
        "value_text":     _s(value_text),
        "value_lakhs":    core.parse_value_to_lakhs(value_text) if value_text else None,
        "emd":            _s(emd),
        "published_date": _iso(published_date),
        "deadline":       _iso(closing_date),
        "opening_date":   _iso(opening_date),
        "newspaper":      _s(newspaper),
        "document_url":   _s(document_url),
        "description":    (_s(description)[:500] if _s(description) else None),
        "source_portal":  "offline:newspaper",
        "added_by":       (_s(added_by).lower() if _s(added_by) else None),
        "scraped_at":     core._now_iso(),
    }


def extract_tenders_from_epaper(file_bytes: bytes, mime_type: str = "image/jpeg", *,
                                district_hint: str | None = None,
                                state_hint: str | None = None,
                                newspaper_hint: str | None = None,
                                added_by: str | None = None) -> tuple[list[dict], str]:
    """Read ONE e-paper page (image or PDF) -> structured offline-tender records.

    Returns (records, status). Never raises. Honest: returns [] when the page
    has no tender notices (or when AI is unavailable), and only shapes notices
    Gemini actually read off the page.
    """
    try:
        data, status = _gemini_vision_json(file_bytes, mime_type)
        # Gemini usually returns a JSON array; tolerate a {"tenders":[...]} wrap.
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), None)
        if not isinstance(data, list):
            return [], status

        out: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            work = item.get("work") or item.get("title")
            if not work or not str(work).strip():
                continue
            dist = item.get("district") or district_hint
            st_  = state_hint or _guess_state(f"{item.get('district') or ''} "
                                              f"{item.get('office') or ''} {work}")
            out.append(offline_tender_record(
                title=work,
                organization=item.get("office"),
                district=dist,
                state=st_,
                nit_no=item.get("nit_no"),
                value_text=item.get("value"),
                emd=item.get("emd"),
                published_date=item.get("published_date"),
                closing_date=item.get("closing_date"),
                opening_date=item.get("opening_date"),
                newspaper=newspaper_hint,
                document_url=item.get("portal"),
                description=work,
                added_by=added_by,
            ))
        return out, status
    except Exception as exc:
        return [], f"error:{type(exc).__name__}"


# ──────────────────────────────────────────────────────────────────────────────
# Part E — vault document expiry / validity reader (Opporta Intelligence)
# ──────────────────────────────────────────────────────────────────────────────
_DOC_EXPIRY_PROMPT = """You are reading ONE business / compliance document that a contractor uploaded
to a tender platform (e.g. contractor license / registration, GST certificate, ISO certificate,
bank solvency certificate, Class-3 Digital Signature Certificate, insurance, EMD/bank guarantee,
CA net-worth certificate, experience/completion certificate, PAN card).

Find the date until which this document is VALID. Look for: "Valid up to", "Valid till",
"Valid until", "Expiry date", "Date of Expiry", "Valid from <date> to <date>", "Renewal date",
"Date of validity", or a printed certificate validity period. If the document clearly has NO
expiry (e.g. a PAN card or an experience/completion certificate), set has_expiry to false.

Return ONLY this JSON (no markdown fences):
{"expiry_date": "YYYY-MM-DD or null", "doc_type": "short label e.g. GST Certificate / Contractor License / ISO 9001 / DSC / Solvency Certificate", "has_expiry": true or false}
If two validity dates appear, use the LATER 'valid to' date. Never invent a date that is not printed."""


def extract_document_expiry(file_bytes: bytes, mime_type: str = "application/pdf") -> dict:
    """Read a vault document with Gemini Vision and return its validity info.

    Returns: {expiry_date: 'YYYY-MM-DD'|None, doc_type: str|None,
              has_expiry: bool, status: 'ok'|'no_key'|'error:*'}. Never raises.
    """
    try:
        data, status = _gemini_vision_json(file_bytes, mime_type, prompt=_DOC_EXPIRY_PROMPT)
        if not isinstance(data, dict):
            return {"expiry_date": None, "doc_type": None,
                    "has_expiry": False, "status": status}
        raw = data.get("expiry_date")
        iso = None
        if raw and str(raw).strip().lower() not in ("null", "none", ""):
            d = core.parse_date(raw)
            iso = d.isoformat() if d else None
        return {"expiry_date": iso,
                "doc_type": (str(data.get("doc_type")).strip() if data.get("doc_type") else None),
                "has_expiry": bool(data.get("has_expiry")),
                "status": "ok"}
    except Exception as exc:
        return {"expiry_date": None, "doc_type": None,
                "has_expiry": False, "status": f"error:{type(exc).__name__}"}


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
