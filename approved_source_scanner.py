"""Controlled, review-only scanner for administrator-approved sources.

Findings go to ``discovered_files`` or its ignored local JSON fallback. This
module never writes public tender/job records and never bypasses access controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from source_discovery import MAX_HTML_BYTES, _safe_get, robots_allowed
from source_validator import (
    detect_restricted_access,
    is_document_url,
    is_private_or_local_url,
    is_social_url,
    load_discovery_queries,
    normalize_url,
    url_extension,
    validate_candidate,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
APPROVED_FALLBACK = DATA / "approved_sources.json"
FILES_FALLBACK = DATA / "discovered_files.json"
DEFAULT_TIMEOUT = 6.0
SUPABASE_BATCH_SIZE = 200

FILE_FIELDS = (
    "file_url", "source_url", "file_name", "file_type", "title", "state",
    "district", "category", "source_id", "hash", "status",
    "confidence_score", "requires_ocr", "requires_manual_review",
    "discovered_at", "last_seen_at",
)


def _read_list(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _write_list(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def _supabase_credentials() -> tuple[str, str, bool, str]:
    url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    fallback_key = os.getenv("SUPABASE_KEY", "").strip()
    configured = bool(url or service_key or fallback_key)
    if url and service_key:
        return url, service_key, configured, "service key"
    if url and fallback_key:
        return url, fallback_key, configured, "fallback key"
    return url, "", configured, ""


def _active_source(source: dict[str, Any]) -> bool:
    url = normalize_url(str(source.get("url", "")))
    return bool(
        str(source.get("status", "")).casefold() == "active"
        and not source.get("requires_captcha")
        and url
        and not is_private_or_local_url(url)
        and not is_social_url(url)
    )


def load_approved_sources(
    *,
    fallback_path: Path = APPROVED_FALLBACK,
    client: Any | None = None,
) -> tuple[list[dict[str, Any]], str, str | None]:
    """Prefer the private cloud store; use JSON only with no cloud config."""
    backend = "supabase" if client is not None else "local"
    if client is None:
        url, key, configured, _ = _supabase_credentials()
        if configured:
            backend = "supabase"
            if not (url and key):
                return [], backend, "Supabase approved-source credentials are incomplete"
            try:
                from supabase import create_client

                client = create_client(url, key)
            except Exception as exc:
                return [], backend, f"{type(exc).__name__}: {str(exc)[:200]}"
    if client is None:
        sources = _read_list(fallback_path)
        return [item for item in sources if _active_source(item)], backend, None

    try:
        sources: list[dict[str, Any]] = []
        offset, batch_size = 0, 1_000
        while True:
            rows = (
                client.table("approved_sources")
                .select("*")
                .eq("status", "active")
                .order("source_id")
                .range(offset, offset + batch_size - 1)
                .execute()
                .data
                or []
            )
            sources.extend(item for item in rows if isinstance(item, dict))
            if len(rows) < batch_size:
                break
            offset += batch_size
        return [item for item in sources if _active_source(item)], backend, None
    except Exception as exc:
        return [], backend, f"{type(exc).__name__}: {str(exc)[:200]}"


def _same_site(first_url: str, second_url: str) -> bool:
    first = (urlsplit(first_url).hostname or "").lower().removeprefix("www.")
    second = (urlsplit(second_url).hostname or "").lower().removeprefix("www.")
    return bool(first and first == second)


def _allowed_internal_url(source_url: str, candidate_url: str) -> bool:
    if (
        not candidate_url
        or is_private_or_local_url(candidate_url)
        or is_social_url(candidate_url)
    ):
        return False
    if _same_site(source_url, candidate_url):
        return True
    host = (urlsplit(candidate_url).hostname or "").lower()
    return is_document_url(candidate_url) and host == "cdn.s3waas.gov.in"


def _relevant_page(
    url: str, title: str, queries: dict[str, list[str]]
) -> bool:
    searchable = f"{url} {title}".casefold()
    return any(
        term.casefold() in searchable
        for group in ("tender", "job", "news")
        for term in queries.get(group, [])
        if len(term.strip()) >= 3
    )


def _file_record(
    *,
    file_url: str,
    title: str,
    context: str,
    page_text: str,
    page_url: str,
    source: dict[str, Any],
    queries: dict[str, list[str]],
    now: datetime,
) -> dict[str, Any]:
    evaluation = validate_candidate(
        url=file_url,
        title=title,
        context_text=context,
        page_text=page_text,
        discovered_from=page_url,
        source_type=str(source.get("source_type") or "web"),
        source_state=str(source.get("state") or ""),
        source_district=str(source.get("district") or ""),
        source_name=str(source.get("title") or ""),
        robots_allowed=True,
        requires_playwright=False,
        queries=queries,
        now=now,
    )
    category = str(evaluation.get("category") or "unknown")
    if category == "newspaper":
        category = "document"
    extension = url_extension(file_url)
    timestamp = now.isoformat()
    file_name = unquote(Path(urlsplit(file_url).path).name) or "document"
    return {
        "file_url": file_url,
        "source_url": normalize_url(str(source.get("url", ""))),
        "file_name": file_name,
        "file_type": extension.lstrip("."),
        "title": title.strip() or file_name,
        "state": evaluation.get("state") or source.get("state") or "",
        "district": evaluation.get("district") or source.get("district") or "",
        "category": category,
        "source_id": source.get("source_id") or "",
        # Stable URL hash only; the scanner does not download document bodies.
        "hash": hashlib.sha256(file_url.encode("utf-8")).hexdigest(),
        "status": "pending_review",
        "confidence_score": int(evaluation.get("confidence_score") or 0),
        "requires_ocr": bool(
            evaluation.get("requires_ocr")
            or (extension == ".pdf" and source.get("requires_ocr"))
        ),
        "requires_manual_review": True,
        "discovered_at": timestamp,
        "last_seen_at": timestamp,
    }


def scan_approved_source(
    source: dict[str, Any],
    *,
    timeout: float,
    max_pages: int,
    max_files: int,
    queries: dict[str, list[str]],
    now: datetime,
) -> tuple[list[dict[str, Any]], str | None]:
    """Scan one source with strict bounds and complete failure isolation."""
    source_url = normalize_url(str(source.get("url", "")))
    if not _active_source(source):
        return [], "source is not active, public, and CAPTCHA-free"
    if source.get("requires_playwright"):
        return [], "requires Playwright; skipped by the basic scanner"
    if is_document_url(source_url):
        if not robots_allowed(source_url, timeout):
            return [], "robots.txt disallows the approved document URL"
        return [
            _file_record(
                file_url=source_url,
                title=str(source.get("title") or ""),
                context="approved direct document",
                page_text="",
                page_url=source_url,
                source=source,
                queries=queries,
                now=now,
            )
        ], None

    page_queue = [source_url]
    visited: set[str] = set()
    seen_files: set[str] = set()
    findings: list[dict[str, Any]] = []
    while page_queue and len(visited) < max_pages and len(findings) < max_files:
        page_url = page_queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        if not robots_allowed(page_url, timeout):
            if page_url == source_url:
                return findings, "robots.txt disallows the approved source"
            continue
        try:
            final_url, _, html = _safe_get(page_url, timeout, MAX_HTML_BYTES)
        except (requests.RequestException, ValueError) as exc:
            if page_url == source_url:
                return findings, f"{type(exc).__name__}: {str(exc)[:180]}"
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        page_text = soup.get_text(" ", strip=True)[:80_000]
        captcha, login, paywall = detect_restricted_access(page_text)
        if captcha:
            return findings, "CAPTCHA detected; source was not traversed"
        if login or paywall:
            return findings, "login-protected or paywalled source was not traversed"

        for anchor in soup.find_all("a", href=True):
            candidate = normalize_url(urljoin(final_url, anchor.get("href", "")))
            if not candidate or not _allowed_internal_url(source_url, candidate):
                continue
            title = anchor.get_text(" ", strip=True) or anchor.get("title", "").strip()
            container = anchor.find_parent(["tr", "li", "article"])
            context = container.get_text(" ", strip=True)[:1_500] if container else title
            if is_document_url(candidate):
                if candidate in seen_files or not robots_allowed(candidate, timeout):
                    continue
                findings.append(
                    _file_record(
                        file_url=candidate,
                        title=title,
                        context=context,
                        page_text=f"{page_title} {page_text}",
                        page_url=final_url,
                        source=source,
                        queries=queries,
                        now=now,
                    )
                )
                seen_files.add(candidate)
                if len(findings) >= max_files:
                    break
            elif (
                candidate not in visited
                and candidate not in page_queue
                and _relevant_page(candidate, f"{title} {context}", queries)
                and len(page_queue) + len(visited) < max_pages
            ):
                page_queue.append(candidate)
    return findings, None


def _merge_finding(
    current: dict[str, Any], incoming: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(incoming)
    merged["discovered_at"] = (
        current.get("discovered_at") or incoming.get("discovered_at")
    )
    if str(current.get("status")) in {"extracted", "rejected"}:
        merged["status"] = current["status"]
    return merged


def write_local_findings(
    findings: Iterable[dict[str, Any]],
    output_path: Path = FILES_FALLBACK,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in _read_list(output_path):
        key = normalize_url(str(item.get("file_url", "")))
        if key:
            merged[key] = item
    for item in findings:
        key = normalize_url(str(item.get("file_url", "")))
        if not key:
            continue
        merged[key] = (
            _merge_finding(merged[key], item) if key in merged else item
        )
    records = sorted(
        merged.values(),
        key=lambda item: (
            str(item.get("status")) != "pending_review",
            -int(item.get("confidence_score") or 0),
            str(item.get("file_url") or ""),
        ),
    )
    _write_list(output_path, records)
    return records


def _existing_file_state(client: Any) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    offset, batch_size = 0, 1_000
    while True:
        rows = (
            client.table("discovered_files")
            .select("file_url,discovered_at,status")
            .order("file_url")
            .range(offset, offset + batch_size - 1)
            .execute()
            .data
            or []
        )
        for item in rows:
            key = normalize_url(str(item.get("file_url", "")))
            if key:
                existing[key] = item
        if len(rows) < batch_size:
            break
        offset += batch_size
    return existing


def sync_findings_to_supabase(
    findings: Iterable[dict[str, Any]], *, client: Any | None = None
) -> tuple[str, int, str]:
    key_label = "provided client"
    if client is None:
        url, key, configured, key_label = _supabase_credentials()
        if not configured:
            return "skipped", 0, "Supabase credentials are not configured"
        if not (url and key):
            return "failed", 0, "Supabase discovered-file credentials are incomplete"
        try:
            from supabase import create_client

            client = create_client(url, key)
        except Exception as exc:
            return "failed", 0, f"{type(exc).__name__}: {str(exc)[:200]}"
    try:
        existing = _existing_file_state(client)
        rows: list[dict[str, Any]] = []
        for item in findings:
            key = normalize_url(str(item.get("file_url", "")))
            if not key:
                continue
            row = {field: item.get(field) for field in FILE_FIELDS}
            previous = existing.get(key, {})
            row["file_url"] = key
            row["discovered_at"] = (
                previous.get("discovered_at") or row.get("discovered_at")
            )
            if str(previous.get("status")) in {"extracted", "rejected"}:
                row["status"] = previous["status"]
            rows.append(row)
        for start in range(0, len(rows), SUPABASE_BATCH_SIZE):
            (
                client.table("discovered_files")
                .upsert(
                    rows[start : start + SUPABASE_BATCH_SIZE],
                    on_conflict="file_url",
                )
                .execute()
            )
        return "synced", len(rows), f"using {key_label}"
    except Exception as exc:
        return "failed", 0, f"{type(exc).__name__}: {str(exc)[:200]}"


def run_approved_scan(
    sources: list[dict[str, Any]],
    *,
    timeout: float,
    workers: int,
    max_sources: int,
    max_pages_per_source: int,
    max_files: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    active = sorted(
        (item for item in sources if _active_source(item)),
        key=lambda item: str(item.get("source_id") or item.get("url") or ""),
    )[: max(0, max_sources)]
    queries = load_discovery_queries()
    now = datetime.now(timezone.utc)
    per_source_limit = min(
        max_files,
        max(10, ((max_files + max(1, len(active)) - 1) // max(1, len(active))) * 3),
    )
    findings: list[dict[str, Any]] = []
    failures: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 12))) as executor:
        futures = {
            executor.submit(
                scan_approved_source,
                source,
                timeout=timeout,
                max_pages=max_pages_per_source,
                max_files=per_source_limit,
                queries=queries,
                now=now,
            ): source
            for source in active
        }
        for future in as_completed(futures):
            source = futures[future]
            source_id = str(source.get("source_id") or source.get("url") or "unknown")
            try:
                found, error = future.result()
                findings.extend(found)
                if error:
                    failures[source_id] = error
            except Exception as exc:
                failures[source_id] = f"{type(exc).__name__}: {str(exc)[:180]}"

    unique: dict[str, dict[str, Any]] = {}
    for item in findings:
        key = normalize_url(str(item.get("file_url", "")))
        if key and (
            key not in unique
            or int(item.get("confidence_score") or 0)
            > int(unique[key].get("confidence_score") or 0)
        ):
            unique[key] = item
    ranked = sorted(
        unique.values(),
        key=lambda item: (
            -int(item.get("confidence_score") or 0),
            str(item.get("file_url") or ""),
        ),
    )
    return ranked[: max(0, max_files)], failures


def _positive_env_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        number = int(value)
    except ValueError:
        return None
    return number if number > 0 else None


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan approved sources into a private file review queue."
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--source-limit", type=int, default=None)
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--max-pages-per-source", type=int, default=None)
    parser.add_argument("--approved-input", type=Path, default=APPROVED_FALLBACK)
    parser.add_argument("--output", type=Path, default=FILES_FALLBACK)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    mode = os.getenv("OPPORTA_APPROVED_SCAN_MODE", "full").strip().lower()
    max_sources = (
        args.source_limit
        or _positive_env_int("OPPORTA_APPROVED_MAX_SOURCES")
        or (25 if mode == "basic" else 50)
    )
    max_files = (
        args.max_files
        or _positive_env_int("OPPORTA_APPROVED_MAX_FILES")
        or (300 if mode == "basic" else 500)
    )
    max_pages = (
        args.max_pages_per_source
        or _positive_env_int("OPPORTA_APPROVED_MAX_PAGES_PER_SOURCE")
        or (2 if mode == "basic" else 3)
    )
    sources, backend, load_error = load_approved_sources(
        fallback_path=args.approved_input
    )
    if load_error:
        print(f"Approved source load failed safely: {load_error}")
        return 1
    findings, failures = run_approved_scan(
        sources,
        timeout=max(1.0, args.timeout),
        workers=args.workers,
        max_sources=max_sources,
        max_pages_per_source=max_pages,
        max_files=max_files,
    )
    local_records = write_local_findings(findings, args.output)
    sync_status, sync_count, sync_detail = sync_findings_to_supabase(findings)
    if sync_status == "failed":
        print(f"Discovered-file Supabase sync failed safely: {sync_detail}")
        print(f"Local review fallback: {args.output}")
        return 1
    print(
        f"Approved source scan complete: {len(sources)} active source(s), "
        f"{len(findings)} file candidate(s), {len(failures)} isolated failure(s)."
    )
    if sync_status == "synced":
        print(
            f"Supabase: upserted {sync_count} finding(s) into "
            f"public.discovered_files ({sync_detail})."
        )
    else:
        print("Supabase: not configured; local review fallback remains active.")
    print(
        f"Local review fallback: {args.output} "
        f"({len(local_records)} total queued record(s)); source backend: {backend}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
