"""Safe, bounded public-source discovery for OPPORTA Phase 4A.

This command only creates an admin review queue. It never adds a discovered URL
to ingestion, downloads linked documents, or attempts to solve a CAPTCHA.
"""

from __future__ import annotations

import argparse
import json
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from source_registry import load_registry
from source_validator import (
    detect_restricted_access,
    is_document_url,
    is_private_or_local_url,
    is_social_url,
    load_discovery_queries,
    normalize_url,
    validate_candidate,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = DATA / "discovered_sources.json"
USER_AGENT = "OPPORTA-Discovery/1.0 (+public-source-review; no-captcha-bypass)"
DEFAULT_TIMEOUT = 6.0
MAX_HTML_BYTES = 2_000_000
MAX_SITEMAP_BYTES = 4_000_000
MAX_REDIRECTS = 3
MAX_CANDIDATES_PER_SOURCE = 30

_robots_cache: dict[str, RobotFileParser | None] = {}
_robots_lock = threading.Lock()
_thread_local = threading.local()


def _session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.5"
                ),
            }
        )
        _thread_local.session = session
    return session


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _same_site(first_url: str, second_url: str) -> bool:
    first = (urlsplit(first_url).hostname or "").lower().removeprefix("www.")
    second = (urlsplit(second_url).hostname or "").lower().removeprefix("www.")
    return bool(first and first == second)


def _safe_redirect_target(current_url: str, location: str) -> str:
    target = normalize_url(urljoin(current_url, location))
    if (
        not target
        or is_private_or_local_url(target)
        or is_social_url(target)
        or not _same_site(current_url, target)
    ):
        return ""
    return target


