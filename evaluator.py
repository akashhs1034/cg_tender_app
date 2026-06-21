"""
evaluator.py — the AI document evaluator.

Given a tender (or job) and the contractor's own documents, it answers the
question that actually wastes their time: "do I qualify, and what am I missing?"

Handles raw text fallbacks and native Claude 3.5 Sonnet Vision/Document binaries.
"""

from __future__ import annotations

import os
import re
import json
import base64
import core

# Latest Gemini Flash. "gemini-flash-latest" auto-tracks the newest flash model
# and works with the AQ. key format; gemini-2.0-flash is quota-limited (429).
GEMINI_MODEL = "gemini-flash-latest"

# ---------------------------------------------------------------------------
# Core LLM extraction — tries Gemini first, falls back to Claude
# ---------------------------------------------------------------------------
def _llm_extract(prompt: str, document_bytes: bytes = None, mime_type: str = "application/pdf") -> dict | None:
    """Call Gemini (preferred) or Claude to return structured JSON."""
    full_prompt = prompt + "\n\nRespond strictly with valid raw JSON only. Do not wrap in markdown code blocks or fences."

    gemini_key    = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_key and not anthropic_key:
        core.record_ai_error("no api key configured")
        return None

    # ---- Gemini path (direct REST + X-goog-api-key header) ----
    # We call the REST endpoint directly instead of the google-genai SDK: the
    # SDK mishandles the newer "AQ." API-key format (sends it as an OAuth token
    # -> 401). The header method below matches a working curl exactly.
    if gemini_key:
        try:
            import requests
            parts: list = []
            if document_bytes:
                actual_mime = mime_type if ("pdf" in mime_type or "image" in mime_type) else "application/pdf"
                parts.append({"inline_data": {
                    "mime_type": actual_mime,
                    "data": base64.b64encode(document_bytes).decode(),
                }})
            parts.append({"text": full_prompt})

            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                headers={"Content-Type": "application/json", "X-goog-api-key": gemini_key},
                json={"contents": [{"parts": parts}]}, timeout=90,
            )
            resp.raise_for_status()
            _parts = resp.json()["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in _parts).strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(text)
            core.clear_ai_error()
            return result
        except Exception as e:
            print(f"[AI Evaluator] Gemini error: {e}")
            core.record_ai_error(e)
            if not anthropic_key:
                return None

    # ---- Claude fallback ----
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            content_block: list = []

            if document_bytes:
                encoded_doc = base64.b64encode(document_bytes).decode("utf-8")
                if "pdf" in mime_type.lower():
                    content_block.append({
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": encoded_doc}
                    })
                elif "image" in mime_type.lower() or any(ext in mime_type.lower() for ext in ["png", "jpeg", "jpg"]):
                    actual_mime = "image/jpeg" if "jpg" in mime_type.lower() or "jpeg" in mime_type.lower() else "image/png"
                    content_block.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": actual_mime, "data": encoded_doc}
                    })

            content_block.append({"type": "text", "text": full_prompt})
            msg = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=2048,
                messages=[{"role": "user", "content": content_block}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(text)
            core.clear_ai_error()
            return result
        except Exception as e:
            print(f"[AI Evaluator] Claude error: {e}")
            core.record_ai_error(e)
            return None

    return None

# ---------------------------------------------------------------------------
# HIGH PRIORITY sector detection
# ---------------------------------------------------------------------------
_PRIORITY_KW = [
    "coal", "coal transportation", "loading", "unloading", "railway siding",
    "dumper hiring", "truck hiring", "vehicle hiring", "manpower supply",
    "security services", "housekeeping", "mining", "freight movement",
    "material transportation", "logistics", "warehousing", "transport",
    "industrial transportation", "road construction",
]

def is_high_priority(tender: dict) -> bool:
    text = (f"{tender.get('title','')} {tender.get('category','')} "
            f"{tender.get('description','')} {tender.get('organization','')}").lower()
    return any(kw in text for kw in _PRIORITY_KW)


# ---------------------------------------------------------------------------
# 6-Dimension Opportunity Scoring
# ---------------------------------------------------------------------------
_HIGH_RELIABILITY_ORGS = [
    "secl", "cil", "coal india", "ntpc", "bhel", "bpcl", "hpcl", "ongc",
    "nhpc", "nhai", "ircon", "rites", "central", "cpwd", "national",
]
_MED_RELIABILITY_ORGS = [
    "state", "pwd", "phed", "phd", "cspdcl", "uppcl", "jal", "nagar",
    "municipal", "district", "collector",
]

_NICHE_CATS = ["Coal & Mining", "Transport", "Manpower Supply", "Warehousing"]
_COMMODITY_CATS = ["Civil Infrastructure", "Electrical & Energy", "Water & Irrigation"]


def score_opportunity(tender: dict, profile: dict) -> dict:
    """
    Return 6 scores (0-100) + reasoning for each dimension.
    lead, profit, qualification, competition, payment, strategic
    """
    title    = _s(tender.get("title"))
    org      = _s(tender.get("organization")).lower()
    cat      = _s(tender.get("category"))
    val      = _sf(tender.get("value_lakhs"))
    emd_raw  = _s(tender.get("emd"))
    turnover = _sf(profile.get("turnover_lakhs"))
    exp_yrs  = _si(profile.get("experience_years"))
    t_text   = f"{title} {cat} {_s(tender.get('description'))}".lower()
    high_pri = is_high_priority(tender)

    # ── Lead Score ────────────────────────────────────────────────────────
    lead = 50
    lead_r = []
    if high_pri:
        lead += 20; lead_r.append("Matches your priority sectors (coal/transport/logistics)")
    if val > 0:
        if val <= turnover * 0.3:
            lead += 15; lead_r.append("Contract size fits your capacity")
        elif val <= turnover:
            lead += 8; lead_r.append("Contract is sizeable but reachable")
        elif val > turnover * 2:
            lead -= 15; lead_r.append("Contract likely exceeds your capacity")
    emd_pct = 0.0
    try:
        emd_num = core.parse_value_to_lakhs(emd_raw)
        if emd_num and val:
            emd_pct = (emd_num / val) * 100
            if emd_pct <= 2:
                lead += 8; lead_r.append("Low EMD relative to contract value")
            elif emd_pct > 5:
                lead -= 8; lead_r.append("High EMD requirement")
    except Exception:
        pass
    if not tender.get("contractor_class"):
        lead += 5; lead_r.append("No contractor class restriction stated")
    lead = max(0, min(100, lead))

    # ── Profitability Score ───────────────────────────────────────────────
    profit = 45
    profit_r = []
    if cat in _NICHE_CATS:
        profit += 20; profit_r.append(f"{cat} typically carries strong margins")
    if "coal" in t_text or "mining" in t_text:
        profit += 12; profit_r.append("Coal/mining contracts often carry 15–25% margins")
    if "transport" in t_text or "vehicle" in t_text:
        profit += 8; profit_r.append("Transport/hiring contracts: low overhead, fast cash")
    if val and val >= 50:
        profit += 10; profit_r.append("Contract value justifies mobilisation cost")
    elif val and val < 5:
        profit -= 10; profit_r.append("Small contract — margin may be tight")
    if "annual" in t_text or "year" in t_text:
        profit += 8; profit_r.append("Recurring/annual contract = predictable revenue")
    profit = max(0, min(100, profit))

    # ── Qualification Probability ─────────────────────────────────────────
    qual = 60
    qual_r = []
    req_rank = core._rank(tender.get("contractor_class"))
    if req_rank == 0:
        qual += 15; qual_r.append("No contractor class requirement")
    elif core._rank(profile.get("contractor_class")) >= req_rank:
        qual += 12; qual_r.append(f"You meet class requirement ({tender.get('contractor_class')})")
    else:
        qual -= 25; qual_r.append(f"Class mismatch — needs {tender.get('contractor_class')}")
    req_exp = core._exp_years(tender.get("experience"))
    if req_exp == 0:
        qual += 8; qual_r.append("No experience barrier")
    elif exp_yrs >= req_exp:
        qual += 10; qual_r.append(f"Your {exp_yrs}yr experience meets {req_exp}yr requirement")
    else:
        qual -= 15; qual_r.append(f"Experience gap: need {req_exp}yr, have {exp_yrs}yr")
    if val and turnover and val <= turnover * 2.5:
        qual += 8; qual_r.append("Turnover likely sufficient for EMD eligibility")
    qual = max(0, min(100, qual))

    # ── Competition Risk (higher = more competitors = harder to win) ──────
    comp = 50
    comp_r = []
    if cat in _NICHE_CATS:
        comp -= 20; comp_r.append(f"Niche category ({cat}) = fewer qualified bidders")
    if cat in _COMMODITY_CATS:
        comp += 15; comp_r.append(f"{cat} attracts many bidders")
    if val and val > 500:
        comp += 15; comp_r.append("High-value contracts attract large firms")
    elif val and val < 20:
        comp -= 8; comp_r.append("Small contract — less attractive to large players")
    if "secl" in org or "coal india" in org or "cil" in org:
        comp -= 10; comp_r.append("SECL/CIL contracts favour experienced mining contractors")
    comp = max(0, min(100, comp))

    # ── Payment Reliability ───────────────────────────────────────────────
    pay = 55
    pay_r = []
    if any(x in org for x in _HIGH_RELIABILITY_ORGS):
        pay = 85; pay_r.append("Central PSU / national body — strong payment track record")
    elif any(x in org for x in _MED_RELIABILITY_ORGS):
        pay = 65; pay_r.append("State department — generally reliable, sometimes delayed")
    else:
        pay = 55; pay_r.append("Check department's payment history before bidding")
    if "secl" in org or "cil" in org:
        pay = 90; pay_r.append("Coal India subsidiaries are known for timely payments")
    pay = max(0, min(100, pay))

    # ── Strategic Value ───────────────────────────────────────────────────
    strat = 50
    strat_r = []
    if high_pri:
        strat += 20; strat_r.append("Aligns with your core business sectors")
    if "secl" in org or "cil" in org:
        strat += 20; strat_r.append("SECL/CIL vendor empanelment opens repeat business pipeline")
    if "annual" in t_text or "year" in t_text or "rate" in t_text:
        strat += 10; strat_r.append("Rate contract / annual order = recurring revenue")
    if val and val >= 100:
        strat += 8; strat_r.append("Large contract builds portfolio credentials")
    strat = max(0, min(100, strat))

    return {
        "lead":          (lead,   lead_r),
        "profit":        (profit, profit_r),
        "qualification": (qual,   qual_r),
        "competition":   (comp,   comp_r),
        "payment":       (pay,    pay_r),
        "strategic":     (strat,  strat_r),
    }


# ---------------------------------------------------------------------------
# Profitability Analysis
# ---------------------------------------------------------------------------
def profitability_analysis(tender: dict, profile: dict) -> dict:
    """Estimate revenue, cost, margin, working capital for this tender."""
    val = _sf(tender.get("value_lakhs"))
    cat = _s(tender.get("category"))
    t_text = (f"{tender.get('title','')} {tender.get('description','')}").lower()

    # Gross margin % by sector (realistic for Indian Govt contracts)
    margin_pct = {
        "Coal & Mining": 20,
        "Transport": 18,
        "Manpower Supply": 15,
        "Warehousing": 17,
        "Civil Infrastructure": 12,
        "Electrical & Energy": 13,
        "Water & Irrigation": 12,
        "Municipal Projects": 10,
        "IT Services": 25,
        "Government Supply": 12,
    }.get(cat, 12)

    if "coal" in t_text:        margin_pct = max(margin_pct, 20)
    if "transport" in t_text:   margin_pct = max(margin_pct, 17)
    if "manpower" in t_text:    margin_pct = max(margin_pct, 14)

    rev        = val if val else 0
    op_cost    = round(rev * (1 - margin_pct / 100), 1)
    gross_margin = round(rev - op_cost, 1)

    # Working capital: typically need 15–20% of contract value
    wc_pct     = 0.15 if margin_pct >= 15 else 0.20
    working_cap = round(rev * wc_pct, 1)

    # Cash flow risk
    if rev == 0:
        cf_risk = "Unknown"
    elif rev < 10:
        cf_risk = "Low — small contract, quick recovery"
    elif rev < 50:
        cf_risk = "Medium — mobilisation + 30–60 day payment cycle"
    elif rev >= 50:
        cf_risk = "Moderate — plan for retention money and running bill gaps"

    if gross_margin > 30:
        rating = "High Profit Potential"
        color  = "#10B981"
    elif gross_margin > 10:
        rating = "Medium Profit Potential"
        color  = "#F59E0B"
    else:
        rating = "Low Profit Potential"
        color  = "#F87171"

    return {
        "revenue":       rev,
        "op_cost":       op_cost,
        "gross_margin":  gross_margin,
        "margin_pct":    margin_pct,
        "working_cap":   working_cap,
        "cf_risk":       cf_risk,
        "rating":        rating,
        "color":         color,
    }


# ---------------------------------------------------------------------------
# Full Government Document Submission Checklist
# ---------------------------------------------------------------------------
_ALWAYS_REQUIRED = [
    ("GST Registration Certificate",        ["gst"]),
    ("PAN Card",                            ["pan"]),
    ("Digital Signature Certificate (DSC)", ["dsc", "digital signature"]),
    ("Contractor / Firm Registration",      ["registration", "license", "empanel", "firm"]),
    ("Turnover Certificates (Last 3 Yrs)",  ["turnover", "financial", "balance sheet", "audited"]),
    ("Bank Solvency Certificate",           ["solvency", "bank certificate"]),
    ("EMD / Bid Security",                  ["emd", "earnest money", "bid security"]),
]

_CONDITIONAL_DOCS = [
    ("MSME / Udyam Registration",           ["msme", "udyam", "small enterprise"]),
    ("Experience / Work Completion Certs",  ["experience", "completion certificate", "similar work"]),
    ("EPF Registration",                    ["epf", "provident fund", "pf "]),
    ("ESIC Registration",                   ["esic", "esi ", "employee state"]),
    ("Labour License",                      ["labour license", "labour licence", "contract labour"]),
    ("Balance Sheets (3 years)",            ["balance sheet", "audited accounts"]),
    ("Tender Document Fees / DD",           ["tender fee", "document fee", "demand draft", "dd "]),
    ("Affidavit (non-blacklisted)",         ["blacklist", "affidavit"]),
]


def submission_checklist(tender: dict, doc_text: str = "") -> dict:
    """
    Return always-required and conditional documents with present/unknown status.
    doc_text: text from uploaded documents (for verification).
    """
    low = doc_text.lower() if doc_text else ""
    t_text = (f"{tender.get('requirements','')} {tender.get('description','')} "
              f"{tender.get('eligibility','')}").lower()

    always = []
    for label, kws in _ALWAYS_REQUIRED:
        found = any(kw in low for kw in kws) if low else None
        always.append({"label": label, "status": "present" if found else ("unknown" if not low else "missing")})

    conditional = []
    for label, kws in _CONDITIONAL_DOCS:
        required_in_tender = any(kw in t_text for kw in kws)
        found_in_docs      = any(kw in low for kw in kws) if low else None
        if required_in_tender:
            conditional.append({
                "label": label,
                "status": "present" if found_in_docs else ("unknown" if not low else "missing"),
                "required": True,
            })
        else:
            conditional.append({"label": label, "status": "check", "required": False})

    steps = [
        "1. Download & read the official NIT / tender document completely",
        "2. Check eligibility: contractor class, turnover, experience requirements",
        "3. Pay tender document fee (if any) via DD or online payment",
        "4. Prepare all required documents — scan as PDFs",
        "5. Pay EMD via RTGS / NEFT / demand draft (as specified)",
        "6. Get your DSC (Class 3) ready for digital signing",
        "7. Register / login on the tender portal",
        "8. Fill technical bid form completely — attach all documents",
        "9. Fill financial bid / BOQ — price each line item carefully",
        "10. Submit before deadline — download acknowledgement receipt",
    ]

    return {"always": always, "conditional": conditional, "steps": steps}


# ---------------------------------------------------------------------------
# Deterministic Regex Fallbacks & Configuration Maps
# ---------------------------------------------------------------------------
_DOC_KEYWORDS = {
    "GST registration": ["gst"],
    "ISO certification": ["iso "],
    "Contractor registration / license": ["registration", "license", "licence", "empanel"],
    "EMD / bank guarantee": ["emd", "bank guarantee", "earnest money"],
    "Turnover / financial proof": ["turnover", "financial", "balance sheet", "audited"],
    "Experience / completion certificate": ["experience", "completion certificate", "similar work"],
    "PAN card": ["pan "],
    "Safety / DGMS pass": ["dgms", "safety pass"],
    "Drug / equipment license": ["drug license", "wholesale license", "13485"],
}

_DEGREE_PATTERNS = [
    ("B.Tech / B.E. (Engineering)", ["b.tech", "b.e.", "btech", "bachelor of engineering", "be (", "b.e in", "b.tech in"]),
    ("MBA / PGDM",    ["mba", "pgdm", "master of business", "bba", "bachelor of business"]),
    ("MCA",           ["mca", "master of computer"]),
    ("M.Tech / M.E.", ["m.tech", "m.e.", "mtech", "master of engineering"]),
    ("B.Ed (Teacher Training)", ["b.ed", "bed ", "bachelor of education"]),
    ("MBBS / Medical Degree",   ["mbbs", "md ", "ms (medicine)", "bachelor of medicine"]),
    ("GNM / B.Sc Nursing",      ["gnm", "b.sc nursing", "bsc nursing", "general nursing"]),
    ("12th / Intermediate",     ["12th", "intermediate", "higher secondary", "hsc", "+2", "class xii"]),
    ("Diploma",                 ["diploma"]),
    # Keep this last — broad keywords must not override specific patterns above
    ("B.Sc / B.A. / B.Com (Graduate)", ["b.sc", "b.a.", "b.com", "bsc", "b.com", "graduate", "graduation", "bachelor of arts", "bachelor of science", "bachelor of commerce"]),
]

_SKILL_CAT_MAP = {
    "Engineering":    ["autocad", "civil", "structural", "electrical", "mechanical", "revit", "staad"],
    "IT Services":    ["python", "java", "sql", "linux", "cloud", "networking", "software", "programming"],
    "Education":      ["teaching", "pedagogy", "curriculum", "classroom", "tet", "ctet"],
    "Administration": ["ms office", "excel", "word", "tally", "documentation", "compliance"],
    "Police":         ["law", "legal", "driving", "physical"],
    "Health":         ["patient care", "clinical", "pharmacy", "nursing", "lab", "diagnostics"],
}

_CERT_KEYWORDS = ["ccna", "ccnp", "pmp", "itil", "cfa", " ca ", "iso", "gnm", "b.ed", "ctet", "tet", "gate"]

def _turnover_from_text(text: str) -> float | None:
    m = re.search(r"turnover[^.]{0,60}?(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|l)\b", text, re.I)
    return core.parse_value_to_lakhs(f"{m.group(1)} {m.group(2)}") if m else None

def _years_from_text(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(?:\+)?\s*year", text, re.I)
    return int(m.group(1)) if m else None

# ---------------------------------------------------------------------------
# Requirements Discovery Match Pipelines
# ---------------------------------------------------------------------------
def tender_requirements(tender: dict) -> list[dict]:
    reqs = []
    text = " ".join(str(tender.get(k, "")) for k in ("requirements", "description", "eligibility"))

    if tender.get("contractor_class") and core._rank(tender["contractor_class"]) > 0:
        reqs.append({"key": "class", "kind": "class",
                     "label": f"Contractor class {tender['contractor_class']} or higher",
                     "target": core._rank(tender["contractor_class"]), "mandatory": True})

    turnover = _turnover_from_text(text)
    if turnover is None and tender.get("value_lakhs"):
        try:
            turnover = round(float(tender["value_lakhs"]) * 0.3, 1)
            reqs.append({"key": "turnover", "kind": "turnover",
                         "label": f"Approx. ₹{turnover}L annual turnover (estimated)",
                         "target": turnover, "mandatory": True, "estimated": True})
        except (TypeError, ValueError):
            pass
    elif turnover is not None:
        reqs.append({"key": "turnover", "kind": "turnover",
                     "label": f"₹{turnover}L annual turnover", "target": turnover, "mandatory": True})

    yrs = core._exp_years(tender.get("experience")) or _years_from_text(text)
    if yrs:
        reqs.append({"key": "experience", "kind": "experience",
                     "label": f"~{yrs}+ years relevant experience", "target": yrs, "mandatory": True})

    low = text.lower()
    for label, kws in _DOC_KEYWORDS.items():
        if any(kw in low for kw in kws):
            reqs.append({"key": label, "kind": "document", "label": label, "target": kws, "mandatory": True})
    return reqs

def job_requirements(job: dict) -> list[dict]:
    reqs = []
    qual = _s(job.get("qualification")) or _s(job.get("description"))
    low = qual.lower()
    degree_map = {
        "Graduate / Bachelor's degree": ["graduate", "bachelor", "b.e", "b.tech", "b.sc", "bca", "degree"],
        "Postgraduate / MCA / M.Tech": ["mca", "m.tech", "post graduate", "masters", "pg "],
        "12th pass": ["12th", "intermediate", "higher secondary"],
        "Diploma": ["diploma"],
        "Professional certification": ["ccna", "ccnp", "gnm", "nursing council", "registration"],
    }
    for label, kws in degree_map.items():
        if any(kw in low for kw in kws):
            reqs.append({"key": label, "kind": "document", "label": label, "target": kws, "mandatory": True})
    yrs = _years_from_text(qual)
    if yrs:
        reqs.append({"key": "experience", "kind": "experience",
                     "label": f"~{yrs}+ years experience", "target": yrs, "mandatory": True})
    if not reqs:
        reqs.append({"key": "Eligibility document", "kind": "document",
                     "label": "Qualification proof (see official notification)", "target": [], "mandatory": True})
    return reqs

def user_facts(profile: dict, doc_text: str = "") -> dict:
    low = (doc_text or "").lower()
    facts = {
        "class_rank":       core._rank(profile.get("contractor_class")),
        "turnover_lakhs":   _sf(profile.get("turnover_lakhs")),
        "experience_years": _si(profile.get("experience_years")),
        "doc_text":         low,
    }
    for label in ("a", "b", "c", "d"):
        if f"class {label}" in low:
            facts["class_rank"] = max(facts["class_rank"], core._rank(f"class {label}"))
    t = _turnover_from_text(low)
    if t:
        facts["turnover_lakhs"] = max(facts["turnover_lakhs"], t)
    return facts

# ---------------------------------------------------------------------------
# Universal Evaluation Execution Handlers
# ---------------------------------------------------------------------------
def evaluate(requirements: list[dict], facts: dict) -> dict:
    met, missing, unknown = [], [], []
    for req in requirements:
        kind = req["kind"]
        if kind == "class":
            (met if facts["class_rank"] >= req["target"] else missing).append(req["label"])
        elif kind == "turnover":
            if facts["turnover_lakhs"] <= 0:
                unknown.append(req["label"])
            else:
                (met if facts["turnover_lakhs"] >= req["target"] else missing).append(req["label"])
        elif kind == "experience":
            (met if facts["experience_years"] >= req["target"] else missing).append(req["label"])
        elif kind == "document":
            kws = req.get("target") or []
            found = any(kw.strip() in facts["doc_text"] for kw in kws) if kws else False
            if found:
                met.append(req["label"])
            elif facts["doc_text"]:
                missing.append(req["label"])
            else:
                unknown.append(req["label"])

    total = len(met) + len(missing) + len(unknown)
    readiness = round(100 * len(met) / total) if total else 0

    if not missing and not unknown:
        verdict = "You appear to meet all stated requirements. Verify against the official document before bidding."
    elif missing:
        verdict = f"You're missing {len(missing)} mandatory item(s). Address these before you bid."
    else:
        verdict = "Upload your documents to confirm the unverified items."

    return {"readiness_pct": readiness, "met": met, "missing": missing,
            "unknown": unknown, "verdict": verdict}

def evaluate_tender(tender: dict, profile: dict, doc_text: str = "") -> dict:
    return evaluate(tender_requirements(_clean(tender)), user_facts(profile, doc_text))

def evaluate_job(job: dict, profile: dict, doc_text: str = "") -> dict:
    return evaluate(job_requirements(_clean(job)), user_facts(profile, doc_text))

# ---------------------------------------------------------------------------
# Resume Matching Pipeline (Fixed KeyError Alignment)
# ---------------------------------------------------------------------------
def _s(val) -> str:
    """Safely convert any value (including pandas NaN / numpy floats) to str."""
    if val is None:
        return ""
    try:
        # val != val is True only for NaN (works for float, numpy.float64, etc.)
        if val != val:
            return ""
    except Exception:
        pass
    s = str(val).strip()
    return "" if s.lower() in ("nan", "none", "nat", "") else s

def _sf(val, default: float = 0.0) -> float:
    """Safe float — returns default for None/NaN/invalid."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if f != f else f   # f != f is True only for NaN
    except (TypeError, ValueError):
        return default

def _si(val, default: int = 0) -> int:
    """Safe int — returns default for None/NaN/invalid."""
    return int(_sf(val, default))

def _clean(d: dict) -> dict:
    """Replace every NaN/float/None in a pandas-derived dict with a safe string."""
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = ""
        else:
            try:
                if v != v:      # NaN check — works for float, numpy.float64, etc.
                    out[k] = ""
                    continue
            except Exception:
                pass
            out[k] = str(v) if not isinstance(v, (str, int, list, dict)) else v
    return out

def _resume_reqs(job: dict) -> list[dict]:
    reqs = []
    title_low = (_s(job.get("title")) + " " + _s(job.get("department"))).lower()
    qual_low  = _s(job.get("qualification")).lower()
    cat       = _s(job.get("category")) or "General"

    degree_added = False
    if qual_low:
        for label, kws in _DEGREE_PATTERNS:
            if any(kw in qual_low for kw in kws):
                reqs.append({"label": label, "kind": "degree", "target": kws})
                degree_added = True
                break

    if not degree_added:
        if cat == "Engineering" or any(k in title_low for k in ["engineer", "technical", "jto"]):
            reqs.append({"label": "B.Tech / B.E. in Engineering", "kind": "degree", "target": ["b.tech", "b.e.", "btech", "engineering"]})
        elif cat == "Education" or any(k in title_low for k in ["teacher", "lecturer", "professor", "college"]):
            reqs.append({"label": "Graduate degree (B.A./B.Sc./B.Tech) + B.Ed preferred", "kind": "degree", "target": ["bachelor", "graduate", "b.a.", "b.sc", "b.ed", "graduation", "b.tech", "btech", "b.com", "bca"]})
        elif cat == "Health" or any(k in title_low for k in ["nurse", "medical", "doctor", "health"]):
            reqs.append({"label": "Medical / nursing qualification (MBBS / GNM / B.Sc Nursing)", "kind": "degree", "target": ["mbbs", "gnm", "nursing", "b.sc nursing", "bsc nursing"]})
        else:
            reqs.append({"label": "Graduate degree (any discipline)", "kind": "degree", "target": ["bachelor", "graduate", "b.a.", "b.sc", "b.tech", "graduation", "degree"]})

    yrs = _years_from_text(qual_low)
    if yrs:
        reqs.append({"label": f"{yrs}+ years relevant experience", "kind": "experience", "target": yrs})
    if job.get("state") in ("Uttar Pradesh", "Chhattisgarh"):
        reqs.append({"label": "Hindi language proficiency", "kind": "language", "target": ["hindi"]})

    cat_skills = _SKILL_CAT_MAP.get(cat, [])
    if cat_skills:
        reqs.append({"label": f"Domain skills: {', '.join(cat_skills[:4])}", "kind": "skills", "target": cat_skills})

    return reqs

def _resume_facts(resume_text: str) -> dict:
    low = resume_text.lower()
    degrees = []
    for label, kws in _DEGREE_PATTERNS:
        if any(kw in low for kw in kws):
            degrees.append(label)

    exp_matches = re.findall(r"(\d+)\s*\+?\s*years?\s*(?:of\s+)?(experience|exp\.?|work)", low)
    exp_years = max((int(x[0]) for x in exp_matches), default=0)
    all_skills = [kw for kws in _SKILL_CAT_MAP.values() for kw in kws]
    skills = [s for s in all_skills if s in low]
    certifications = [c for c in _CERT_KEYWORDS if c in low]
    languages = [lang for lang in ["hindi", "english", "urdu", "punjabi", "marathi"] if lang in low]

    return {
        "degrees": degrees, "experience_years": exp_years, "skills": skills,
        "certifications": certifications, "languages": languages, "raw": low,
    }

def _keyword_resume_eval(job: dict, resume_text: str) -> dict:
    reqs  = _resume_reqs(job)
    facts = _resume_facts(resume_text)
    met, missing, unknown = [], [], []
    domain_skills_missing = False

    for req in reqs:
        kind, target = req["kind"], req.get("target")
        label = req["label"]

        if not facts["raw"]:
            unknown.append(label)
            continue

        if kind == "degree":
            # Match against extracted degree labels, not raw text, to avoid
            # false positives like MBA matching "bachelor" for a nursing job.
            candidate_degree_text = " ".join(facts["degrees"]).lower()
            found = any(kw in candidate_degree_text for kw in (target or []))
            (met if found else missing).append(label)
        elif kind == "experience":
            (met if facts["experience_years"] >= target else missing).append(label)
        elif kind == "language":
            found = any(lang in facts["languages"] for lang in (target or []))
            (met if found else missing).append(label)
        elif kind == "skills":
            found_skills = [s for s in (target or []) if s in facts["raw"]]
            if found_skills:
                met.append(f"{label} (found: {', '.join(found_skills[:3])})")
            else:
                missing.append(label)
                domain_skills_missing = True  # critical gap — core competency absent

    total = len(met) + len(missing) + len(unknown)
    match_pct = round(100 * len(met) / total) if total else 0

    # Domain skills represent the job's core competency. Missing them is a hard
    # disqualifier regardless of how many other boxes are ticked — cap at 35%.
    if domain_skills_missing:
        match_pct = min(match_pct, 35)

    cat = _s(job.get("category")) or "this field"
    if not missing and not unknown:
        verdict = "Your resume appears to satisfy all stated requirements."
    elif len(met) == 0:
        verdict = "Your resume does not appear to match the requirements for this role."
    elif domain_skills_missing:
        verdict = (
            f"Your background may meet some basic criteria, but the core {cat} "
            f"domain skills are not found in your resume — this is a critical gap "
            f"that would likely disqualify the application."
        )
    elif not missing:
        verdict = "Some requirements couldn't be verified from the resume text."
    else:
        verdict = f"Partial match — {len(met)} of {total} requirements found in your resume."

    return {"readiness_pct": match_pct, "met": met, "missing": missing, "unknown": unknown, "verdict": verdict}

def _llm_resume_eval(job: dict, resume_text: str) -> dict | None:
    qual = _s(job.get("qualification")) or "Not specified — infer from job title and category"
    prompt = f"""You are an HR screening assistant. Evaluate a candidate's resume against a government job posting.

JOB DETAILS:
Title: {job.get('title', '')}
Department: {job.get('department', '')}
State: {job.get('state', '')}
Category: {job.get('category', '')}
Qualification required: {qual}
Description: {job.get('description', '')}

CANDIDATE RESUME:
{resume_text[:4000]}

Return ONLY valid JSON:
{{
  "requirements": [
    {{"label": "B.Tech/B.E. in Civil Engineering", "status": "met"}},
    {{"label": "3+ years site experience", "status": "missing"}}
  ],
  "match_pct": 60,
  "verdict": "The candidate holds the required degree but lacks the stated field experience."
}}"""

    data = _llm_extract(prompt)
    if not data or "requirements" not in data:
        return None

    met     = [r["label"] for r in data["requirements"] if r.get("status") == "met"]
    missing = [r["label"] for r in data["requirements"] if r.get("status") == "missing"]
    unknown = [r["label"] for r in data["requirements"] if r.get("status") == "unknown"]

    # Map internal match_pct to external readiness_pct to prevent app.py KeyError crash
    return {
        "readiness_pct": max(0, min(100, int(data.get("match_pct", 0)))),
        "met": met, "missing": missing, "unknown": unknown,
        "verdict": str(data.get("verdict", "")),
    }

def evaluate_resume_for_job(job: dict, resume_text: str) -> dict:
    job = _clean(job)               # sanitize all NaN / float values first
    resume_text = resume_text or ""
    if os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        result = _llm_resume_eval(job, resume_text)
        if result is not None:
            return result
    return _keyword_resume_eval(job, resume_text)