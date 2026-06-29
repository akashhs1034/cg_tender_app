"""
scrapers/newspapers.py — regional-newspaper government-notice collector.

Collects OFFLINE government **tenders** (NIT / EOI / RFP / auction / corrigendum)
and government **recruitment** notices printed as display advertisements in
regional Chhattisgarh / Uttar Pradesh newspapers, and in government e-papers /
notice PDFs.

How it works (and what it honestly does NOT do)
───────────────────────────────────────────────
Newspaper tenders are printed as image advertisements inside the e-paper edition,
not as scrapable HTML articles. So the real extractor is Gemini Vision: we
DOWNLOAD a reachable asset (a notice PDF, or an e-paper page image) and hand its
bytes to data_engine's vision extractor, which returns structured records. This
module's job is the *acquisition + orchestration* layer around that:

  • a registry of the target papers with their reachability,
  • best-effort discovery of directly-fetchable assets (PDFs / page images),
  • download with automatic retry + per-asset fault isolation,
  • Gemini-Vision extraction of BOTH tenders and recruitment notices,
  • cross-newspaper de-duplication into one master record that lists every
    newspaper source it appeared in,
  • a structured failure log, and structured JSON output.

Accuracy > Completeness > Speed. We NEVER fabricate: a field that is not printed
comes back null, an unreachable source returns [] and is logged, and a JS-gated
e-paper viewer whose page-image URLs are not configured yields [] honestly rather
than inventing data.

Run standalone:   python -m scrapers.newspapers            (live, needs GEMINI_API_KEY)
                  python -m scrapers.newspapers --dump out.json
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core            # noqa: E402
import data_engine     # noqa: E402

_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")}

# ──────────────────────────────────────────────────────────────────────────────
# Target-newspaper registry. `reachable` reflects a live connectivity probe; the
# scrape never assumes — it re-checks each run and logs anything that fails.
#   kind = "pdf_index"      → page links to government-notice PDFs we can fetch
#          "html_notices"   → news site with a tenders/recruitment/notice section
#          "epaper_portal"  → JS e-paper viewer; page-image URLs must be supplied
#                             via `page_images` (none wired = honest 0, logged)
# ──────────────────────────────────────────────────────────────────────────────
NEWSPAPERS: list[dict] = [
    {"name": "Rihand Times",    "state": "Uttar Pradesh",
     "urls": ["https://rihandtimes.com", "https://www.rihandtimes.com"],
     "kind": "html_notices"},
    {"name": "Navbharat Times", "state": None,
     "urls": ["https://navbharattimes.indiatimes.com"],
     "kind": "epaper_portal"},
    {"name": "Ghatti Ghatna",   "state": "Chhattisgarh",
     "urls": ["https://ghattighatna.com", "https://www.ghattighatna.com"],
     "kind": "html_notices"},
    {"name": "CG Frontline",    "state": "Chhattisgarh",
     "urls": ["https://cgfrontline.com", "https://www.cgfrontline.com"],
     "kind": "html_notices"},
    {"name": "Haribhoomi",      "state": "Chhattisgarh",
     "urls": ["https://www.haribhoomi.com"],
     "kind": "html_notices"},
    {"name": "Haribhoomi e-paper", "state": "Chhattisgarh",
     "urls": ["https://epaper.haribhoomi.com"],
     "kind": "epaper_portal", "epaper_fn": "haribhoomi", "max_assets": 28},
    {"name": "Akashvani",       "state": None,
     "urls": ["https://akashvani.gov.in", "https://www.akashvani.gov.in"],
     "kind": "pdf_index"},
]


def _load_newspaper_sources() -> list[dict]:
    """Load the versioned acquisition registry, retaining a safe fallback."""
    path = Path(__file__).parent.parent / "newspaper_sources.json"
    try:
        configured = json.loads(path.read_text(encoding="utf-8"))
        valid = [
            item for item in configured
            if isinstance(item, dict) and item.get("active", True)
            and item.get("name") and item.get("urls")
        ]
        return valid or NEWSPAPERS
    except (OSError, ValueError, TypeError):
        return NEWSPAPERS


NEWSPAPERS = _load_newspaper_sources()

# A link / anchor is treated as a probable government-notice asset only if its URL
# or visible text hits one of these (Hindi + English). Keeps us off news/sport ads.
_GOV_HINTS = [
    "tender", "tender notice", "निविदा", "टेंडर", "ई-निविदा",
    "e-tender", "nit", "eoi", "rfp", "quotation", "कोटेशन",
    "auction", "नीलाम", "corrigendum", "शुद्धिपत्र", "recruitment", "भर्ती",
    "vacancy", "रिक्ति", "bharti", "notice", "सूचना", "vigyapan", "विज्ञापन",
    "advertisement", "वैकेंसी", "appointment", "नियुक्ति", "career", "job",
]

# ──────────────────────────────────────────────────────────────────────────────
# Structured failure log (Requirement: log extraction failures).
# ──────────────────────────────────────────────────────────────────────────────
_FAILURES: list[dict] = []
_MANUAL_REVIEW: list[dict] = []


def _log_fail(source: str, url: str, stage: str, err: str) -> None:
    _FAILURES.append({"source": source, "url": url, "stage": stage,
                      "error": str(err)[:200], "at": core._now_iso()})


# ──────────────────────────────────────────────────────────────────────────────
# Networking — fetch with automatic retry + exponential backoff (Requirement:
# retry failed pages automatically). Never raises.
# ──────────────────────────────────────────────────────────────────────────────
def _fetch(url: str, source: str = "", want: str = "text",
           tries: int = 3) -> tuple[object, str, str]:
    """Return (payload, content_type, status). payload is str (want='text') or
    bytes (want='bytes'); None on failure. Retries transient errors."""
    last = "unknown"
    for attempt in range(tries):
        try:
            r = requests.get(url, headers=_UA, timeout=25, allow_redirects=True)
            if r.status_code == 200:
                ctype = r.headers.get("content-type", "").lower()
                return ((r.text if want == "text" else r.content), ctype, "ok")
            last = f"HTTP {r.status_code}"
            if r.status_code in (404, 401, 403):
                break                       # not transient — don't waste retries
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(1.0 * (attempt + 1))     # backoff before the next try
    _log_fail(source, url, "fetch", last)
    return None, "", last


# ──────────────────────────────────────────────────────────────────────────────
# Discovery — find directly-fetchable government-notice assets on a reachable page
# ──────────────────────────────────────────────────────────────────────────────
def _looks_governmental(text: str, href: str) -> bool:
    blob = f"{text or ''} {href or ''}".lower()
    return any(h in blob for h in _GOV_HINTS)


def _discover_assets(homepage_html: str, base_url: str,
                     grab_all_pdfs: bool = False) -> dict:
    """From a page's HTML, collect candidate asset URLs.

    Returns {"pdfs": [...], "images": [...], "notice_pages": [...]}.
    PDFs that look governmental are always kept; when `grab_all_pdfs` is true
    (e.g. on a .gov.in site or a page we reached via a 'tenders' link) ALL PDFs
    are kept and Vision decides relevance. Images need a gov / e-paper signal.
    """
    pdfs, images, pages = [], [], []
    try:
        soup = BeautifulSoup(homepage_html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"].strip())
            txt = a.get_text(" ", strip=True)
            low = href.lower()
            if low.split("?")[0].endswith(".pdf"):
                if grab_all_pdfs or _looks_governmental(txt, href):
                    pdfs.append(href)
            elif low.split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
                if _looks_governmental(txt, href) or "epaper" in low or "edition" in low:
                    images.append(href)
            elif _looks_governmental(txt, href):
                pages.append(href)
        pdfs   = list(dict.fromkeys(pdfs))[:40]
        images = list(dict.fromkeys(images))[:60]
        pages  = list(dict.fromkeys(pages))[:25]
    except Exception as exc:
        _log_fail("discover", base_url, "parse", exc)
    return {"pdfs": pdfs, "images": images, "notice_pages": pages}


# ──────────────────────────────────────────────────────────────────────────────
# Gemini-Vision extraction of BOTH tenders AND recruitment from one asset.
# ──────────────────────────────────────────────────────────────────────────────
_COMBINED_PROMPT = """You are reading a scanned PAGE / advertisement / notice PDF from an Indian (Chhattisgarh or Uttar Pradesh) regional newspaper or a government website. Text may be Hindi (Devanagari) or English.

