"""
core.py — the single source of truth for Opporta's data shape.

Everything (the ingestion pipeline, the scrapers, the Streamlit app) speaks the
schema defined here. This is the file that fixes the "four scrapers, four
schemas" problem: there is now exactly one normalized record shape for tenders
and one for jobs.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from difflib import SequenceMatcher
from datetime import datetime, date, timezone
from dateutil import parser as dateparser  # python-dateutil

# Your business profile — used by the win-fit score. Override via .env if you like.
DEFAULT_TURNOVER_LAKHS = 500.0  # 5 Crore = 500 Lakh


# ---------------------------------------------------------------------------
# AI call status — lets the UI tell the user WHY an AI call failed
# (quota hit vs. missing/invalid key vs. network) instead of a generic error.
#
# Stored THREAD-LOCAL: Streamlit runs each user session in its own ScriptRunner
# thread, so a module-level dict would leak one user's AI error to another. A
# threading.local() store isolates it per session.
# ---------------------------------------------------------------------------
_AI_ERR = threading.local()


def _ai_err_state() -> dict:
    d = getattr(_AI_ERR, "state", None)
    if d is None:
        d = _AI_ERR.state = {"kind": None, "detail": ""}
    return d


def record_ai_error(exc) -> None:
    """Classify and store the most recent AI failure (for this session)."""
    msg = str(exc)
    low = msg.lower()
    if any(s in low for s in ("429", "quota", "rate limit", "rate_limit",
                              "resource_exhausted", "resource exhausted", "exceeded")):
        kind = "quota"
    elif any(s in low for s in ("401", "403", "unauthenticated", "unauthorized",
                                "permission_denied", "permission denied", "api key",
                                "api_key", "invalid authentication", "no api key")):
        kind = "auth"
    elif any(s in low for s in ("timeout", "timed out", "connection", "network",
                                "temporarily", "503", "502", "unavailable")):
        kind = "network"
    else:
        kind = "error"
    st = _ai_err_state()
    st["kind"] = kind
    st["detail"] = msg[:300]


def clear_ai_error() -> None:
    st = _ai_err_state()
    st["kind"] = None
    st["detail"] = ""


def ai_error_message():
    """Return (severity, text) for the last AI failure, or None if there was none.

    severity is one of 'warning' | 'error' so the UI can pick st.warning/st.error.
    """
    st = _ai_err_state()
    kind = st.get("kind")
    if not kind:
        return None
    if kind == "quota":
        return ("warning",
                "⏳ Opporta Intelligence has hit its usage limit (quota) for the moment. "
                "This is temporary — please try again in a few minutes. Your key is fine.")
    if kind == "auth":
        return ("error",
                "🔑 Opporta Intelligence couldn't authenticate. The GEMINI_API_KEY is missing "
                "or invalid in this app's secrets — add a valid key to enable Opporta Intelligence.")
    if kind == "network":
        return ("warning",
                "🌐 Couldn't reach Opporta Intelligence just now (network/temporary issue). Please retry.")
    return ("error",
            f"⚠ Opporta Intelligence error — please try again. ({st.get('detail', '')[:140]})")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
def parse_value_to_lakhs(raw) -> float | None:
    """Convert messy money strings into a numeric value in LAKHS.

    Examples:
        "₹ 45.00 L"   -> 45.0
        "₹ 2.36 Cr"   -> 236.0
        "₹4,500,000"  -> 45.0        (absolute rupees -> lakhs)
        "10171.0"     -> 10171.0     (already lakhs, e.g. estimated_value_lakhs)
        "₹ 45000 /mo" -> None        (this is a salary, not a tender value)
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"n/a", "nan", "none", "exempted"}:
        return None
    if "/mo" in s.lower() or "month" in s.lower():
        return None  # salaries are handled separately

    is_cr = bool(re.search(r"\bcr\b|crore", s, re.I))
    is_l = bool(re.search(r"\bl\b|lakh|lac", s, re.I))

    digits = re.findall(r"[\d.]+", s.replace(",", ""))
    if not digits:
        return None
    try:
        num = float(digits[0])
    except ValueError:
        return None

    if is_cr:
        return round(num * 100, 2)        # 1 Cr = 100 L
    if is_l:
        return round(num, 2)
    # No unit. Heuristic: a big absolute rupee figure -> convert to lakhs.
    if num >= 100000:
        return round(num / 100000, 2)
    return round(num, 2)                  # assume already in lakhs


