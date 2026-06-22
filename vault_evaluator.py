"""
vault_evaluator.py — Zero-failure binary eligibility gate.

Decides **ELIGIBLE / NOT ELIGIBLE / NEEDS REVIEW** for one contractor against
one tender, using only signals that can never raise:

  * Profile parameters — contractor_class, turnover_lakhs, experience_years,
    registration_year (-> derived years in business).
  * Document Vault registry — each file is classified by its name / filename
    metadata. This is the graceful fallback the spec calls for: when a file's
    *contents* can't be OCR'd or parsed, we still credit the user for having
    the document on record rather than blocking them with an error.

Design rule — extreme defensive programming. Every public function returns a
structured dict and is wrapped so it CANNOT raise: bad, missing, NaN or corrupt
fields degrade to a safe default. A government portal handing us garbage must
never crash a Streamlit Cloud page.

This module *complements* core.score_tender_for_user / bid_engine.readiness_check
(the richer AI/heuristic scorers). It does not replace them — it adds a crisp,
crash-proof yes/no gate on top of the same profile + vault data.
"""

from __future__ import annotations

import datetime as _dt

# Verdict constants — import these instead of hard-coding strings.
ELIGIBLE      = "ELIGIBLE"
NOT_ELIGIBLE  = "NOT ELIGIBLE"
NEEDS_REVIEW  = "NEEDS REVIEW"

# Contractor-class ladder (higher = more capable; "Class A" outranks "Class C").
_CLASS_RANK = {
    "open": 0, "unlimited": 5,
    "class a": 4, "a": 4, "class b": 3, "b": 3,
    "class c": 2, "c": 2, "class d": 1, "d": 1, "class e": 1, "e": 1,
}

# Map a canonical document type -> the keywords we look for in a vault file's
# user-supplied name or original filename. Lower-cased substring match.
_DOC_SIGNATURES = {
    "GST Registration":          ["gst"],
    "PAN Card":                  ["pan"],
    "Contractor Registration":   ["registration", "license", "licence",
                                   "empanel", "enlist", "class "],
    "Turnover / Financials":     ["turnover", "balance sheet", "audited",
                                   "net worth", "networth", "financial",
                                   "itr", "income tax", "ca certificate"],
    "Experience Certificate":    ["experience", "completion", "work order",
                                   "performance certificate", "similar work"],
    "EMD / Bank Guarantee":      ["emd", "bank guarantee", "earnest", "dd ",
                                   "demand draft", "fdr"],
    "Solvency Certificate":      ["solvency"],
    "ISO Certification":         ["iso"],
    "Affidavit":                 ["affidavit", "non-blacklist", "non blacklist",
                                   "undertaking"],
    "Partnership / Incorporation": ["partnership", "incorporation", "moa",
                                   "memorandum", "udyam", "msme", "gumasta"],
}


# ──────────────────────────────────────────────────────────────────────────────
# Defensive primitives — never raise.
# ──────────────────────────────────────────────────────────────────────────────
def _safe_float(v, default: float = 0.0) -> float:
    try:
        f = float(str(v).replace(",", "").strip())
        return default if f != f else f          # NaN guard
    except (TypeError, ValueError, AttributeError):
        return default


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(round(_safe_float(v, float(default))))
    except (TypeError, ValueError):
        return default


def _safe_str(v, default: str = "") -> str:
    try:
        if v is None:
            return default
        s = str(v).strip()
        return s if s and s.lower() not in ("nan", "none", "nat") else default
    except Exception:
        return default


def _class_rank(label) -> int:
    return _CLASS_RANK.get(_safe_str(label).lower(), 0)


# ──────────────────────────────────────────────────────────────────────────────
# Vault registry classification (metadata-only — survives OCR failure)
# ──────────────────────────────────────────────────────────────────────────────
def classify_document(doc) -> set[str]:
    """Best-effort document-type tags from a vault record's metadata.

    `doc` may be a dict ({name, filename, ...}) or a plain string. We only read
    the *name* + *filename* — no file contents — so a scan / image PDF that fails
    OCR still gets classified. Returns an empty set on anything unusable.
    """
    try:
        if isinstance(doc, dict):
            hay = f"{_safe_str(doc.get('name'))} {_safe_str(doc.get('filename'))}".lower()
        else:
            hay = _safe_str(doc).lower()
    except Exception:
        return set()
    if not hay.strip():
        return set()
    tags = set()
    for canonical, kws in _DOC_SIGNATURES.items():
        if any(kw in hay for kw in kws):
            tags.add(canonical)
    return tags


def vault_doc_types(documents) -> set[str]:
    """Union of canonical document types present in the vault registry."""
    found: set[str] = set()
    try:
        for d in (documents or []):
            found |= classify_document(d)
    except Exception:
        pass
    return found


# ──────────────────────────────────────────────────────────────────────────────
# The binary gate
# ──────────────────────────────────────────────────────────────────────────────
def _required_turnover(tender: dict) -> float:
    """Explicit required turnover, else a conservative 30% of tender value."""
    explicit = _safe_float(tender.get("required_turnover_lakhs"))
    if explicit > 0:
        return explicit
    val = _safe_float(tender.get("value_lakhs"))
    return round(val * 0.3, 1) if val > 0 else 0.0


def _years_in_business(profile: dict) -> int:
    """Prefer experience_years; fall back to (this year - registration_year)."""
    exp = _safe_int(profile.get("experience_years"))
    reg = _safe_int(profile.get("registration_year"))
    if reg and 1900 < reg <= _dt.date.today().year:
        exp = max(exp, _dt.date.today().year - reg)
    return exp


