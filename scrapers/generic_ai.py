"""
scrapers/generic_ai.py — config-driven AI extractor for arbitrary sources.

The goal: onboard a NEW tender/job source without writing a new scraper.
Add one entry to ``data/ai_sources.json`` (a URL + a couple of hints) and this
module fetches the page (or PDF/image), hands the content to Gemini, and turns
whatever it finds into normalized core.tender_record() / core.job_record()
objects — the same shape every hand-written scraper produces.

How it decides what to do per source (fields in ai_sources.json):
    name    : human label (shown in logs / provenance)
    url     : page, listing, PDF, or image URL to read
    state   : "Chhattisgarh" | "Uttar Pradesh" | "" (hint only; the model still
              tags each record's real state, and we keep only CG/UP + central)
    kind    : "tender" | "job" | "auto"   (auto = let the model return both)
    format  : "html" (default) | "pdf" | "image"
    render  : true to load with Playwright (JS-heavy pages); default false

Nothing here raises: a bad source is logged and skipped so one dead URL never
breaks the daily run.

    from scrapers import generic_ai
    result = generic_ai.collect()          # {"tenders":[...], "jobs":[...], "report":{...}}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402

_ROOT = Path(__file__).parent.parent
_CONFIG = _ROOT / "data" / "ai_sources.json"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
}

# Cap the text handed to the model — keeps quota/latency sane; listings rarely
# need more than this to enumerate their rows.
_MAX_TEXT_CHARS = 20000

_ALLOWED_STATES = {"chhattisgarh", "uttar pradesh", "central", "all india", "india"}

_EXTRACT_INSTRUCTIONS = """You are a precise data extractor for an Indian government
tenders-and-jobs aggregator focused on Chhattisgarh (CG) and Uttar Pradesh (UP).

From the SOURCE CONTENT below, extract every genuine government/PSU TENDER and every
JOB / recruitment notice you can find. Ignore navigation, ads, headers, and anything
that is not an actual tender or job posting.

Return STRICT JSON with exactly this shape:
{
  "tenders": [
    {
      "title": "...",                     // required, the work/procurement title
      "organization": "...",              // issuing dept/PSU/office
      "department": "...",
      "category": "...",                  // e.g. Civil, Electrical, IT, Supply
      "tender_no": "...",
      "value_text": "...",                // estimated value as written (with ₹/Rs if shown)
      "emd": "...",
      "deadline": "...",                  // submission/last date, keep as written
      "district": "...",                  // CG/UP district if identifiable
      "state": "...",                     // Chhattisgarh | Uttar Pradesh | Central
      "description": "...",
      "document_url": "..."               // absolute link to the notice/PDF if present
    }
  ],
  "jobs": [
    {
      "title": "...",                     // required, the post/position name
      "department": "...",
      "vacancies": "...",
      "qualification": "...",
      "salary": "...",
      "advertisement_no": "...",
      "deadline": "...",                  // last date to apply, as written
      "district": "...",
      "state": "...",
      "description": "...",
      "apply_link": "..."
    }
  ]
}

