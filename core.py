"""
core.py — the single source of truth for Opporta's data shape.

Everything (the ingestion pipeline, the scrapers, the Streamlit app) speaks the
schema defined here. This is the file that fixes the "four scrapers, four
schemas" problem: there is now exactly one normalized record shape for tenders
and one for jobs.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, date
from dateutil import parser as dateparser  # python-dateutil

# Your business profile — used by the win-fit score. Override via .env if you like.
DEFAULT_TURNOVER_LAKHS = 500.0  # 5 Crore = 500 Lakh


# ---------------------------------------------------------------------------
# AI call status — lets the UI tell the user WHY an AI call failed
# (quota hit vs. missing/invalid key vs. network) instead of a generic error.
# ---------------------------------------------------------------------------
LAST_AI_ERROR: dict = {"kind": None, "detail": ""}


def record_ai_error(exc) -> None:
    """Classify and store the most recent AI failure."""
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
    LAST_AI_ERROR["kind"] = kind
    LAST_AI_ERROR["detail"] = msg[:300]


def clear_ai_error() -> None:
    LAST_AI_ERROR["kind"] = None
    LAST_AI_ERROR["detail"] = ""


def ai_error_message():
    """Return (severity, text) for the last AI failure, or None if there was none.

    severity is one of 'warning' | 'error' so the UI can pick st.warning/st.error.
    """
    kind = LAST_AI_ERROR.get("kind")
    if not kind:
        return None
    if kind == "quota":
        return ("warning",
                "⏳ Opporta Intelligence has hit its usage limit (quota) for the moment. "
                "This is temporary — please try again in a few minutes. Your key is fine.")
    if kind == "auth":
        return ("error",
                "🔑 Opporta Intelligence couldn't authenticate. The GEMINI_API_KEY is missing "
                "or invalid in this app's secrets — add a valid key to enable AI features.")
    if kind == "network":
        return ("warning",
                "🌐 Couldn't reach the AI service just now (network/temporary issue). Please retry.")
    return ("error",
            f"⚠ AI service error — please try again. ({LAST_AI_ERROR.get('detail', '')[:140]})")


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
    """Parse '24 Jun 2026', '2026-07-15', etc. Returns None if unparseable."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"n/a", "nan", "none"}:
        return None
    try:
        return dateparser.parse(s, dayfirst=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def parse_int(raw) -> int | None:
    if raw is None:
        return None
    digits = re.findall(r"\d+", str(raw).replace(",", ""))
    return int(digits[0]) if digits else None


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
    return datetime.utcnow().isoformat()


def tender_record(*, title, state, organization, category=None, district=None,
                  value_text=None, value_lakhs=None, deadline=None, emd=None,
                  contractor_class=None, experience=None, eligibility=None,
                  description=None, requirements=None, document_url=None,
                  ai_score=None, source_portal=None):
    d = parse_date(deadline)
    v = value_lakhs if value_lakhs is not None else parse_value_to_lakhs(value_text)
    if ai_score is None:
        ai_score, _ = win_fit_score(v, category, eligibility, experience, d)
    return {
        "source_id": make_source_id(title, organization, deadline),
        "title": (title or "Untitled tender").strip()[:300],
        "state": (state or "").strip() or None,
        "district": (district or "").strip() or None,
        "organization": (organization or "").strip() or None,
        "category": (category or "").strip() or None,
        "value_text": (str(value_text).strip() if value_text else None),
        "value_lakhs": v,
        "deadline": d.isoformat() if d else None,
        "emd": (str(emd).strip() if emd else None),
        "contractor_class": (contractor_class or "").strip() or None,
        "experience": (experience or "").strip() or None,
        "eligibility": (eligibility or "").strip() or None,
        "description": (description or "").strip() or None,
        "requirements": (requirements or "").strip() or None,
        "document_url": (document_url or "").strip() or None,
        "ai_score": int(ai_score) if ai_score is not None else None,
        "source_portal": (source_portal or "").strip() or None,
        "scraped_at": _now_iso(),
    }


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
               ai_score=None, source_portal=None, category=None):
    d = parse_date(deadline)
    return {
        "source_id": make_source_id(title, department, deadline),
        "title": (title or "Untitled position").strip()[:300],
        "state": (state or "").strip() or None,
        "district": (district or "").strip() or None,
        "department": (department or "").strip() or None,
        "category": category or classify_job_category(title or "", department or ""),
        "vacancies": parse_int(vacancies),
        "qualification": (qualification or "").strip() or None,
        "salary": (str(salary).strip() if salary else None),
        "deadline": d.isoformat() if d else None,
        "description": (description or "").strip() or None,
        "document_url": (document_url or "").strip() or None,
        "apply_link": (apply_link or "").strip() or None,
        "ai_score": int(ai_score) if ai_score is not None else None,
        "source_portal": (source_portal or "").strip() or None,
        "scraped_at": _now_iso(),
    }


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

    # --- Sector relevance ---
    sectors = [s.lower() for s in profile.get("sectors", [])]
    cat = str(tender.get("category") or "").lower()
    if sectors:
        if any(s in cat or cat in s for s in sectors):
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
