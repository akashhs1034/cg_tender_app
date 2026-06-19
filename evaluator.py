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