Extract TWO things printed on this page:

1) Government TENDER notices — headed by words like "निविदा सूचना", "ई-निविदा", "Tender Notice", "NIT", "Notice Inviting Tender", "EOI", "RFP", "Auction / नीलामी", "Corrigendum / शुद्धिपत्र", "Quotation / कोटेशन" — issued by a government office (PWD / लोक निर्माण विभाग, Collector / कलेक्टर, Nagar Nigam / Nagar Palika, Jal Sansadhan / PHED, Gram Panchayat, Janpad, Zila Panchayat, Police, Health, Education, Forest, Irrigation, Electricity, Mining, Railway, Smart City, University, PSU, Executive Engineer, etc.).

2) Government RECRUITMENT / JOB notices — headed by words like "भर्ती", "Recruitment", "Vacancy", "रिक्ति", "Appointment", "Walk-in", "आवेदन आमंत्रित" — issued by a government department / PSU / university / municipal / collector / district panchayat / police / health / education body.

IGNORE political news, sports, entertainment, editorials, matrimonials and commercial (non-government) advertisements.

Translate Hindi VALUES to clean English where natural, but keep proper nouns / numbers / NIT references as printed.

Return ONLY this JSON (no markdown fences):
{
 "tenders":[{"work":"","office":"","district":"","state":"","nit_no":"","category":"","value":"","emd":"","published_date":"","closing_date":"","opening_date":"","eligibility":"","contact":"","portal":"","language":"","confidence_score":0}],
 "jobs":[{"title":"","department":"","district":"","state":"","advertisement_no":"","vacancies":"","qualification":"","age_limit":"","salary":"","last_date":"","apply_link":"","contact":"","language":"","confidence_score":0}]
}
Set confidence_score from 0 to 100 based only on page legibility and certainty of
the extracted fields. Do not return full page or article text.
Use null for any field not printed. Empty arrays if none. NEVER invent or guess — extract only what is actually printed."""


def _extraction_confidence(item: dict, kind: str) -> int:
    raw = core.parse_int(item.get("confidence_score"))
    if raw is not None:
        return max(0, min(100, raw))
    # Deterministic extraction-quality score when a model omits confidence.
    score = 35
    score += 20 if item.get("work") or item.get("title") else 0
    score += 15 if item.get("office") or item.get("department") else 0
    score += 10 if item.get("district") or item.get("state") else 0
    score += 10 if item.get("closing_date") or item.get("last_date") else 0
    score += 10 if (item.get("nit_no") if kind == "tender"
                    else item.get("advertisement_no")) else 0
    return min(100, score)


def _queue_if_uncertain(record: dict, record_type: str, source_url: str) -> None:
    confidence = int(record.get("confidence_score") or 0)
    if confidence >= 60 and not record.get("requires_manual_review"):
        return
    _MANUAL_REVIEW.append({
        "queue_id": core.make_source_id(record_type, record.get("source_id"), source_url),
        "record_type": record_type,
        "reason": "Low OCR confidence or incomplete scanned notice",
        "confidence_score": confidence,
        "source_url": source_url,
        "record": record,
        "queued_at": core._now_iso(),
    })


def _vision_extract(file_bytes: bytes, mime_type: str, *, newspaper: str,
                    state_hint: str | None, source_url: str,
                    district_hint: str | None = None,
                    published_hint: str | None = None,
                    source_type: str = "newspaper") -> tuple[list[dict], list[dict], str]:
    """Run Vision on one asset → (tender_records, job_records, status). Never raises."""
    if not (os.getenv("GEMINI_API_KEY")):
        return [], [], "no_key"
    try:
        data, status = data_engine._gemini_vision_json(file_bytes, mime_type, prompt=_COMBINED_PROMPT)
        if not isinstance(data, dict):
            return [], [], status
        tenders, jobs = [], []
        for item in (data.get("tenders") or []):
            if not isinstance(item, dict):
                continue
            work = item.get("work") or item.get("title")
            if not work or not str(work).strip():
                continue
            st_ = item.get("state") or state_hint or data_engine._guess_state(
                f"{item.get('district') or ''} {item.get('office') or ''} {work}")
            confidence = _extraction_confidence(item, "tender")
            uncertain = (
                confidence < 60 or not item.get("office")
                or (not item.get("nit_no") and not item.get("closing_date"))
            )
            rec = core.tender_record(
                title=work, organization=item.get("office"), state=st_,
                district=item.get("district") or district_hint,
                tender_no=item.get("nit_no"), category=item.get("category"),
                value_text=item.get("value"), emd=item.get("emd"),
                published_date=item.get("published_date") or published_hint,
                deadline=item.get("closing_date"),
                opening_date=item.get("opening_date"),
                eligibility=item.get("eligibility"), description=work,
                newspaper_name=newspaper,
                document_url=item.get("portal") or source_url,
                source_url=source_url, source_name=newspaper,
                source_portal=f"newspaper:{newspaper}",
                source_type=("epaper" if "epaper" in source_type else "newspaper"),
                online_or_offline="offline",
                confidence_score=confidence, language=item.get("language"),
                is_corrigendum=("corrigendum" in str(work).lower()
                                or "शुद्धिपत्र" in str(work)),
                requires_manual_review=uncertain,
            )
            if item.get("contact"):
                rec["requirements"] = f"Contact: {item['contact']}"[:500]
            tenders.append(rec)
            _queue_if_uncertain(rec, "tender", source_url)
        for item in (data.get("jobs") or []):
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            if not title or not str(title).strip():
                continue
            st_ = item.get("state") or state_hint or data_engine._guess_state(
                f"{item.get('district') or ''} {item.get('department') or ''} {title}")
            confidence = _extraction_confidence(item, "job")
            uncertain = (
                confidence < 60 or not item.get("department")
                or (not item.get("last_date") and not item.get("apply_link"))
            )
            jrec = core.job_record(
                title=title, state=st_, department=item.get("department"),
                district=item.get("district") or district_hint, vacancies=item.get("vacancies"),
                qualification=item.get("qualification"), salary=item.get("salary"),
                deadline=item.get("last_date"), apply_link=item.get("apply_link"),
                document_url=source_url, advertisement_no=item.get("advertisement_no"),
                age_limit=item.get("age_limit"), language=item.get("language"),
                source_url=source_url, source_name=newspaper,
                source_type=("epaper" if "epaper" in source_type else "newspaper"),
                source_portal=f"newspaper:{newspaper}",
                online_or_offline="offline", confidence_score=confidence,
                requires_manual_review=uncertain)
            jobs.append(jrec)
            _queue_if_uncertain(jrec, "job", source_url)
        return tenders, jobs, status
    except Exception as exc:
        _log_fail(newspaper, source_url, "vision", exc)
        return [], [], f"error:{type(exc).__name__}"


# ──────────────────────────────────────────────────────────────────────────────
# Haribhoomi e-paper — reverse-engineered full-resolution page reader.
# Editions are /category/<id>/<city>-main-edition; opening /epaper/default/open?id=<id>
# embeds every page as {"f_folder":"YYYY-MM","f_filename":"page-NN-<id>.jpg"}, and
# the full-res scan is /media/<folder>/<filename> (~600 KB JPEG, Vision-readable).
# ──────────────────────────────────────────────────────────────────────────────
_HB_EPAPER = "https://epaper.haribhoomi.com"
_HB_CG_KEYS = ("raipur", "bilaspur", "durg", "korba", "raigarh", "rajnandgaon",
               "bhilai", "jagdalpur", "ambikapur", "bastar", "dhamtari",
               "mahasamund", "kanker", "chhattisgarh")


def _haribhoomi_epaper_pages(max_editions: int = 4,
                             max_pages: int = 14) -> list[tuple[str, str]]:
    """Return [(full_res_image_url, city_district)] for Haribhoomi CG editions."""
    out: list[tuple[str, str]] = []
    body, _ct, _s = _fetch(_HB_EPAPER, source="Haribhoomi e-paper", want="text")
    if not body:
        return out
    editions = {m.group(1): m.group(2)
                for m in re.finditer(r"/category/(\d+)/([a-z0-9-]+)-main-edition", body)}
    cg = [(i, c.split("-")[0]) for i, c in editions.items()
          if any(k in c for k in _HB_CG_KEYS)]
    for edid, city in cg[:max_editions]:
        h, _c2, _s2 = _fetch(f"{_HB_EPAPER}/epaper/default/open?id={edid}",
                             source="Haribhoomi e-paper", want="text")
        if not h:
            continue
        pairs = re.findall(r'"f_folder":"(\d{4}-\d{2})","f_filename":"(page-\d+-\d+\.jpg)"', h)
        for folder, fn in list(dict.fromkeys(pairs))[:max_pages]:
            out.append((f"{_HB_EPAPER}/media/{folder}/{fn}", city.title()))
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Per-newspaper acquisition → extraction
# ──────────────────────────────────────────────────────────────────────────────
_MAX_ASSETS_PER_PAPER = 12       # accuracy/cost guard: cap Vision calls per paper

_EPAPER_FNS = {"haribhoomi": _haribhoomi_epaper_pages}


def _process_newspaper(paper: dict) -> tuple[list[dict], list[dict], str]:
    name, kind = paper["name"], paper["kind"]
    state_hint = paper.get("state")
    cap = paper.get("max_assets", _MAX_ASSETS_PER_PAPER)
    tenders: list[dict] = []
    jobs: list[dict] = []
    vision_statuses: list[str] = []

    if not os.getenv("GEMINI_API_KEY"):
        _log_fail(
            name, paper["urls"][0], "ocr",
            "OCR skipped because GEMINI_API_KEY is not configured",
        )
        return [], [], "skipped_no_ocr_key"

    # (url, kind, district_hint)
    asset_urls: list[tuple[str, str, str | None]] = []

    # ── A) portals with a reverse-engineered full-res page reader (live e-paper)
    epaper_fn = _EPAPER_FNS.get(paper.get("epaper_fn", ""))
    if epaper_fn:
        try:
            for img_url, district in epaper_fn():
                asset_urls.append((img_url, "image", district))
        except Exception as exc:
            _log_fail(name, _HB_EPAPER, "epaper_discover", exc)
    else:
        # ── B) generic: reach homepage, discover directly-fetchable assets ──
        html, base = None, None
        for u in paper["urls"]:
            body, ctype, status = _fetch(u, source=name, want="text")
            if body:
                html, base = body, u
                break
        if html is None:
            return [], [], "unreachable"

        _is_gov = ".gov.in" in (urlparse(base).netloc or "")
        assets = _discover_assets(html, base, grab_all_pdfs=_is_gov)
        # one-level crawl into 'tender / recruitment / notice' sections
        for pg in assets["notice_pages"][:5]:
            if pg.rstrip("/") == base.rstrip("/"):
                continue
            sub, _c, _s = _fetch(pg, source=name, want="text")
            if sub:
                sa = _discover_assets(sub, pg, grab_all_pdfs=True)
                assets["pdfs"] += sa["pdfs"]
                assets["images"] += sa["images"]
        for p in dict.fromkeys(assets["pdfs"]):
            asset_urls.append((p, "pdf", None))
        for img in dict.fromkeys(assets["images"]):
            asset_urls.append((img, "image", None))
        for pg in paper.get("page_images", []):
            asset_urls.append((pg, "image", None))

    if not asset_urls:
        _log_fail(name, paper["urls"][0], "discover",
                  f"no directly-fetchable government assets ({kind})")
        return [], [], "no_assets"

    # ── download + Vision each asset (capped), per-asset isolation ──
    for url, akind, district in asset_urls[:cap]:
        payload, ctype, status = _fetch(url, source=name, want="bytes")
        if not payload:
            continue
        mime = ("application/pdf" if (akind == "pdf" or "pdf" in ctype)
                else ("image/png" if url.lower().endswith(".png") else "image/jpeg"))
        t, j, vstatus = _vision_extract(payload, mime, newspaper=name,
                                        state_hint=state_hint, source_url=url,
                                        district_hint=district,
                                        source_type=kind)
        vision_statuses.append(vstatus)
        if str(vstatus).startswith("error"):
            _log_fail(name, url, "ocr", vstatus)
        tenders += t
        jobs += j

    if vision_statuses and all(str(status).startswith("error")
                               for status in vision_statuses):
        return tenders, jobs, "failed"
    if any(str(status).startswith("error") for status in vision_statuses):
        return tenders, jobs, "warning"
    return tenders, jobs, "ok"


# ──────────────────────────────────────────────────────────────────────────────
# Cross-newspaper de-duplication: one master record, every source listed.
# ──────────────────────────────────────────────────────────────────────────────
def _dedup_key(rec: dict) -> str:
    """Content identity independent of which newspaper printed it."""
    nit = (rec.get("nit_no") or "").strip().lower()
    if nit:
        return f"nit::{nit}"
    title = re.sub(r"\W+", " ", (rec.get("title") or "").lower()).strip()
    dist  = (rec.get("district") or "").strip().lower()
    return f"t::{title[:80]}::{dist}"


def _merge_sources(records: list[dict]) -> list[dict]:
    """Collapse the same notice seen in multiple papers into one master that
    carries a `sources` list of every newspaper it appeared in."""
    masters: dict[str, dict] = {}
    for rec in records:
        k = _dedup_key(rec)
        src = {"newspaper": rec.get("newspaper"),
               "published_date": rec.get("published_date"),
               "source_url": rec.get("source_url") or rec.get("document_url")}
        if k not in masters:
            rec["sources"] = [src]
            masters[k] = rec
        else:
            m = masters[k]
            if src["newspaper"] and src["newspaper"] not in {
                    s.get("newspaper") for s in m["sources"]}:
                m["sources"].append(src)
            # keep the most complete master (prefer one with an NIT / value)
            if not m.get("nit_no") and rec.get("nit_no"):
                m["nit_no"] = rec["nit_no"]
            if not m.get("value_text") and rec.get("value_text"):
                m["value_text"] = rec["value_text"]
    return list(masters.values())


# ──────────────────────────────────────────────────────────────────────────────
# Public entry points
# ──────────────────────────────────────────────────────────────────────────────
def collect() -> dict:
    """Run every newspaper source. Returns a structured, JSON-serializable dict:

      {"tenders":[...master records...], "jobs":[...],
       "report": {newspaper: {"tenders":n,"jobs":n,"status":s}},
       "failures":[...], "generated_at": iso}
    """
    _FAILURES.clear()
    _MANUAL_REVIEW.clear()
    all_tenders: list[dict] = []
    all_jobs: list[dict] = []
    report: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_process_newspaper, p): p for p in NEWSPAPERS}
        for fut in as_completed(futs):
            paper = futs[fut]
            name = paper["name"]
            source_id = paper.get("source_id") or f"newspaper-{core.make_source_id(name)}"
            try:
                t, j, status = fut.result()
            except Exception as exc:
                t, j, status = [], [], f"error:{type(exc).__name__}"
                _log_fail(name, "", "process", exc)
            all_tenders += t
            all_jobs += j
            related_failures = [f for f in _FAILURES if f.get("source") == name]
            report[source_id] = {
                "source_id": source_id, "source_name": name,
                "tenders": len(t), "jobs": len(j), "count": len(t) + len(j),
                "status": status,
                "error": (related_failures[-1]["error"] if related_failures else None),
            }

    tenders = core.merge_duplicate_records(all_tenders, "tender")
    jobs = core.merge_duplicate_records(all_jobs, "job")
    return {"tenders": tenders, "jobs": jobs, "report": report,
            "failures": list(_FAILURES), "manual_review": list(_MANUAL_REVIEW),
            "generated_at": core._now_iso()}


# Columns the DB tables actually have — the rich extra fields (eligibility,
# contact, sources, age_limit, source_url) live in the JSON output only; for the
# DB we fold them into `description` so nothing is lost but the upsert stays valid.
_TENDER_COLS = {"source_id", "title", "state", "district", "organization", "nit_no",
                "category", "value_text", "value_lakhs", "emd", "published_date",
                "deadline", "opening_date", "newspaper", "document_url",
                "description", "source_portal", "added_by", "scraped_at"}
_JOB_COLS = {"source_id", "title", "state", "district", "department", "category",
             "vacancies", "qualification", "salary", "deadline", "description",
             "document_url", "apply_link", "ai_score", "source_portal", "scraped_at"}


def _table_safe(rec: dict, cols: set, extra_into_desc: list[str]) -> dict:
    """Keep only real table columns; fold the named extra fields into description."""
    notes = []
    for f in extra_into_desc:
        v = rec.get(f)
        if v:
            notes.append(f"{f.replace('_', ' ').title()}: {v}")
    if rec.get("sources") and len(rec["sources"]) > 1:
        papers = ", ".join(s.get("newspaper") for s in rec["sources"] if s.get("newspaper"))
        if papers:
            notes.append(f"Also printed in: {papers}")
    safe = {k: v for k, v in rec.items() if k in cols}
    if notes:
        base = safe.get("description") or ""
        safe["description"] = (base + ("  |  " if base else "") + "  |  ".join(notes))[:500]
    return safe


def scrape() -> list[dict]:
    """Ingest hook: de-duplicated canonical newspaper tender records."""
    return collect()["tenders"]


def scrape_jobs() -> list[dict]:
    """Ingest hook: de-duplicated canonical newspaper job records."""
    return collect()["jobs"]


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import argparse
    ap = argparse.ArgumentParser(description="Regional-newspaper government-notice collector")
    ap.add_argument("--dump", metavar="FILE", help="write the full structured JSON to FILE")
    args = ap.parse_args()

    t0 = time.time()
    if not os.getenv("GEMINI_API_KEY"):
        print("NOTE: GEMINI_API_KEY not set — assets will be discovered/fetched but "
              "Vision extraction is skipped (honest 0 records).")
    out = collect()
    print("=" * 64)
    print("  NEWSPAPER COLLECTOR SUMMARY")
    print("=" * 64)
    for name, r in out["report"].items():
        print(f"  {name:<22} tenders={r['tenders']:<3} jobs={r['jobs']:<3} [{r['status']}]")
    print("-" * 64)
    print(f"  master tenders: {len(out['tenders'])}   master jobs: {len(out['jobs'])}"
          f"   failures: {len(out['failures'])}   {time.time()-t0:.1f}s")
    if out["failures"]:
        print("  failure log (first 8):")
        for f in out["failures"][:8]:
            print(f"    - [{f['source']}] {f['stage']}: {f['error'][:80]}")
    if args.dump:
        Path(args.dump).write_text(json.dumps(out, ensure_ascii=False, indent=2,
                                              default=str), encoding="utf-8")
        print(f"  wrote {args.dump}")