Rules:
- Only include items relevant to Chhattisgarh, Uttar Pradesh, or central/all-India postings.
- If the content clearly has only tenders (or only jobs), return the other array empty.
- Never invent data. Omit a field (use "") when it is not present in the content.
- Return raw JSON only — no markdown, no commentary.
"""


def _load_config() -> list[dict]:
    if not _CONFIG.exists():
        return []
    try:
        data = json.loads(_CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"   generic_ai: could not parse {_CONFIG.name} — {exc}")
        return []
    sources = data.get("sources") if isinstance(data, dict) else data
    return [s for s in (sources or []) if isinstance(s, dict) and s.get("url")]


def _fetch_html_text(url: str, render: bool) -> str | None:
    """Return visible text of a page. Uses Playwright when render=True."""
    if render:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=_HEADERS["User-Agent"],
                                        locale="en-IN")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)
                html = page.content()
                browser.close()
        except Exception as exc:
            print(f"   generic_ai: playwright fetch failed {url} — {exc}")
            return None
    else:
        try:
            r = requests.get(url, headers=_HEADERS, timeout=30)
            r.raise_for_status()
            html = r.text
        except Exception as exc:
            print(f"   generic_ai: fetch failed {url} — {exc}")
            return None

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
    except Exception:
        text = html
    return text[:_MAX_TEXT_CHARS] if text else None


def _fetch_bytes(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=60)
        r.raise_for_status()
        return r.content
    except Exception as exc:
        print(f"   generic_ai: download failed {url} — {exc}")
        return None


def _extract(source: dict) -> dict | None:
    """Call the shared LLM helper and return the parsed {tenders,jobs} dict."""
    from evaluator import _llm_extract  # reuse Gemini REST + Claude fallback

    fmt = (source.get("format") or "html").lower()
    url = source["url"]

    if fmt == "pdf" or fmt == "image":
        blob = _fetch_bytes(url)
        if not blob:
            return None
        mime = "application/pdf" if fmt == "pdf" else "image/jpeg"
        prompt = _EXTRACT_INSTRUCTIONS + f"\n\nSOURCE: {source.get('name') or url}"
        return _llm_extract(prompt, document_bytes=blob, mime_type=mime)

    text = _fetch_html_text(url, bool(source.get("render")))
    if not text:
        return None
    prompt = (_EXTRACT_INSTRUCTIONS
              + f"\n\nSOURCE: {source.get('name') or url}\n\nSOURCE CONTENT:\n{text}")
    return _llm_extract(prompt)


def _state_ok(state: str | None, hint: str | None) -> bool:
    s = (state or hint or "").strip().lower()
    if not s:
        return True  # unknown — let dedup/UI filters decide
    return any(a in s for a in _ALLOWED_STATES)


def _to_tenders(items: list, source: dict) -> list[dict]:
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        title = (it.get("title") or "").strip()
        if len(title) < 6:
            continue
        if not _state_ok(it.get("state"), source.get("state")):
            continue
        out.append(core.tender_record(
            title=title,
            state=(it.get("state") or source.get("state") or "").strip() or None,
            organization=(it.get("organization") or it.get("department")
                          or source.get("name") or "").strip() or None,
            department=(it.get("department") or "").strip() or None,
            category=(it.get("category") or "").strip() or None,
            tender_no=(it.get("tender_no") or "").strip() or None,
            value_text=(it.get("value_text") or "").strip() or None,
            emd=(it.get("emd") or "").strip() or None,
            deadline=(it.get("deadline") or "").strip() or None,
            district=(it.get("district") or "").strip() or None,
            description=(it.get("description") or "").strip() or None,
            document_url=(it.get("document_url") or "").strip() or source["url"],
            source_type="ai_extracted",
            source_name=source.get("name") or source["url"],
            source_url=source["url"],
        ))
    return out


def _to_jobs(items: list, source: dict) -> list[dict]:
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        title = (it.get("title") or "").strip()
        if len(title) < 4:
            continue
        if not _state_ok(it.get("state"), source.get("state")):
            continue
        out.append(core.job_record(
            title=title,
            state=(it.get("state") or source.get("state") or "").strip() or None,
            department=(it.get("department") or source.get("name") or "").strip() or None,
            vacancies=(it.get("vacancies") or None),
            qualification=(it.get("qualification") or "").strip() or None,
            salary=(it.get("salary") or "").strip() or None,
            advertisement_no=(it.get("advertisement_no") or "").strip() or None,
            deadline=(it.get("deadline") or "").strip() or None,
            district=(it.get("district") or "").strip() or None,
            description=(it.get("description") or "").strip() or None,
            apply_link=(it.get("apply_link") or "").strip() or source["url"],
            source_type="ai_extracted",
            source_name=source.get("name") or source["url"],
            source_url=source["url"],
        ))
    return out


def collect() -> dict:
    """Run every configured AI source. Returns {tenders, jobs, report}."""
    import os
    sources = _load_config()
    tenders: list[dict] = []
    jobs: list[dict] = []
    report: dict = {}

    if not sources:
        print("   generic_ai: no sources configured (data/ai_sources.json) — skipping")
        return {"tenders": [], "jobs": [], "report": {}}

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("   generic_ai: no GEMINI_API_KEY/ANTHROPIC_API_KEY — skipping AI extraction")
        return {"tenders": [], "jobs": [], "report": {
            "generic_ai": {"source_id": "generic_ai", "count": 0,
                           "status": "failed", "error": "no LLM API key"}}}

    print(f"   generic_ai: extracting from {len(sources)} configured source(s)…")
    for src in sources:
        name = src.get("name") or src["url"]
        try:
            parsed = _extract(src)
            if not parsed or not isinstance(parsed, dict):
                report[name] = {"source_id": name, "count": 0,
                                "status": "no_records", "error": None}
                continue
            kind = (src.get("kind") or "auto").lower()
            t = _to_tenders(parsed.get("tenders"), src) if kind in ("tender", "auto") else []
            j = _to_jobs(parsed.get("jobs"), src) if kind in ("job", "auto") else []
            tenders += t
            jobs += j
            print(f"   generic_ai: {name} → {len(t)} tenders, {len(j)} jobs")
            report[name] = {"source_id": name, "count": len(t) + len(j),
                            "status": "healthy" if (t or j) else "no_records",
                            "error": None}
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"[:500]
            print(f"   generic_ai: {name} failed safely — {err}")
            report[name] = {"source_id": name, "count": 0,
                            "status": "failed", "error": err}

    print(f"   generic_ai: total {len(tenders)} tenders, {len(jobs)} jobs")
    return {"tenders": tenders, "jobs": jobs, "report": report}


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    print(f"\n{'-'*70}\n  {len(res['tenders'])} tenders, {len(res['jobs'])} jobs (generic_ai)\n{'-'*70}")
    for r in (res["tenders"][:3] + res["jobs"][:3]):
        print()
        for k, v in r.items():
            if v not in (None, "", [], {}):
                print(f"  {k:<16}: {v}")
