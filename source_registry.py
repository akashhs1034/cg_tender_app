"""Persisted source inventory and health updates for the Phase 3 pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
BASE_REGISTRY = ROOT / "sources_registry.json"
NEWSPAPER_REGISTRY = ROOT / "newspaper_sources.json"
RUNTIME_REGISTRY = DATA / "sources_registry.json"

REGISTRY_FIELDS = (
    "source_id", "source_name", "state", "district", "source_type",
    "category", "url", "discovery_url", "scraper_module", "active",
    "requires_ocr", "requires_playwright", "requires_manual_review",
    "last_success_at", "last_error", "last_count", "notes",
)


def _read_list(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _normalise(source: dict) -> dict:
    defaults = {
        "source_id": "", "source_name": "", "state": None, "district": None,
        "source_type": "portal", "category": "both", "url": "",
        "discovery_url": None, "scraper_module": None, "active": True,
        "requires_ocr": False, "requires_playwright": False,
        "requires_manual_review": False, "last_success_at": None,
        "last_error": None, "last_count": 0, "notes": None,
    }
    defaults.update({key: source.get(key) for key in REGISTRY_FIELDS
                     if key in source})
    # Keep acquisition configuration used by newspaper_sources.json.
    for key in ("urls", "kind", "epaper_fn", "max_assets", "page_images",
                "base_url"):
        if key in source:
            defaults[key] = source[key]
    return defaults


def load_registry(include_districts: bool = True,
                  include_newspapers: bool = True) -> list[dict]:
    """Load the versioned seeds and expand every CG/UP district source."""
    sources = [_normalise(item) for item in _read_list(BASE_REGISTRY)]
    if include_newspapers:
        sources.extend(_normalise(item) for item in _read_list(NEWSPAPER_REGISTRY))
    if include_districts:
        from scrapers.district_notices import (
            NOTICE_PATHS, authority_site_catalog, district_site_catalog,
        )

        for site in district_site_catalog():
            sources.append(_normalise({
                "source_id": site["source_id"],
                "source_name": site["source_name"],
                "state": site["state"],
                "district": site["district"],
                "source_type": "district_site",
                "category": "both",
                "url": site["base_url"],
                "discovery_url": site["base_url"].rstrip("/") + NOTICE_PATHS[0],
                "scraper_module": "scrapers.district_notices",
                "active": True,
                "requires_ocr": False,
                "requires_playwright": False,
                "requires_manual_review": False,
                "notes": "Auto-discovers all common S3WaaS notice-category paths.",
                "base_url": site["base_url"],
            }))
        for authority in authority_site_catalog():
            sources.append(_normalise({
                "source_id": authority["source_id"],
                "source_name": authority["source_name"],
                "state": authority["state"],
                "district": authority["district"],
                "source_type": "department_site",
                "category": "tender",
                "url": authority["url"],
                "discovery_url": authority["url"],
                "scraper_module": "scrapers.district_notices",
                "active": True,
                "requires_ocr": False,
                "requires_playwright": False,
                "requires_manual_review": False,
                "notes": "Public authority tender listing.",
            }))

    # Runtime telemetry survives across runs, while versioned configuration wins.
    previous = {
        item.get("source_id"): item for item in _read_list(RUNTIME_REGISTRY)
        if item.get("source_id")
    }
    telemetry = ("last_success_at", "last_error", "last_count")
    unique: dict[str, dict] = {}
    for source in sources:
        source_id = source.get("source_id")
        if not source_id:
            continue
        old = previous.get(source_id, {})
        for key in telemetry:
            if key in old:
                source[key] = old[key]
        unique[source_id] = source
    return list(unique.values())


def apply_health(registry: list[dict], report: dict[str, dict]) -> list[dict]:
    """Apply one ingest run's source report without erasing prior successes."""
    now = datetime.now(timezone.utc).isoformat()
    for source in registry:
        result = report.get(source["source_id"])
        if result is None:
            continue
        count = int(result.get("count", result.get("record_count", 0)) or 0)
        error = result.get("error")
        if not error and result.get("errors"):
            error = "; ".join(
                str(item.get("error") if isinstance(item, dict) else item)
                for item in result["errors"][:3])
        source["last_count"] = count
        source["last_error"] = str(error)[:1000] if error else None
        if str(result.get("status", "")).lower() in {
                "healthy", "ok", "no_records", "warning"}:
            source["last_success_at"] = now
    return registry


def write_registry(registry: list[dict]) -> Path:
    DATA.mkdir(exist_ok=True)
    RUNTIME_REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return RUNTIME_REGISTRY
