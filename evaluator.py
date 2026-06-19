"""
evaluator.py — the AI document evaluator.

Given a tender (or job) and the contractor's own documents, it answers the
question that actually wastes their time: "do I qualify, and what am I missing?"

It returns a READINESS / ELIGIBILITY percentage — the share of mandatory
requirements the user's documents satisfy. It deliberately does NOT invent a
"win probability": that needs competitor/price/results data you don't have yet,
and a wrong number costs a contractor real money (EMD, missed bids).

Two modes:
  * If ANTHROPIC_API_KEY is set -> uses Claude to extract structured
    requirements/facts from messy document text (the real-AI path).
  * Otherwise -> a deterministic keyword/regex extractor so the feature works
    today with no key and no cost.
"""

from __future__ import annotations

import os
import re
import json

import core


# ---------------------------------------------------------------------------
# Optional LLM extraction (real-AI upgrade path)
# ---------------------------------------------------------------------------
def _llm_extract(prompt: str) -> dict | None:
    """Call Claude to return structured JSON. Returns None if no key/SDK."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(text)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------
# Credentials/documents commonly demanded in CG/UP tenders.
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


def _turnover_from_text(text: str) -> float | None:
    """Find an explicit turnover figure in requirement text, in lakhs."""
    m = re.search(r"turnover[^.]{0,60}?(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|l)\b",
                  text, re.I)
    if m:
        return core.parse_value_to_lakhs(f"{m.group(1)} {m.group(2)}")
    return None


def _years_from_text(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(?:\+)?\s*year", text, re.I)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Build the requirement list for a tender / job
# ---------------------------------------------------------------------------
def tender_requirements(tender: dict) -> list[dict]:
    """Each requirement: {key, label, kind, target, mandatory}."""
    reqs = []
    text = " ".join(str(tender.get(k, "")) for k in ("requirements", "description", "eligibility"))

    if tender.get("contractor_class") and core._rank(tender["contractor_class"]) > 0:
        reqs.append({"key": "class", "kind": "class",
                     "label": f"Contractor class {tender['contractor_class']} or higher",
                     "target": core._rank(tender["contractor_class"]), "mandatory": True})

    turnover = _turnover_from_text(text)
    if turnover is None and tender.get("value_lakhs"):
        try:
            turnover = round(float(tender["value_lakhs"]) * 0.3, 1)  # common ~30% rule
            reqs.append({"key": "turnover", "kind": "turnover",
                         "label": f"Approx. ₹{turnover}L annual turnover (estimated)",
                         "target": turnover, "mandatory": True, "estimated": True})
        except (TypeError, ValueError):
            pass
    elif turnover is not None:
        reqs.append({"key": "turnover", "kind": "turnover",
                     "label": f"₹{turnover}L annual turnover", "target": turnover,
                     "mandatory": True})

    yrs = core._exp_years(tender.get("experience")) or _years_from_text(text)
    if yrs:
        reqs.append({"key": "experience", "kind": "experience",
                     "label": f"~{yrs}+ years relevant experience", "target": yrs,
                     "mandatory": True})

    low = text.lower()
    for label, kws in _DOC_KEYWORDS.items():
        if any(kw in low for kw in kws):
            reqs.append({"key": label, "kind": "document", "label": label,
                         "target": kws, "mandatory": True})
    return reqs


def job_requirements(job: dict) -> list[dict]:
    reqs = []
    qual = str(job.get("qualification", "")) or str(job.get("description", ""))
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
            reqs.append({"key": label, "kind": "document", "label": label,
                         "target": kws, "mandatory": True})
    yrs = _years_from_text(qual)
    if yrs:
        reqs.append({"key": "experience", "kind": "experience",
                     "label": f"~{yrs}+ years experience", "target": yrs, "mandatory": True})
    if not reqs:
        reqs.append({"key": "Eligibility document", "kind": "document",
                     "label": "Qualification proof (see official notification)",
                     "target": [], "mandatory": True})
    return reqs


# ---------------------------------------------------------------------------
# Extract facts about the USER from profile + uploaded document text
# ---------------------------------------------------------------------------
def user_facts(profile: dict, doc_text: str = "") -> dict:
    low = (doc_text or "").lower()
    facts = {
        "class_rank": core._rank(profile.get("contractor_class")),
        "turnover_lakhs": float(profile.get("turnover_lakhs") or 0),
        "experience_years": int(profile.get("experience_years") or 0),
        "doc_text": low,
    }
    # Let uploaded documents override/raise profile facts when they say more.
    for label in ("a", "b", "c", "d"):
        if f"class {label}" in low:
            facts["class_rank"] = max(facts["class_rank"], core._rank(f"class {label}"))
    t = _turnover_from_text(low)
    if t:
        facts["turnover_lakhs"] = max(facts["turnover_lakhs"], t)
    return facts


# ---------------------------------------------------------------------------
# The evaluation
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
    return evaluate(tender_requirements(tender), user_facts(profile, doc_text))


def evaluate_job(job: dict, profile: dict, doc_text: str = "") -> dict:
    return evaluate(job_requirements(job), user_facts(profile, doc_text))


# ===========================================================================
# RESUME ANALYZER  (new — for the Jobs tab "Match My Resume" widget)
# ===========================================================================

_DEGREE_PATTERNS: list[tuple[str, list[str]]] = [
    ("B.Tech / B.E. (Engineering)", ["b.tech", "b.e.", "btech", "bachelor of engineering", "be (", "b.e in", "b.tech in"]),
    ("B.Sc / B.A. / B.Com (Graduate)", ["b.sc", "b.a.", "b.com", "bachelor of", "bsc", "ba ", "b.com", "graduate", "graduation"]),
    ("M.Tech / M.E.", ["m.tech", "m.e.", "mtech", "master of engineering"]),
    ("MBA / PGDM", ["mba", "pgdm", "master of business"]),
    ("MCA", ["mca", "master of computer"]),
    ("12th / Intermediate", ["12th", "intermediate", "higher secondary", "hsc", "+2", "class xii"]),
    ("Diploma", ["diploma"]),
    ("B.Ed (Teacher Training)", ["b.ed", "bed ", "bachelor of education"]),
    ("MBBS / Medical Degree", ["mbbs", "md ", "ms (medicine)", "bachelor of medicine"]),
    ("GNM / B.Sc Nursing", ["gnm", "b.sc nursing", "bsc nursing", "general nursing"]),
]

_SKILL_CAT_MAP: dict[str, list[str]] = {
    "Engineering":    ["autocad", "civil", "structural", "electrical", "mechanical", "revit", "staad"],
    "IT Services":    ["python", "java", "sql", "linux", "cloud", "networking", "software", "programming"],
    "Education":      ["teaching", "pedagogy", "curriculum", "classroom", "tet", "ctet"],
    "Administration": ["ms office", "excel", "word", "tally", "documentation", "compliance"],
    "Police":         ["law", "legal", "driving", "physical"],
    "Health":         ["patient care", "clinical", "pharmacy", "nursing", "lab", "diagnostics"],
}

_CERT_KEYWORDS = ["ccna", "ccnp", "pmp", "itil", "cfa", " ca ", "iso", "gnm", "b.ed", "ctet", "tet", "gate"]


def _resume_reqs(job: dict) -> list[dict]:
    """Build a requirement checklist from a job record for resume matching."""
    reqs: list[dict] = []
    title_low = (job.get("title", "") + " " + job.get("department", "")).lower()
    qual_low  = (job.get("qualification") or "").lower()
    cat       = job.get("category", "General")

    # --- Degree from qualification field or infer from title/category ---
    degree_added = False
    if qual_low:
        for label, kws in _DEGREE_PATTERNS:
            if any(kw in qual_low for kw in kws):
                reqs.append({"label": label, "kind": "degree", "target": kws})
                degree_added = True
                break

    if not degree_added:
        if cat == "Engineering" or any(k in title_low for k in ["engineer", "technical", "jto"]):
            reqs.append({"label": "B.Tech / B.E. in Engineering",
                         "kind": "degree",
                         "target": ["b.tech", "b.e.", "btech", "engineering"]})
        elif cat == "Education" or any(k in title_low for k in ["teacher", "lecturer", "professor", "college"]):
            reqs.append({"label": "Graduate degree (B.A./B.Sc./B.Tech) + B.Ed preferred",
                         "kind": "degree",
                         "target": ["bachelor", "graduate", "b.a.", "b.sc", "b.ed",
                                    "graduation", "b.tech", "btech", "b.com", "bca"]})
        elif cat == "Health" or any(k in title_low for k in ["nurse", "medical", "doctor", "health"]):
            reqs.append({"label": "Medical / nursing qualification (MBBS / GNM / B.Sc Nursing)",
                         "kind": "degree",
                         "target": ["mbbs", "gnm", "nursing", "b.sc nursing", "bsc nursing"]})
        else:
            reqs.append({"label": "Graduate degree (any discipline)",
                         "kind": "degree",
                         "target": ["bachelor", "graduate", "b.a.", "b.sc", "b.tech", "graduation", "degree"]})

    # --- Experience ---
    yrs = _years_from_text(qual_low)
    if yrs:
        reqs.append({"label": f"{yrs}+ years relevant experience",
                     "kind": "experience", "target": yrs})

    # --- Hindi for CG/UP government postings ---
    if job.get("state") in ("Uttar Pradesh", "Chhattisgarh"):
        reqs.append({"label": "Hindi language proficiency",
                     "kind": "language", "target": ["hindi"]})

    # --- Category-specific skills ---
    cat_skills = _SKILL_CAT_MAP.get(cat, [])
    if cat_skills:
        reqs.append({"label": f"Domain skills: {', '.join(cat_skills[:4])}",
                     "kind": "skills", "target": cat_skills})

    return reqs


def _resume_facts(resume_text: str) -> dict:
    """Extract structured facts from raw resume text using regex/keywords."""
    low = resume_text.lower()
    degrees: list[str] = []
    for label, kws in _DEGREE_PATTERNS:
        if any(kw in low for kw in kws):
            degrees.append(label)

    exp_matches = re.findall(r"(\d+)\s*\+?\s*years?\s*(?:of\s+)?(?:experience|exp\.?|work)", low)
    exp_years = max((int(x) for x in exp_matches), default=0)

    all_skills = [kw for kws in _SKILL_CAT_MAP.values() for kw in kws]
    skills = [s for s in all_skills if s in low]

    certifications = [c for c in _CERT_KEYWORDS if c in low]

    languages = [lang for lang in ["hindi", "english", "urdu", "punjabi", "marathi"] if lang in low]

    return {
        "degrees": degrees,
        "experience_years": exp_years,
        "skills": skills,
        "certifications": certifications,
        "languages": languages,
        "raw": low,
    }


def _keyword_resume_eval(job: dict, resume_text: str) -> dict:
    reqs  = _resume_reqs(job)
    facts = _resume_facts(resume_text)

    met, missing, unknown = [], [], []

    for req in reqs:
        kind, target = req["kind"], req.get("target")
        label = req["label"]

        if not facts["raw"]:
            unknown.append(label)
            continue

        if kind == "degree":
            found = any(kw in facts["raw"] for kw in (target or []))
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

    total = len(met) + len(missing) + len(unknown)
    match_pct = round(100 * len(met) / total) if total else 0

    if not missing and not unknown:
        verdict = "Your resume appears to satisfy all stated requirements. Verify against the official advertisement before applying."
    elif len(met) == 0:
        verdict = "The resume doesn't clearly match the requirements for this role. You may be missing key qualifications."
    elif not missing:
        verdict = "Some requirements couldn't be verified from the text. Download the official notification to check full eligibility criteria."
    else:
        verdict = (f"Partial match — {len(met)} of {total} requirements found in your resume. "
                   f"Review the {len(missing)} missing item(s) before applying.")

    return {"match_pct": match_pct, "met": met, "missing": missing,
            "unknown": unknown, "verdict": verdict}


def _llm_resume_eval(job: dict, resume_text: str) -> dict | None:
    """Claude-powered resume evaluation. Returns None if API unavailable."""
    qual = job.get("qualification") or "Not specified — infer from job title and category"
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

Tasks:
1. Identify 4-6 key requirements for this job (degree, experience, skills, language, certifications, etc.)
2. For each requirement check if the resume satisfies it — status must be exactly "met", "missing", or "unknown"
3. Estimate an overall match percentage (0-100)
4. Write a 1-2 sentence plain English verdict

Return ONLY valid JSON, no markdown fence, no explanation:
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

    return {
        "match_pct": max(0, min(100, int(data.get("match_pct", 0)))),
        "met": met, "missing": missing, "unknown": unknown,
        "verdict": str(data.get("verdict", "")),
    }


def evaluate_resume_for_job(job: dict, resume_text: str) -> dict:
    """
    Check how well a resume matches a government job posting.

    Returns:
        match_pct : int (0-100)
        met       : list[str] — requirements the resume satisfies
        missing   : list[str] — requirements not found
        unknown   : list[str] — could not verify
        verdict   : str — plain English summary
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        result = _llm_resume_eval(job, resume_text)
        if result is not None:
            return result
    return _keyword_resume_eval(job, resume_text)