def parse_date(raw) -> date | None:
    """Parse '24 Jun 2026', '2026-07-15', '10-06-2026', ISO datetimes, etc.

    ISO-style YYYY-MM-DD[...] strings are parsed WITHOUT dayfirst — otherwise
    dateutil's dayfirst=True swaps month/day on ISO dates (e.g. '2026-06-10'
    became Oct 6). Indian DD-MM-YYYY strings still use dayfirst=True.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"n/a", "nan", "none", "nat"}:
        return None
    # ISO date / datetime (starts with 4-digit year) → unambiguous, no dayfirst
    iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}", s))
    try:
        return dateparser.parse(s, dayfirst=not iso).date()
    except (ValueError, OverflowError, TypeError):
        return None


def parse_int(raw) -> int | None:
    if raw is None:
        return None
    digits = re.findall(r"\d+", str(raw).replace(",", ""))
    return int(digits[0]) if digits else None


def parse_bool(raw) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def make_source_id(*parts) -> str:
    """Deterministic dedup key from the fields that identify a record."""
    basis = "|".join(str(p or "").strip().lower() for p in parts)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Transparent "AI" win-fit score
# ---------------------------------------------------------------------------
def win_fit_score(value_lakhs, category, eligibility, experience,
                  deadline, turnover_lakhs=DEFAULT_TURNOVER_LAKHS):
    """A simple, explainable fit score (0-100) plus the reasons behind it.

    This is deliberately rule-based and honest. It is NOT a black box and is
    NOT trained on outcomes. When you have real bid/win history, replace this
    with a learned model — but a transparent baseline beats a fake one.
    """
    score = 50
    reasons = []

    # Contract size vs your capacity: sweet spot is up to ~half your turnover.
    if value_lakhs is not None:
        if 0 < value_lakhs <= turnover_lakhs * 0.5:
            score += 25
            reasons.append("Contract size is comfortably within your capacity")
        elif value_lakhs <= turnover_lakhs:
            score += 10
            reasons.append("Contract size is sizeable but manageable")
        elif value_lakhs > turnover_lakhs * 2:
            score -= 20
            reasons.append("Contract may be too large for current turnover")

    # Eligibility signal carried from the source, if present.
    if eligibility and "eligible" in str(eligibility).lower():
        score += 10
        reasons.append("Marked eligible at source")
    elif eligibility and "review" in str(eligibility).lower():
        score -= 5
        reasons.append("Flagged for eligibility review")

    # Experience barrier.
    if experience and "no experience" in str(experience).lower():
        score += 8
        reasons.append("No prior experience required")
    elif experience and "5+" in str(experience):
        score -= 8
        reasons.append("Requires 5+ years experience")

    # Deadline pressure: too soon is risky to prepare for.
    if deadline:
        days = (deadline - date.today()).days
        if days < 5:
            score -= 12
            reasons.append(f"Closes very soon ({days} days)")
        elif days > 30:
            score += 5
            reasons.append("Comfortable time to prepare a bid")

    score = max(0, min(100, score))
    return score, reasons


# ---------------------------------------------------------------------------
# Normalizers: turn each CSV row into the unified record shape
# ---------------------------------------------------------------------------
def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# Columns supported by the original Supabase schema.  Ingest uses these as a
# compatibility fallback when a deployment has not applied the additive Phase 3
# migration yet.  Local CSVs always retain the complete canonical records.
TENDER_DB_FIELDS = {
    "source_id", "title", "state", "district", "organization", "category",
    "value_text", "value_lakhs", "deadline", "emd", "contractor_class",
    "experience", "eligibility", "description", "requirements", "document_url",
    "ai_score", "source_portal", "scraped_at",
}
JOB_DB_FIELDS = {
    "source_id", "title", "state", "district", "department", "category",
    "vacancies", "qualification", "salary", "deadline", "description",
    "document_url", "apply_link", "ai_score", "source_portal", "scraped_at",
}

TENDER_SCHEMA_FIELDS = (
    "source_id", "title", "state", "district", "department", "organization",
    "source_type", "source_name", "source_url", "document_url", "tender_no",
    "category", "subcategory", "sector", "value_text", "value_lakhs",
    "estimated_value", "emd", "deadline", "opening_date", "published_date",
    "location", "eligibility", "contractor_class", "experience",
    "required_turnover", "required_experience", "required_documents",
    "requirements", "description", "submission_mode", "online_or_offline",
    "newspaper_name", "page_no", "confidence_score", "ocr_text", "language",
    "is_corrigendum", "linked_original_tender", "all_sources", "source_count",
    "first_seen_at", "last_seen_at", "scraped_at", "status",
    "requires_manual_review", "ai_score",
)
JOB_SCHEMA_FIELDS = (
    "source_id", "title", "state", "district", "department", "source_type",
    "source_name", "source_url", "document_url", "advertisement_no", "category",
    "subcategory", "field", "qualification", "vacancies", "age_limit", "salary",
    "deadline", "application_start_date", "application_end_date", "exam_date",
    "application_fee", "apply_link", "selection_process", "reservation_info",
    "description", "language", "ocr_text", "confidence_score",
    "online_or_offline", "all_sources", "source_count", "first_seen_at",
    "last_seen_at", "scraped_at", "status", "requires_manual_review", "ai_score",
    "source_portal",
)


TENDER_TAXONOMY = [
    "Civil Construction", "Road & Bridge", "Electrical", "Solar & Energy",
    "Water/Irrigation", "IT/Software/Hardware", "CCTV/Surveillance",
    "Medical Equipment", "Medicines", "Vehicle Hiring", "Transport",
    "Coal/Mining", "Manpower", "Security", "Housekeeping", "Food/Catering",
    "Printing/Advertisement", "Stationery", "Furniture", "Education Supply",
    "Agriculture", "Municipal/Sanitation", "Waste Management", "Consultancy",
    "CA/Audit", "Legal", "Survey/GIS", "Event Management",
]
_TENDER_TAXONOMY_KEYWORDS = [
    ("Road & Bridge", ["road", "bridge", "highway", "culvert", "सड़क", "पुल"]),
    ("Solar & Energy", ["solar", "renewable", "energy", "सौर"]),
    ("CCTV/Surveillance", ["cctv", "surveillance", "camera", "video wall"]),
    ("IT/Software/Hardware", ["software", "hardware", "computer", "server", "network", "website", "it service"]),
    ("Medical Equipment", ["medical equipment", "surgical", "diagnostic", "hospital equipment"]),
    ("Medicines", ["medicine", "drug", "pharma", "tablet", "औषध"]),
    ("Water/Irrigation", ["water", "irrigation", "canal", "pipeline", "sewer", "जल", "सिंचाई"]),
    ("Electrical", ["electrical", "transformer", "cable", "street light", "विद्युत"]),
    ("Vehicle Hiring", ["vehicle hiring", "hire of vehicle", "वाहन किराया"]),
    ("Transport", ["transport", "logistics", "freight", "haulage"]),
    ("Coal/Mining", ["coal", "mining", "mine", "खनन"]),
    ("Manpower", ["manpower", "outsourcing", "staff supply", "human resource"]),
    ("Security", ["security guard", "security service", "watch and ward"]),
    ("Housekeeping", ["housekeeping", "cleaning service"]),
    ("Food/Catering", ["catering", "food supply", "meal", "भोजन"]),
    ("Printing/Advertisement", ["printing", "advertisement", "publicity", "प्रिंट", "विज्ञापन"]),
    ("Stationery", ["stationery", "office supply", "लेखन सामग्री"]),
    ("Furniture", ["furniture", "chair", "desk", "फर्नीचर"]),
    ("Education Supply", ["school supply", "education kit", "textbook", "uniform"]),
    ("Agriculture", ["agriculture", "seed", "fertilizer", "कृषि", "बीज"]),
    ("Waste Management", ["solid waste", "waste management", "garbage"]),
    ("Municipal/Sanitation", ["municipal", "sanitation", "nagar nigam", "स्वच्छता"]),
    ("CA/Audit", ["chartered accountant", "statutory audit", "internal audit", " ca "]),
    ("Legal", ["legal service", "advocate", "law firm"]),
    ("Survey/GIS", ["survey", "gis", "mapping", "geospatial"]),
    ("Event Management", ["event management", "event organiser", "कार्यक्रम"]),
    ("Consultancy", ["consultancy", "consultant", "dpr preparation", "advisory"]),
    ("Civil Construction", ["construction", "civil work", "building", "repair", "renovation", "rcc"]),
]

JOB_TAXONOMY = [
    "Police", "Teaching", "Assistant Professor", "Health/Nursing/Medical",
    "Engineering", "IT/Computer Operator", "Clerk/Assistant",
    "Accountant", "CA/Audit/Finance", "Patwari/Revenue", "Forest",
    "Court/Judiciary", "Apprenticeship", "Municipal Jobs",
    "District Contract Jobs", "PSC", "Vyapam", "UPSSSC", "UPPSC",
    "University Jobs",
]
_JOB_TAXONOMY_KEYWORDS = [
    ("UPSSSC", ["upsssc"]),
    ("UPPSC", ["uppsc"]),
    ("Vyapam", ["vyapam", "व्यापम"]),
    ("PSC", ["public service commission", "cgpsc", "psc"]),
    ("Assistant Professor", ["assistant professor", "associate professor"]),
    ("University Jobs", ["university", "विश्वविद्यालय"]),
    ("Court/Judiciary", ["court", "judiciary", "judge", "न्यायालय"]),
    ("Police", ["police", "constable", "sub inspector", "आरक्षक"]),
    ("Teaching", ["teacher", "lecturer", "tgt", "pgt", "शिक्षक"]),
    ("Health/Nursing/Medical", ["nurse", "medical", "doctor", "health", "pharmacist", "स्वास्थ्य"]),
    ("Engineering", ["engineer", "civil", "electrical", "mechanical", "अभियंता"]),
    ("IT/Computer Operator", ["computer operator", "programmer", "software", "data entry"]),
    ("CA/Audit/Finance", ["chartered accountant", "audit", "finance"]),
    ("Accountant", ["accountant", "accounts officer", "लेखापाल"]),
    ("Patwari/Revenue", ["patwari", "revenue", "lekhpal", "पटवारी"]),
    ("Forest", ["forest", "वनरक्षक", "ranger"]),
    ("Apprenticeship", ["apprentice", "apprenticeship"]),
    ("Municipal Jobs", ["municipal", "nagar nigam", "नगर निगम"]),
    ("District Contract Jobs", ["district", "collector", "contractual", "संविदा"]),
    ("Clerk/Assistant", ["clerk", "assistant", "stenographer", "कार्यालय सहायक"]),
]


def classify_tender_subcategory(title=None, organization=None, category=None,
                                description=None) -> str:
    blob = f" {title or ''} {organization or ''} {category or ''} {description or ''} ".lower()
    for label, keywords in _TENDER_TAXONOMY_KEYWORDS:
        if any(keyword in blob for keyword in keywords):
            return label
    return "Civil Construction" if "work" in blob else "Consultancy"


def classify_job_taxonomy(title=None, department=None, description=None) -> str:
    blob = f" {title or ''} {department or ''} {description or ''} ".lower()
    for label, keywords in _JOB_TAXONOMY_KEYWORDS:
        if any(keyword in blob for keyword in keywords):
            return label
    return "Clerk/Assistant"


def lifecycle_status(deadline, confidence_score=None, requires_manual_review=False) -> str:
    if requires_manual_review or (confidence_score is not None and confidence_score < 55):
        return "needs_review"
    d = parse_date(deadline)
    if not d:
        return "active"
    days = (d - date.today()).days
    if days < -30:
        return "archived"
    if days < 0:
        return "expired"
    if days <= 7:
        return "closing_soon"
    return "active"


def tender_record(*, title, state, organization, category=None, district=None,
                  value_text=None, value_lakhs=None, deadline=None, emd=None,
                  contractor_class=None, experience=None, eligibility=None,
                  description=None, requirements=None, document_url=None,
                  ai_score=None, source_portal=None, department=None,
                  source_type=None, source_name=None, source_url=None,
                  tender_no=None, subcategory=None, sector=None,
                  estimated_value=None, opening_date=None, published_date=None,
                  location=None, required_turnover=None, required_experience=None,
                  required_documents=None, submission_mode=None,
                  online_or_offline=None, newspaper_name=None, page_no=None,
                  confidence_score=None, ocr_text=None, language=None,
                  is_corrigendum=False, linked_original_tender=None,
                  last_seen_at=None, status=None, requires_manual_review=False):
    d = parse_date(deadline)
    v = (value_lakhs if value_lakhs is not None
         else parse_value_to_lakhs(estimated_value if estimated_value is not None else value_text))
    parsed_ai_score = parse_int(ai_score)
    if parsed_ai_score is None:
        parsed_ai_score, _ = win_fit_score(
            v, category, eligibility, experience, d)
    scraped = _now_iso()
    source_label = source_name or source_portal
    source_link = source_url or document_url
    detailed = subcategory or classify_tender_subcategory(
        title, organization, category, description)
    confidence = parse_int(confidence_score)
    return {
        "source_id": (make_source_id(tender_no, title, organization, deadline)
                      if tender_no else make_source_id(title, organization, deadline)),
        "title": (title or "Untitled tender").strip()[:300],
        "state": (state or "").strip() or None,
        "district": (district or "").strip() or None,
        "department": (department or organization or "").strip() or None,
        "organization": (organization or "").strip() or None,
        "category": (category or "").strip() or None,
        "subcategory": detailed,
        "sector": sector or classify_sector(title, organization, category),
        "value_text": (str(value_text).strip() if value_text else None),
        "value_lakhs": v,
        "estimated_value": (str(estimated_value).strip()
                            if estimated_value is not None else
                            (str(value_text).strip() if value_text else None)),
        "deadline": d.isoformat() if d else None,
        "opening_date": (parse_date(opening_date).isoformat()
                         if parse_date(opening_date) else None),
        "published_date": (parse_date(published_date).isoformat()
                           if parse_date(published_date) else None),
        "emd": (str(emd).strip() if emd else None),
        "contractor_class": (contractor_class or "").strip() or None,
        "experience": (experience or "").strip() or None,
        "tender_no": (str(tender_no).strip() if tender_no else None),
        "location": (location or district or "").strip() or None,
        "eligibility": (eligibility or "").strip() or None,
        "description": (description or "").strip() or None,
        "requirements": (requirements or "").strip() or None,
        "required_turnover": (str(required_turnover).strip() if required_turnover else None),
        "required_experience": (str(required_experience).strip()
                                if required_experience else
                                ((experience or "").strip() or None)),
        "required_documents": required_documents or [],
        "submission_mode": (submission_mode or "").strip() or None,
        "online_or_offline": (online_or_offline or
                              ("offline" if "offline" in str(source_type or source_portal).lower()
                               or newspaper_name else "online")),
        "newspaper_name": (newspaper_name or "").strip() or None,
        "page_no": (str(page_no).strip() if page_no else None),
        "confidence_score": confidence,
        "ocr_text": (ocr_text or "").strip()[:10000] or None,
        "language": (language or "").strip() or None,
        "is_corrigendum": parse_bool(is_corrigendum),
        "linked_original_tender": linked_original_tender,
        "document_url": (document_url or "").strip() or None,
        "ai_score": parsed_ai_score,
        "source_portal": (source_portal or "").strip() or None,
        "source_type": (source_type or "tender_portal").strip(),
        "source_name": (source_label or "").strip() or None,
        "source_url": (source_link or "").strip() or None,
        "all_sources": ([{"source_name": source_label, "source_url": source_link}]
                        if source_label or source_link else []),
        "source_count": 1,
        "first_seen_at": scraped,
        "last_seen_at": last_seen_at or scraped,
        "scraped_at": scraped,
        "status": status or lifecycle_status(d, confidence, requires_manual_review),
        "requires_manual_review": parse_bool(requires_manual_review),
    }


# ---------------------------------------------------------------------------
# Tender category normalization — fold the 45+ raw scraped categories into a
# clean set of ~10 parent buckets used for filtering, the sector picker, and
# the fit-score sector match (so vocabulary is consistent end-to-end).
# ---------------------------------------------------------------------------
CATEGORY_BUCKETS = [
    "Civil & Construction", "Water & Irrigation", "Electrical & Energy",
    "Medical & Healthcare", "IT & Technology", "Transport & Logistics",
    "Manufacturing & Goods", "Municipal Projects", "Consultancy & Survey",
    "Police & Security", "Government & Administration", "Printing & Advertising",
    "Miscellaneous",
]

# Checked in order — first keyword hit wins, so put narrower buckets first.
_BUCKET_KEYWORDS = [
    ("Water & Irrigation",    ["water", "irrigation", "pipe", "drilling", "boring",
                               "canal", "marine", "dam", "sewer", "drainage", "borewell"]),
    ("Electrical & Energy",   ["electric", "solar", "energy", "power", "lighting",
                               "street light", "transformer", "ht ", "lt "]),
    ("Medical & Healthcare",  ["medical", "health", "hospital", "surgical", "pharma",
                               "drug", "medicine", "nursing"]),
    ("IT & Technology",       ["it services", "software", "computer", "network",
                               "digital", "cctv", "data cent", "website", "hardware"]),
    ("Transport & Logistics", ["transport", "vehicle", "crane", "shipping", "freight",
                               "logistic", "coal", "mining", "loading", "haul"]),
    ("Municipal Projects",    ["municipal", "nagar", "urban", "sanitation", "solid waste"]),
    ("Consultancy & Survey",  ["survey", "investigation", "consultanc", "design",
                               "dpr", "audit", "advisory"]),
    ("Manufacturing & Goods", ["manufactur", "abrasive", "mechanical", "equipment",
                               "goods", "material", "memento", "medal", "dairy",
                               "furniture", "supply", "stationery", "uniform"]),
    ("Civil & Construction",  ["civil", "construction", "road", "bridge", "building",
                               "composite", "concrete", "rcc", "works", "structure"]),
]


def normalize_category(raw) -> str:
    """Map a raw scraped category string to one of CATEGORY_BUCKETS."""
    s = str(raw or "").strip().lower()
    if not s or s in ("nan", "none", "nat", "other", "miscellaneous", "misc"):
        return "Miscellaneous"
    for bucket, kws in _BUCKET_KEYWORDS:
        if any(kw in s for kw in kws):
            return bucket
    return "Miscellaneous"


# Sector signals that live in the TITLE / ORGANISATION rather than the scraped
# 'category' field — so police, collectorate/admin and printing work surfaces as
# its own filterable sector instead of vanishing into "Civil"/"Miscellaneous".
# Keywords are kept specific to avoid false positives (e.g. "collectorate" not a
# bare "collector", which would catch "dust collector").
_SECTOR_OVERRIDES = [
    ("Police & Security", [
        "police", "आरक्षी", "थाना", "thana ", "constab", "home guard", "homeguard",
        "jail", "prison", "जेल", "forensic", "superintendent of police", "sp office",
        "central jail", "police line", "police station", "armed force", "lock-up",
    ]),
    ("Government & Administration", [
        "collectorate", "कलेक्टर", "office of the collector", "collector office",
        "district collector", "district administration", "tehsil", "तहसील", "tahsil",
        "revenue department", "janpad panchayat", "जनपद", "zila panchayat", "जिला पंचायत",
        "sachivalaya", "mantralaya", "मंत्रालय", "vidhan sabha", "विधानसभा",
        "sdm office", "tahsildar", "naib tehsildar",
    ]),
    ("Printing & Advertising", [
        "printing", "मुद्रण", "advertis", "विज्ञापन", "publicity", "प्रचार-प्रसार",
        "jansampark", "जनसंपर्क", "samvad", "हाेर्डिंग", "hoarding", "calendar printing",
        "diary printing", "stationery printing",
    ]),
]


def classify_sector(title=None, organization=None, category=None) -> str:
    """Sector bucket from title + organisation + category.

    Checks the title/org for police / administration / printing signals first
    (these never appear in the scraped 'category' field), then falls back to
    normalize_category(category). Used for both filtering and sector scoring so
    the vocabulary stays consistent end-to-end.
    """
    blob = f"{title or ''} {organization or ''} {category or ''}"
    low  = blob.lower()
    for bucket, kws in _SECTOR_OVERRIDES:
        if any(kw in low or kw in blob for kw in kws):
            return bucket
    return normalize_category(category)


# Light keyword router so the Jobs tab's category pills actually do something.
_JOB_CATEGORY_MAP = {
    "Health": ["nurse", "medical", "health", "ecg", "doctor", "pharma"],
    "Police": ["police", "constable", "inspector", "security"],
    "Education": ["professor", "teacher", "education", "lecturer", "warden"],
    "Engineering": ["engineer", "civil", "electrical", "mechanical", "developer", "software", "python", "network"],
    "Administration": ["assistant", "clerk", "officer", "administration", "services"],
}


def classify_job_category(title, department=""):
    text = f"{title} {department}".lower()
    for cat, kws in _JOB_CATEGORY_MAP.items():
        if any(kw in text for kw in kws):
            return cat
    return "General"


def job_record(*, title, state=None, department=None, district=None,
               vacancies=None, qualification=None, salary=None, deadline=None,
               description=None, document_url=None, apply_link=None,
               ai_score=None, source_portal=None, category=None,
               source_type=None, source_name=None, source_url=None,
               advertisement_no=None, subcategory=None, field=None,
               age_limit=None, application_start_date=None,
               application_end_date=None, exam_date=None,
               application_fee=None, selection_process=None,
               reservation_info=None, language=None, ocr_text=None,
               confidence_score=None, last_seen_at=None, status=None,
               online_or_offline=None, requires_manual_review=False):
    d = parse_date(deadline)
    scraped = _now_iso()
    detailed = subcategory or classify_job_taxonomy(title, department, description)
    confidence = parse_int(confidence_score)
    parsed_ai_score = parse_int(ai_score)
    source_label = source_name or source_portal
    source_link = source_url or document_url or apply_link
    return {
        "source_id": (make_source_id(advertisement_no, title, department, deadline)
                      if advertisement_no else make_source_id(title, department, deadline)),
        "title": (title or "Untitled position").strip()[:300],
        "state": (state or "").strip() or None,
        "district": (district or "").strip() or None,
        "department": (department or "").strip() or None,
        "category": category or detailed,
        "subcategory": detailed,
        "field": field or detailed,
        "advertisement_no": (str(advertisement_no).strip() if advertisement_no else None),
        "vacancies": parse_int(vacancies),
        "qualification": (qualification or "").strip() or None,
        "age_limit": (str(age_limit).strip() if age_limit else None),
        "salary": (str(salary).strip() if salary else None),
        "deadline": d.isoformat() if d else None,
        "application_start_date": (parse_date(application_start_date).isoformat()
                                   if parse_date(application_start_date) else None),
        "application_end_date": (parse_date(application_end_date).isoformat()
                                 if parse_date(application_end_date) else
                                 (d.isoformat() if d else None)),
        "exam_date": (parse_date(exam_date).isoformat() if parse_date(exam_date) else None),
        "application_fee": (str(application_fee).strip() if application_fee else None),
        "description": (description or "").strip() or None,
        "document_url": (document_url or "").strip() or None,
        "apply_link": (apply_link or "").strip() or None,
        "selection_process": (selection_process or "").strip() or None,
        "reservation_info": (reservation_info or "").strip() or None,
        "language": (language or "").strip() or None,
        "ocr_text": (ocr_text or "").strip()[:10000] or None,
        "confidence_score": confidence,
        "ai_score": parsed_ai_score,
        "source_portal": (source_portal or "").strip() or None,
        "source_type": (source_type or "job_portal").strip(),
        "source_name": (source_label or "").strip() or None,
        "source_url": (source_link or "").strip() or None,
        "online_or_offline": (online_or_offline or
                              ("offline" if "offline" in str(source_type or source_portal).lower()
                               else "online")),
        "all_sources": ([{"source_name": source_label, "source_url": source_link}]
                        if source_label or source_link else []),
        "source_count": 1,
        "first_seen_at": scraped,
        "last_seen_at": last_seen_at or scraped,
        "scraped_at": scraped,
        "status": status or lifecycle_status(d, confidence, requires_manual_review),
        "requires_manual_review": parse_bool(requires_manual_review),
    }


def canonicalize_tender_record(record: dict) -> dict:
    """Return a complete Phase 3 tender without discarding legacy fields.

    Older scrapers use ``nit_no`` and ``closing_date`` while current scrapers
    already return :func:`tender_record` output.  This adapter lets both shapes
    coexist during a rolling deployment.
    """
    r = dict(record or {})
    rec = tender_record(
        title=r.get("title"), state=r.get("state"),
        organization=r.get("organization") or r.get("department"),
        department=r.get("department"), district=r.get("district"),
        category=r.get("category"), subcategory=r.get("subcategory"),
        sector=r.get("sector"), value_text=r.get("value_text"),
        value_lakhs=r.get("value_lakhs"), estimated_value=r.get("estimated_value"),
        deadline=r.get("deadline") or r.get("closing_date"), emd=r.get("emd"),
        contractor_class=r.get("contractor_class"), experience=r.get("experience"),
        eligibility=r.get("eligibility"), description=r.get("description"),
        requirements=r.get("requirements"), document_url=r.get("document_url"),
        ai_score=r.get("ai_score"), source_portal=r.get("source_portal"),
        source_type=r.get("source_type"), source_name=r.get("source_name"),
        source_url=r.get("source_url"), tender_no=r.get("tender_no") or r.get("nit_no"),
        opening_date=r.get("opening_date"), published_date=r.get("published_date"),
        location=r.get("location"), required_turnover=r.get("required_turnover"),
        required_experience=r.get("required_experience"),
        required_documents=r.get("required_documents"),
        submission_mode=r.get("submission_mode"),
        online_or_offline=r.get("online_or_offline"),
        newspaper_name=r.get("newspaper_name") or r.get("newspaper"),
        page_no=r.get("page_no"), confidence_score=r.get("confidence_score"),
        ocr_text=r.get("ocr_text"), language=r.get("language"),
        is_corrigendum=r.get("is_corrigendum", False),
        linked_original_tender=r.get("linked_original_tender"),
        last_seen_at=r.get("last_seen_at"), status=r.get("status"),
        requires_manual_review=r.get("requires_manual_review", False),
    )
    for key in ("source_id", "first_seen_at", "last_seen_at", "scraped_at",
                "all_sources", "source_count"):
        if r.get(key) not in (None, "", [], {}):
            rec[key] = r[key]
    if isinstance(rec.get("all_sources"), str):
        try:
            parsed = json.loads(rec["all_sources"])
            rec["all_sources"] = parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            rec["all_sources"] = []
    if isinstance(rec.get("required_documents"), str):
        try:
            parsed = json.loads(rec["required_documents"])
            rec["required_documents"] = parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            rec["required_documents"] = []
    rec["source_count"] = parse_int(rec.get("source_count")) or max(
        1, len(rec.get("all_sources") or []))
    rec["status"] = lifecycle_status(
        rec.get("deadline"), rec.get("confidence_score"),
        rec.get("requires_manual_review", False))
    return rec


def canonicalize_job_record(record: dict) -> dict:
    """Return a complete Phase 3 job while accepting the legacy job shape."""
    r = dict(record or {})
    rec = job_record(
        title=r.get("title"), state=r.get("state"), department=r.get("department"),
        district=r.get("district"), vacancies=r.get("vacancies"),
        qualification=r.get("qualification"), salary=r.get("salary"),
        deadline=r.get("deadline") or r.get("application_end_date"),
        description=r.get("description"), document_url=r.get("document_url"),
        apply_link=r.get("apply_link"), ai_score=r.get("ai_score"),
        source_portal=r.get("source_portal"), category=r.get("category"),
        source_type=r.get("source_type"), source_name=r.get("source_name"),
        source_url=r.get("source_url"), advertisement_no=r.get("advertisement_no"),
        subcategory=r.get("subcategory"), field=r.get("field"),
        age_limit=r.get("age_limit"),
        application_start_date=r.get("application_start_date"),
        application_end_date=r.get("application_end_date"),
        exam_date=r.get("exam_date"), application_fee=r.get("application_fee"),
        selection_process=r.get("selection_process"),
        reservation_info=r.get("reservation_info"), language=r.get("language"),
        ocr_text=r.get("ocr_text"), confidence_score=r.get("confidence_score"),
        last_seen_at=r.get("last_seen_at"), status=r.get("status"),
        online_or_offline=r.get("online_or_offline"),
        requires_manual_review=r.get("requires_manual_review", False),
    )
    for key in ("source_id", "first_seen_at", "last_seen_at", "scraped_at",
                "all_sources", "source_count"):
        if r.get(key) not in (None, "", [], {}):
            rec[key] = r[key]
    if isinstance(rec.get("all_sources"), str):
        try:
            parsed = json.loads(rec["all_sources"])
            rec["all_sources"] = parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            rec["all_sources"] = []
    rec["source_count"] = parse_int(rec.get("source_count")) or max(
        1, len(rec.get("all_sources") or []))
    rec["status"] = lifecycle_status(
        rec.get("deadline"), rec.get("confidence_score"),
        rec.get("requires_manual_review", False))
    return rec


def _identity_text(value) -> str:
    return re.sub(r"[^a-z0-9\u0900-\u097f]+", " ",
                  str(value or "").lower()).strip()


def _record_source(rec: dict) -> dict:
    return {
        "source_name": rec.get("source_name") or rec.get("source_portal"),
        "source_url": rec.get("source_url") or rec.get("document_url") or rec.get("apply_link"),
        "source_type": rec.get("source_type"),
        "seen_at": rec.get("scraped_at") or _now_iso(),
    }


def _merge_record(master: dict, incoming: dict) -> dict:
    """Merge a duplicate without discarding its provenance."""
    empty = (None, "", [], {})
    for key, value in incoming.items():
        if key in {"source_id", "all_sources", "source_count", "first_seen_at"}:
            continue
        current = master.get(key)
        if current in empty and value not in empty:
            master[key] = value
        elif key in {"description", "requirements", "ocr_text", "qualification",
                     "eligibility"} and value and len(str(value)) > len(str(current or "")):
            master[key] = value
        elif key == "confidence_score" and value is not None:
            master[key] = max(int(current or 0), int(value))

    sources = list(master.get("all_sources") or [])
    for source in list(incoming.get("all_sources") or []) + [_record_source(incoming)]:
        if not source.get("source_name") and not source.get("source_url"):
            continue
        sig = (source.get("source_name"), source.get("source_url"))
        if sig not in {(s.get("source_name"), s.get("source_url")) for s in sources}:
            sources.append(source)
    master["all_sources"] = sources
    master["source_count"] = len(sources) or 1
    master["first_seen_at"] = min(
        str(master.get("first_seen_at") or master.get("scraped_at") or _now_iso()),
        str(incoming.get("first_seen_at") or incoming.get("scraped_at") or _now_iso()))
    master["last_seen_at"] = max(
        str(master.get("last_seen_at") or master.get("scraped_at") or ""),
        str(incoming.get("last_seen_at") or incoming.get("scraped_at") or ""))
    master["requires_manual_review"] = bool(
        master.get("requires_manual_review") or incoming.get("requires_manual_review"))
    master["status"] = lifecycle_status(
        master.get("deadline"), master.get("confidence_score"),
        master.get("requires_manual_review", False))
    return master


def merge_duplicate_records(records: list[dict], kind: str = "tender") -> list[dict]:
    """Cross-source deduplication with exact IDs/URLs plus conservative fuzzy matching.

    Fuzzy comparison is blocked by state and deadline/district, keeping runtime
    bounded and avoiding accidental merges between unrelated notices.
    """
    masters: list[dict] = []
    exact: dict[str, int] = {}
    blocks: dict[tuple, list[int]] = {}
    number_field = "tender_no" if kind == "tender" else "advertisement_no"
    org_field = "organization" if kind == "tender" else "department"

    for raw in records:
        if not isinstance(raw, dict) or not str(raw.get("title") or "").strip():
            continue
        rec = dict(raw)
        rec.setdefault("all_sources", [_record_source(rec)])
        rec.setdefault("source_count", len(rec["all_sources"]) or 1)
        rec.setdefault("first_seen_at", rec.get("scraped_at") or _now_iso())
        rec.setdefault("last_seen_at", rec.get("scraped_at") or _now_iso())
        rec["status"] = lifecycle_status(
            rec.get("deadline"), rec.get("confidence_score"),
            rec.get("requires_manual_review", False))

        exact_keys = []
        number = _identity_text(rec.get(number_field) or rec.get("nit_no"))
        if number:
            number_scope = ":".join((
                _identity_text(rec.get("state")),
                _identity_text(rec.get(org_field)),
            ))
            exact_keys.append(f"number:{number_scope}:{number}")
        for url_field in ("document_url", "source_url", "apply_link"):
            url = str(rec.get(url_field) or "").split("?", 1)[0].rstrip("/").lower()
            if url.startswith("http") and not url.endswith(("tenders", "jobs", "recruitment", "notices")):
                exact_keys.append(f"url:{url}")
        sid = str(rec.get("source_id") or "")
        if sid:
            exact_keys.append(f"sid:{sid}")

        matched = next((exact[key] for key in exact_keys if key in exact), None)
        title_norm = _identity_text(rec.get("title"))
        block = (
            _identity_text(rec.get("state")),
            str(parse_date(rec.get("deadline")) or ""),
            _identity_text(rec.get("district"))[:30],
        )
        if matched is None:
            for idx in blocks.get(block, []):
                candidate = masters[idx]
                title_score = SequenceMatcher(
                    None, title_norm, _identity_text(candidate.get("title"))).ratio()
                if title_score < 0.90:
                    continue
                org_a = _identity_text(rec.get(org_field))
                org_b = _identity_text(candidate.get(org_field))
                org_score = SequenceMatcher(None, org_a, org_b).ratio() if org_a and org_b else 0.8
                val_a = parse_value_to_lakhs(rec.get("estimated_value") or rec.get("value_lakhs"))
                val_b = parse_value_to_lakhs(candidate.get("estimated_value") or candidate.get("value_lakhs"))
                value_close = (val_a is None or val_b is None or
                               abs(val_a - val_b) <= max(1.0, max(val_a, val_b) * 0.03))
                if org_score >= 0.72 and value_close:
                    matched = idx
                    break

        if matched is None:
            matched = len(masters)
            masters.append(rec)
            blocks.setdefault(block, []).append(matched)
        else:
            _merge_record(masters[matched], rec)
        for key in exact_keys:
            exact[key] = matched

    return masters


# ===========================================================================
# PER-USER SCORING  (the SaaS core)
# ---------------------------------------------------------------------------
# The baseline ai_score stored by ingest.py is generic. In a multi-tenant
# product, the score that matters is computed live against the LOGGED-IN
# contractor's profile. This is what lets one feed serve many customers.
# ===========================================================================

# Higher rank = higher capacity. A Class A contractor may bid on works that
# require Class A or lower; a Class C may not bid on Class A works. "Open" = all.
_CLASS_RANK = {"open": 0, "class d": 1, "class c": 2, "class b": 3, "class a": 4,
               "d": 1, "c": 2, "b": 3, "a": 4}


def _rank(label):
    return _CLASS_RANK.get(str(label or "").strip().lower(), 0)


def _exp_years(label):
    s = str(label or "").lower()
    if "5+" in s or "5 +" in s:
        return 5
    if "3-5" in s or "3+" in s:
        return 3
    if "1-3" in s:
        return 1
    return 0


# A contractor's profile. Stored per user (see profiles table / data/profiles.json).
DEFAULT_PROFILE = {
    # ── Contractor / tender fields ──
    "company_name":     "",
    "turnover_lakhs":   500.0,
    "contractor_class": "Class C",
    "experience_years": 3,
    "sectors":          [],
    "states":           ["Chhattisgarh", "Uttar Pradesh"],
    "districts":        [],
    # ── Job seeker fields ──
    "full_name":              "",
    "qualification":          "",   # free text, e.g. "B.Tech Civil, NIT Raipur 2018"
    "degree_type":            "",   # e.g. "B.Tech / B.E. (Engineering)"
    "job_experience_years":   0,
    "job_skills":             [],   # e.g. ["AutoCAD", "MS Office", "Tally"]
    "job_category":           "General",   # General/OBC/SC/ST/EWS
    "languages":              ["Hindi", "English"],
}


def profile_is_configured(profile: dict, has_documents: bool = False) -> bool:
    """True only when the user has supplied REAL data beyond the shipped defaults.

    This is the guard that kills the "veil" bug: until the contractor/job-seeker
    has actually entered something — or uploaded at least one vault document —
    the matching engine must NOT fabricate a score. A pristine DEFAULT_PROFILE
    (Class C, ₹500L turnover, 3 yrs) is treated as EMPTY, because those are
    placeholders, not verified telemetry.

    Verified signals (any one is enough):
      • a company / firm name              • bid sectors selected
      • target districts selected          • a job-seeker full name
      • qualification / degree text         • key skills listed
      • ≥1 document in the secure vault
    """
    if not profile:
        return bool(has_documents)
    text_signals = [
        str(profile.get("company_name") or "").strip(),
        str(profile.get("full_name") or "").strip(),
        str(profile.get("qualification") or "").strip(),
        str(profile.get("degree_type") or "").strip(),
    ]
    list_signals = [
        list(profile.get("sectors") or []),
        list(profile.get("districts") or []),
        list(profile.get("job_skills") or []),
    ]
    if any(text_signals) or any(list_signals):
        return True
    return bool(has_documents)


def score_tender_for_user(tender: dict, profile: dict):
    """Return (score 0-100, reasons[], eligible: bool|None) for THIS user.

    eligible is a hard pass/fail on stated criteria (class, turnover, experience);
    score is a softer relevance/fit number. The UI shows both so a contractor
    instantly sees 'worth my time?' and 'can I even bid?'.
    """
    score, reasons = 50, []
    eligible = True

    # --- Hard eligibility: contractor class ---
    req_rank = _rank(tender.get("contractor_class"))
    if req_rank > 0:
        if _rank(profile.get("contractor_class")) >= req_rank:
            score += 12
            reasons.append(f"You qualify on class ({tender.get('contractor_class')})")
        else:
            eligible = False
            score -= 25
            reasons.append(f"⚠️ Needs {tender.get('contractor_class')}, "
                           f"you are {profile.get('contractor_class')}")

    # --- Hard eligibility: experience ---
    req_exp = _exp_years(tender.get("experience"))
    if req_exp and profile.get("experience_years", 0) < req_exp:
        eligible = False
        score -= 12
        reasons.append(f"⚠️ Requires ~{req_exp}+ yrs experience")
    elif req_exp == 0:
        reasons.append("No experience barrier")

    # --- Value vs capacity (turnover sweet spot) ---
    v = tender.get("value_lakhs")
    turnover = float(profile.get("turnover_lakhs") or 0)
    if v is not None and turnover > 0:
        try:
            v = float(v)
            if v > turnover * 2:
                eligible = False
                score -= 15
                reasons.append("⚠️ Likely above your turnover eligibility")
            elif v <= turnover * 0.5:
                score += 18
                reasons.append("Comfortably within your capacity")
            else:
                score += 6
                reasons.append("Within reach but sizeable")
        except (TypeError, ValueError):
            pass

    # --- Sector relevance (bucket-to-bucket, consistent vocabulary) ---
    sectors = [s.lower() for s in profile.get("sectors", [])]
    cat_bucket = classify_sector(tender.get("title"), tender.get("organization"),
                                 tender.get("category")).lower()
    raw_cat    = str(tender.get("category") or "").lower()
    if sectors:
        # Match on the clean bucket, but still honour an exact raw-category pick.
        if any(s == cat_bucket or s in cat_bucket or s in raw_cat for s in sectors):
            score += 20
            reasons.append("Matches your sector focus")
        else:
            score -= 8

    # --- Hyper-local relevance (your wedge) ---
    districts = [d.lower() for d in profile.get("districts", [])]
    tdist = str(tender.get("district") or "").lower()
    if districts and tdist and any(d in tdist for d in districts):
        score += 10
        reasons.append("In your target district")

    # --- Deadline pressure ---
    d = parse_date(tender.get("deadline"))
    if d:
        days = (d - date.today()).days
        if days < 5:
            score -= 12
            reasons.append(f"Closes very soon ({days}d)")
        elif days > 30:
            score += 5

    return max(0, min(100, score)), reasons, eligible


def state_match(record: dict, profile: dict) -> bool:
    """Two-state product: only show what's in the user's states."""
    states = profile.get("states") or []
    return (not states) or (record.get("state") in states)
