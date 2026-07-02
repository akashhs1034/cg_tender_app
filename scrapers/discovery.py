"""
scrapers/discovery.py — auto-discover new CG/UP tender & job sources.

Instead of you hunting for portals, this crawls a few government "hub" pages and
(best-effort) a public search engine, keeps links on real .gov.in/.nic.in-style
domains that look like tender/recruitment pages, lightly validates them, and
appends the good ones to data/ai_sources.json — where the generic AI extractor
picks them up on the next run. No code changes needed to grow coverage.

Runs at most once a week (a marker file gates it) so the daily pipeline stays
fast. Never raises: any failure is logged and skipped.

    from scrapers import discovery
    added = discovery.discover()      # returns list of newly-added source dicts
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

_ROOT = Path(__file__).parent.parent
_CONFIG = _ROOT / "data" / "ai_sources.json"
_QUEUE = _ROOT / "data" / "discovered_queue.json"
_MARKER = _ROOT / "data" / ".last_discovery"

_MIN_DAYS_BETWEEN = 6
_MAX_TOTAL_AI_SOURCES = 80          # keep the daily run bounded
_MAX_NEW_PER_RUN = 12

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
}

# Government "hub" pages whose links fan out to many department/portal pages.
_SEED_HUBS = [
    "https://cg.gov.in/",
    "https://cgstate.gov.in/",
    "https://up.gov.in/en",
]

# Best-effort public search (DuckDuckGo HTML endpoint — no API key needed).
_SEARCH_QUERIES = [
    "Chhattisgarh government tender notice site:gov.in",
    "Chhattisgarh recruitment vacancy site:cgstate.gov.in",
    "Uttar Pradesh government tender e-nivida site:gov.in",
    "Uttar Pradesh vibhag bharti recruitment site:up.gov.in",
    "Chhattisgarh nagar nigam tender",
    "Uttar Pradesh nagar nigam tender notice",
]

# A candidate URL/anchor must smell like a tender or job page.
_RELEVANT = re.compile(
    r"tender|nivida|nivida|e-?proc|procure|bid|recruit|vacan|bharti|"
    r"naukri|career|job|advertisement|notification|notice",
    re.I,
)
# Only trust government-style domains.
_GOV_DOMAIN = re.compile(r"\.gov\.in$|\.nic\.in$|cgstate\.gov\.in$|\.up\.nic\.in$", re.I)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _due() -> bool:
    if not _MARKER.exists():
        return True
    try:
        last = datetime.fromisoformat(_MARKER.read_text().strip())
        return (_now() - last).days >= _MIN_DAYS_BETWEEN
    except Exception:
        return True


def _touch_marker() -> None:
    try:
        _MARKER.write_text(_now().isoformat())
    except Exception:
        pass


def _load_config() -> dict:
    if _CONFIG.exists():
        try:
            return json.loads(_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sources": []}


def _existing_urls(cfg: dict) -> set[str]:
    return {(_normalize(s.get("url", ""))) for s in (cfg.get("sources") or [])}


def _normalize(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _guess_state(url: str, text: str = "") -> str:
    blob = (url + " " + text).lower()
    dom = _domain(url)
    if any(k in blob for k in ("chhattisgarh", "cgstate", "chattisgarh", "raipur",
                               "bilaspur", "durg", "bastar")) or "cg" in dom.split("."):
        return "Chhattisgarh"
    if any(k in blob for k in ("uttar pradesh", "up.gov", "up.nic", "lucknow",
                               "kanpur", "prayagraj", "varanasi", "noida")):
        return "Uttar Pradesh"
    return ""


def _guess_kind(text: str) -> str:
    t = text.lower()
    has_job = bool(re.search(r"recruit|vacan|bharti|naukri|career|job|post", t))
    has_tender = bool(re.search(r"tender|nivida|bid|procure|e-?proc", t))
    if has_job and not has_tender:
        return "job"
    if has_tender and not has_job:
        return "tender"
    return "auto"


def _fetch(url: str, timeout: int = 20) -> str | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout)
        if r.status_code == 200 and len(r.text) > 400:
            return r.text
    except Exception:
        return None
    return None


def _links_from_html(base_url: str, html: str) -> list[tuple[str, str]]:
    """Return (href, anchor_text) pairs from a page."""
    out = []
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"].strip())
            text = a.get_text(" ", strip=True)
            if href.startswith("http"):
                out.append((href, text))
    except Exception:
        pass
    return out


def _ddg_results(query: str) -> list[tuple[str, str]]:
    """Best-effort DuckDuckGo HTML search → [(url, title)]. Empty on failure."""
    html = _fetch(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}", timeout=20)
    if not html:
        return []
    results = []
    for href, text in _links_from_html("https://duckduckgo.com/", html):
        # DDG wraps external links as /l/?uddg=<encoded real url>
        if "duckduckgo.com/l/" in href:
            qs = parse_qs(urlparse(href).query)
            real = qs.get("uddg", [None])[0]
            if real:
                results.append((unquote(real), text))
        elif _GOV_DOMAIN.search(_domain(href)):
            results.append((href, text))
    return results


def _candidate_ok(url: str, text: str) -> bool:
    dom = _domain(url)
    if not dom or not _GOV_DOMAIN.search(dom):
        return False
    if not _RELEVANT.search(url + " " + text):
        return False
    # avoid obvious non-content
    if any(url.lower().endswith(ext) for ext in (".jpg", ".png", ".gif", ".zip")):
        return False
    return True


def _validate(url: str) -> str:
    """Fetch the candidate; return its text if it really looks like a tender/job
    page, else empty string."""
    html = _fetch(url, timeout=18)
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    except Exception:
        text = html
    # needs at least a couple of relevant hits to be worth extracting
    if len(_RELEVANT.findall(text)) >= 2:
        return text[:4000]
    return ""


def discover(force: bool = False) -> list[dict]:
    if not force and not _due():
        print("   discovery: skipped (ran within the last "
              f"{_MIN_DAYS_BETWEEN} days)")
        return []

    cfg = _load_config()
    existing = _existing_urls(cfg)
    if len(cfg.get("sources") or []) >= _MAX_TOTAL_AI_SOURCES:
        print("   discovery: source list already at capacity — skipping")
        _touch_marker()
        return []

    print("   discovery: scanning government hubs + search for new CG/UP sources…")
    seen: set[str] = set()
    candidates: list[tuple[str, str]] = []

    # 1) Crawl hub pages for outbound gov links.
    for hub in _SEED_HUBS:
        html = _fetch(hub, timeout=20)
        if not html:
            continue
        for href, text in _links_from_html(hub, html):
            key = _normalize(href)
            if key in seen or key in existing:
                continue
            if _candidate_ok(href, text):
                seen.add(key)
                candidates.append((href, text))
        time.sleep(0.5)

    # 2) Best-effort search queries.
    for q in _SEARCH_QUERIES:
        for href, text in _ddg_results(q):
            key = _normalize(href)
            if key in seen or key in existing:
                continue
            if _candidate_ok(href, text):
                seen.add(key)
                candidates.append((href, text))
        time.sleep(1.0)

    print(f"   discovery: {len(candidates)} raw candidates; validating…")

    added: list[dict] = []
    for href, text in candidates:
        if len(added) >= _MAX_NEW_PER_RUN:
            break
        page_text = _validate(href)
        if not page_text:
            continue
        blob = text + " " + page_text
        src = {
            "name": (text[:60] or _domain(href)) + " (auto-discovered)",
            "url": href,
            "state": _guess_state(href, blob),
            "kind": _guess_kind(blob),
            "format": "html",
            "render": False,
            "discovered_at": _now().date().isoformat(),
        }
        added.append(src)
        print(f"   discovery: + {src['state'] or '??'} [{src['kind']}] {href}")
        time.sleep(0.4)

    if added:
        cfg.setdefault("sources", []).extend(added)
        try:
            _CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False),
                               encoding="utf-8")
        except Exception as exc:
            print(f"   discovery: could not write config — {exc}")
        # also log the raw queue for auditing
        try:
            _QUEUE.write_text(json.dumps(added, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        except Exception:
            pass

    _touch_marker()
    print(f"   discovery: added {len(added)} new source(s) to ai_sources.json")
    return added


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    new = discover(force=True)
    print(f"\n{'-'*70}\n  {len(new)} sources discovered\n{'-'*70}")
    for s in new:
        print(f"  {s['state'] or '??':<14} [{s['kind']:<6}] {s['url']}")