def evaluate(tender: dict, profile: dict, documents=None) -> dict:
    """Binary eligibility gate. ALWAYS returns a structured dict, never raises.

    Returns:
      {
        "verdict": ELIGIBLE | NOT_ELIGIBLE | NEEDS_REVIEW,
        "checks":  [ {label, ok: True/False/None, detail} ... ],
        "blockers":     [str, ...],   # hard reasons it is NOT eligible
        "unknowns":     [str, ...],   # things we could not verify
        "have_docs":    [str, ...],   # document types present in the vault
        "missing_docs": [str, ...],   # tender-required docs not found in vault
        "score":   int,              # informational 0-100 (not the gate)
        "summary": str,
      }
    """
    try:
        return _evaluate(tender or {}, profile or {}, documents or [])
    except Exception as exc:        # absolute last-resort guard
        return {
            "verdict": NEEDS_REVIEW,
            "checks": [],
            "blockers": [],
            "unknowns": [f"Could not complete automated check ({type(exc).__name__})."],
            "have_docs": [], "missing_docs": [],
            "score": 0,
            "summary": "Manual review recommended — automated check unavailable.",
        }


def _evaluate(tender: dict, profile: dict, documents) -> dict:
    checks: list[dict] = []
    blockers: list[str] = []
    unknowns: list[str] = []
    passes = 0
    scorable = 0

    have_types = vault_doc_types(documents)

    # ── 1. Contractor class ──────────────────────────────────────────────────
    req_cls = _safe_str(tender.get("contractor_class"))
    if req_cls and _class_rank(req_cls) > 0:
        scorable += 1
        my_cls = _safe_str(profile.get("contractor_class"))
        if not my_cls:
            unknowns.append("Contractor class not set in your profile.")
            checks.append({"label": "Contractor class", "ok": None,
                           "detail": f"Tender needs {req_cls}; your class is not set."})
        elif _class_rank(my_cls) >= _class_rank(req_cls):
            passes += 1
            checks.append({"label": "Contractor class", "ok": True,
                           "detail": f"You hold {my_cls} (needs {req_cls})."})
        else:
            blockers.append(f"Contractor class too low: you are {my_cls}, tender needs {req_cls}.")
            checks.append({"label": "Contractor class", "ok": False,
                           "detail": f"You hold {my_cls}; tender needs {req_cls}."})

    # ── 2. Annual turnover ───────────────────────────────────────────────────
    req_to = _required_turnover(tender)
    if req_to > 0:
        scorable += 1
        my_to = _safe_float(profile.get("turnover_lakhs"))
        if my_to <= 0:
            unknowns.append("Annual turnover not set in your profile.")
            checks.append({"label": "Annual turnover", "ok": None,
                           "detail": f"Tender needs ~Rs {req_to:.0f}L; your turnover is not set."})
        elif my_to >= req_to:
            passes += 1
            checks.append({"label": "Annual turnover", "ok": True,
                           "detail": f"Rs {my_to:.0f}L meets ~Rs {req_to:.0f}L."})
        else:
            blockers.append(f"Turnover short: you have Rs {my_to:.0f}L, tender needs ~Rs {req_to:.0f}L.")
            checks.append({"label": "Annual turnover", "ok": False,
                           "detail": f"Rs {my_to:.0f}L is below ~Rs {req_to:.0f}L."})

    # ── 3. Experience / years in business ────────────────────────────────────
    req_exp = _safe_int(tender.get("required_experience_years"))
    if req_exp > 0:
        scorable += 1
        my_exp = _years_in_business(profile)
        if my_exp <= 0:
            unknowns.append("Experience / registration year not set in your profile.")
            checks.append({"label": "Experience", "ok": None,
                           "detail": f"Tender needs {req_exp}+ yrs; your experience is not set."})
        elif my_exp >= req_exp:
            passes += 1
            checks.append({"label": "Experience", "ok": True,
                           "detail": f"{my_exp} yrs meets {req_exp}+ yrs."})
        else:
            blockers.append(f"Experience short: {my_exp} yrs vs {req_exp}+ yrs required.")
            checks.append({"label": "Experience", "ok": False,
                           "detail": f"{my_exp} yrs is below {req_exp}+ yrs."})

    # ── 4. Required documents vs vault registry ──────────────────────────────
    missing_docs: list[str] = []
    for raw in (tender.get("required_documents") or []):
        label = _safe_str(raw)
        if not label:
            continue
        # Match the tender's free-text requirement to a canonical type, then
        # check the vault registry for that type (metadata-only, OCR-proof).
        matched_type = None
        low = label.lower()
        for canonical, kws in _DOC_SIGNATURES.items():
            if any(kw in low for kw in kws):
                matched_type = canonical
                break
        if matched_type and matched_type in have_types:
            continue
        if matched_type:
            missing_docs.append(matched_type)
        # Unrecognised doc types are NOT treated as blockers (avoid false negatives).
    missing_docs = sorted(set(missing_docs))

    # ── Decision ─────────────────────────────────────────────────────────────
    score = round(100 * passes / scorable) if scorable else 0

    if blockers:
        verdict = NOT_ELIGIBLE
        summary = blockers[0]
    elif scorable == 0 and not have_types:
        # Nothing concrete to test against — be honest, ask for profile/docs.
        verdict = NEEDS_REVIEW
        summary = "Add your class, turnover & experience (or vault docs) to verify eligibility."
    elif unknowns:
        verdict = NEEDS_REVIEW
        summary = "Eligible on what we can check — " + unknowns[0].lower()
    else:
        verdict = ELIGIBLE
        summary = "You meet the tender's published eligibility criteria."

    return {
        "verdict": verdict,
        "checks": checks,
        "blockers": blockers,
        "unknowns": unknowns,
        "have_docs": sorted(have_types),
        "missing_docs": missing_docs,
        "score": score,
        "summary": summary,
    }