def _read_response(response: requests.Response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=65_536):
        if not chunk:
            continue
        size += len(chunk)
        if size > max_bytes:
            raise ValueError(f"response exceeds {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_get(url: str, timeout: float, max_bytes: int) -> tuple[str, str, str]:
    """Fetch one bounded public text response without cross-domain redirects."""
    current = normalize_url(url)
    if not current or is_private_or_local_url(current) or is_social_url(current):
        raise ValueError("unsafe or unsupported URL")

    for _ in range(MAX_REDIRECTS + 1):
        response = _session().get(
            current,
            timeout=timeout,
            stream=True,
            allow_redirects=False,
        )
        if response.is_redirect or response.is_permanent_redirect:
            target = _safe_redirect_target(current, response.headers.get("Location", ""))
            response.close()
            if not target:
                raise ValueError("redirect leaves the public source domain")
            current = target
            continue
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if not any(
            allowed in content_type
            for allowed in ("text/", "html", "xml", "json")
        ):
            response.close()
            raise ValueError(f"unsupported content type: {content_type or 'unknown'}")
        try:
            payload = _read_response(response, max_bytes)
            encoding = response.encoding or response.apparent_encoding or "utf-8"
        finally:
            response.close()
        return current, content_type, payload.decode(encoding, errors="replace")
    raise ValueError("too many redirects")


def _robots_parser(url: str, timeout: float) -> RobotFileParser | None:
    origin = _origin(url)
    with _robots_lock:
        if origin in _robots_cache:
            return _robots_cache[origin]

    parser: RobotFileParser | None = None
    robots_url = urljoin(origin + "/", "robots.txt")
    try:
        _, _, text = _safe_get(robots_url, min(timeout, 4.0), 500_000)
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(text.splitlines())
    except requests.HTTPError as exc:
        # A missing robots file publishes no crawl restriction.
        if exc.response is not None and exc.response.status_code not in {404, 410}:
            parser = None
    except (requests.RequestException, ValueError):
        parser = None

    with _robots_lock:
        _robots_cache[origin] = parser
    return parser


def robots_allowed(url: str, timeout: float) -> bool:
    parser = _robots_parser(url, timeout)
    return True if parser is None else parser.can_fetch(USER_AGENT, url)


def _source_urls(source: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("discovery_url", "url", "base_url"):
        if source.get(key):
            values.append(str(source[key]))
    values.extend(str(value) for value in source.get("urls", []) if value)
    return list(
        dict.fromkeys(
            normalized
            for value in values
            if (normalized := normalize_url(value))
        )
    )


def _relevant_link(
    url: str, text: str, queries: dict[str, list[str]]
) -> bool:
    if is_document_url(url):
        return True
    searchable = f"{url} {text}".casefold()
    terms = (
        term
        for group in ("tender", "job", "news")
        for term in queries.get(group, [])
        if len(term.strip()) >= 3
    )
    return any(term.casefold() in searchable for term in terms)


def _public_internal_link(base_url: str, candidate_url: str) -> bool:
    if (
        not candidate_url
        or is_private_or_local_url(candidate_url)
        or is_social_url(candidate_url)
    ):
        return False
    if _same_site(base_url, candidate_url):
        return True
    host = (urlsplit(candidate_url).hostname or "").lower()
    return is_document_url(candidate_url) and host == "cdn.s3waas.gov.in"


def _candidate(
    *,
    url: str,
    title: str,
    context: str,
    page_text: str,
    source: dict[str, Any],
    discovered_from: str,
    allowed: bool,
    queries: dict[str, list[str]],
    known_urls: set[str],
    now: datetime,
) -> dict[str, Any]:
    normalized = normalize_url(url)
    return validate_candidate(
        url=normalized,
        title=title,
        context_text=context,
        page_text=page_text,
        discovered_from=discovered_from,
        source_type=str(source.get("source_type") or "web"),
        source_state=str(source.get("state") or ""),
        source_district=str(source.get("district") or ""),
        source_name=str(source.get("source_name") or ""),
        robots_allowed=allowed,
        requires_playwright=bool(source.get("requires_playwright")),
        duplicate=normalized in known_urls,
        queries=queries,
        now=now,
    )


def _parse_html_links(
    html: str,
    page_url: str,
    source: dict[str, Any],
    queries: dict[str, list[str]],
    known_urls: set[str],
    timeout: float,
    now: datetime,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    page_text = soup.get_text(" ", strip=True)[:80_000]
    captcha, login, paywall = detect_restricted_access(page_text)
    if captcha or login or paywall:
        return [
            _candidate(
                url=page_url,
                title=page_title,
                context=page_text[:5_000],
                page_text="",
                source=source,
                discovered_from=page_url,
                allowed=True,
                queries=queries,
                known_urls=set(),
                now=now,
            )
        ]

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        url = normalize_url(urljoin(page_url, anchor.get("href", "")))
        title = anchor.get_text(" ", strip=True) or anchor.get("title", "").strip()
        # A row/list/article is useful local context; using an arbitrary parent
        # can accidentally classify every navigation link from the whole body.
        container = anchor.find_parent(["tr", "li", "article"])
        context = container.get_text(" ", strip=True)[:1_500] if container else title
        if (
            not url
            or url in seen
            or not _public_internal_link(page_url, url)
            or not _relevant_link(url, f"{title} {context}", queries)
        ):
            continue
        candidates.append(
            _candidate(
                url=url,
                title=title,
                context=context,
                page_text=page_text,
                source=source,
                discovered_from=page_url,
                allowed=robots_allowed(url, timeout),
                queries=queries,
                known_urls=known_urls,
                now=now,
            )
        )
        seen.add(url)
        if len(candidates) >= MAX_CANDIDATES_PER_SOURCE:
            break
    return candidates


def _sitemap_candidates(
    page_url: str,
    source: dict[str, Any],
    queries: dict[str, list[str]],
    known_urls: set[str],
    timeout: float,
    now: datetime,
) -> list[dict[str, Any]]:
    sitemap_url = normalize_url(urljoin(_origin(page_url) + "/", "sitemap.xml"))
    if not sitemap_url or not robots_allowed(sitemap_url, timeout):
        return []
    try:
        _, _, xml_text = _safe_get(sitemap_url, timeout, MAX_SITEMAP_BYTES)
        root = ET.fromstring(xml_text)
    except (requests.RequestException, ValueError, ET.ParseError):
        return []

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in root.iter():
        if not node.tag.lower().endswith("loc") or not node.text:
            continue
        url = normalize_url(node.text.strip())
        if (
            not url
            or url in seen
            or not _public_internal_link(page_url, url)
            or not _relevant_link(url, "", queries)
        ):
            continue
        candidates.append(
            _candidate(
                url=url,
                title=(
                    Path(urlsplit(url).path)
                    .name.replace("-", " ")
                    .replace("_", " ")
                ),
                context="sitemap entry",
                page_text="",
                source=source,
                discovered_from=sitemap_url,
                allowed=robots_allowed(url, timeout),
                queries=queries,
                known_urls=known_urls,
                now=now,
            )
        )
        seen.add(url)
        if len(candidates) >= MAX_CANDIDATES_PER_SOURCE:
            break
    return candidates


def discover_source(
    source: dict[str, Any],
    queries: dict[str, list[str]],
    known_urls: set[str],
    timeout: float,
    now: datetime,
) -> tuple[list[dict[str, Any]], str | None]:
    """Discover from one registry source with complete failure isolation."""
    source_urls = _source_urls(source)
    if not source_urls:
        return [], "no public source URL"
    page_url = source_urls[0]
    if not robots_allowed(page_url, timeout):
        return [
            _candidate(
                url=page_url,
                title=str(source.get("source_name") or ""),
                context="",
                page_text="",
                source=source,
                discovered_from=page_url,
                allowed=False,
                queries=queries,
                known_urls=set(),
                now=now,
            )
        ], None

    try:
        final_url, _, html = _safe_get(page_url, timeout, MAX_HTML_BYTES)
    except (requests.RequestException, ValueError) as exc:
        return [], f"{type(exc).__name__}: {str(exc)[:180]}"

    try:
        html_candidates = _parse_html_links(
            html, final_url, source, queries, known_urls, timeout, now
        )
    except Exception as exc:  # one malformed page must not stop the queue
        html_candidates = []
        parse_error = f"{type(exc).__name__}: {str(exc)[:180]}"
    else:
        parse_error = None
    sitemap_candidates = _sitemap_candidates(
        final_url, source, queries, known_urls, timeout, now
    )
    return html_candidates + sitemap_candidates, parse_error


def _merge_candidate(
    current: dict[str, Any], incoming: dict[str, Any]
) -> dict[str, Any]:
    best = (
        incoming
        if int(incoming.get("confidence_score", 0))
        > int(current.get("confidence_score", 0))
        else current
    )
    merged = dict(best)
    merged["first_seen_at"] = current.get("first_seen_at") or incoming.get(
        "first_seen_at"
    )
    merged["last_seen_at"] = incoming.get("last_seen_at") or current.get(
        "last_seen_at"
    )
    merged["matched_keywords"] = sorted(
        {
            *current.get("matched_keywords", []),
            *incoming.get("matched_keywords", []),
        },
        key=str.casefold,
    )
    origins = {
        value.strip()
        for item in (
            current.get("discovered_from", ""),
            incoming.get("discovered_from", ""),
        )
        for value in str(item).split(",")
        if value.strip()
    }
    merged["discovered_from"] = ", ".join(sorted(origins))

    ranks = {"pending_review": 3, "captcha_required": 2, "rejected": 1}
    status_record = max(
        (current, incoming),
        key=lambda item: ranks.get(str(item.get("status")), 0),
    )
    merged["status"] = status_record.get("status", "rejected")
    merged["reason"] = status_record.get("reason", "")
    for flag in ("requires_captcha", "requires_ocr", "requires_playwright"):
        merged[flag] = bool(current.get(flag) or incoming.get(flag))
    merged["robots_allowed"] = bool(
        current.get("robots_allowed") and incoming.get("robots_allowed")
    )
    return merged


def _read_existing(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def write_candidates(
    candidates: Iterable[dict[str, Any]], output_path: Path = OUTPUT
) -> list[dict[str, Any]]:
    """Merge first-seen history and atomically replace the fallback queue."""
    merged: dict[str, dict[str, Any]] = {}
    for item in _read_existing(output_path):
        key = normalize_url(str(item.get("url", "")))
        if key:
            merged[key] = item
    for item in candidates:
        key = normalize_url(str(item.get("url", "")))
        if not key:
            continue
        merged[key] = (
            _merge_candidate(merged[key], item) if key in merged else item
        )

    records = sorted(
        merged.values(),
        key=lambda item: (
            str(item.get("status")) != "pending_review",
            -int(item.get("confidence_score", 0)),
            str(item.get("url", "")),
        ),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(output_path)
    return records


def run_discovery(
    *,
    output_path: Path = OUTPUT,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = 12,
    source_limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    queries = load_discovery_queries()
    registry = [source for source in load_registry() if source.get("active", True)]
    if source_limit is not None:
        registry = registry[: max(0, source_limit)]
    known_urls = {url for source in registry for url in _source_urls(source)}
    now = datetime.now(timezone.utc)
    failures: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max(1, min(workers, 24))) as executor:
        futures = {
            executor.submit(
                discover_source, source, queries, known_urls, timeout, now
            ): source
            for source in registry
        }
        for future in as_completed(futures):
            source = futures[future]
            source_id = str(
                source.get("source_id") or source.get("source_name") or "unknown"
            )
            try:
                found, error = future.result()
                candidates.extend(found)
                if error:
                    failures[source_id] = error
            except Exception as exc:  # absolute per-source failure isolation
                failures[source_id] = f"{type(exc).__name__}: {str(exc)[:180]}"

    return write_candidates(candidates, output_path), failures


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover public OPPORTA source candidates for admin review."
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument(
        "--source-limit",
        type=int,
        default=None,
        help="Optional bounded source count for diagnostics.",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    records, failures = run_discovery(
        output_path=args.output,
        timeout=max(1.0, args.timeout),
        workers=args.workers,
        source_limit=args.source_limit,
    )
    counts = {
        status: sum(1 for item in records if item.get("status") == status)
        for status in ("pending_review", "captcha_required", "rejected")
    }
    print(
        "Discovery complete: "
        f"{len(records)} candidate(s), "
        f"{counts['pending_review']} pending review, "
        f"{counts['captcha_required']} CAPTCHA-only, "
        f"{counts['rejected']} rejected."
    )
    if failures:
        print(
            f"{len(failures)} source(s) failed in isolation; "
            "other sources and the review queue were preserved."
        )
    print(f"Fallback queue: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
