"""verify.py - pre-flight checks for Opporta.

Run:  python verify.py
All lines should end in  [OK]. Fix any [FAIL] before launching.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def ok(msg):   print(f"  {PASS}  {msg}")
def fail(msg): print(f"  {FAIL}  {msg}"); _FAILURES.append(msg)
def warn(msg): print(f"  {WARN}  {msg}")

_FAILURES: list[str] = []


# ---------------------------------------------------------------------------
# 1. .env -- credentials
# ---------------------------------------------------------------------------
print("\n-- .env credentials --------------------------------------------------")

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")

if not url or "YOUR-PROJECT" in url:
    warn("SUPABASE_URL is not set - local CSV fallback remains available")
else:
    ok("SUPABASE_URL is configured")

if not key or "YOUR-SERVICE-KEY" in key:
    warn("SUPABASE_KEY is not set - cloud reads/writes will be skipped")
elif key.startswith("sb_publishable_"):
    warn(
        "SUPABASE_KEY is publishable/anon - app reads work; configure "
        "SUPABASE_SERVICE_KEY for ingestion writes"
    )
elif not key.startswith("eyJ"):
    warn("SUPABASE_KEY format unexpected (expected JWT starting with 'eyJ') - double-check it")
else:
    ok(f"SUPABASE_KEY  = {key[:20]}...")

anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
if not anthropic_key:
    warn("ANTHROPIC_API_KEY not set - AI resume analysis disabled (app still works)")
else:
    ok(f"ANTHROPIC_API_KEY = {anthropic_key[:10]}...")


# ---------------------------------------------------------------------------
# 2. Python packages
# ---------------------------------------------------------------------------
print("\n-- Python packages ---------------------------------------------------")

REQUIRED = [
    ("streamlit",           "streamlit"),
    ("pandas",              "pandas"),
    ("dotenv",              "python-dotenv"),
    ("dateutil",            "python-dateutil"),
    ("supabase",            "supabase"),
    ("requests",            "requests"),
    ("bs4",                 "beautifulsoup4"),
    ("pdfplumber",          "pdfplumber"),
    ("anthropic",           "anthropic"),
    ("playwright.sync_api", "playwright"),
]

for module, pkg in REQUIRED:
    try:
        importlib.import_module(module)
        ok(pkg)
    except ImportError:
        fail(f"{pkg} not installed  ->  pip install {pkg}")


# ---------------------------------------------------------------------------
# 3. Playwright browser
# ---------------------------------------------------------------------------
print("\n-- Playwright --------------------------------------------------------")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
            browser.close()
            ok("Playwright-managed Chromium browser launches OK")
        except Exception as bundled_exc:
            # Developer machines often have Chrome but have not downloaded
            # Playwright's pinned binary. CI still installs pinned Chromium.
            browser = pw.chromium.launch(channel="chrome", headless=True)
            browser.close()
            warn(
                "Playwright-managed Chromium is not installed locally; "
                "system Chrome launches successfully (CI installs Chromium)"
            )
except Exception as exc:
    fail(f"Playwright/Chromium failed: {exc}\n        Run:  python -m playwright install chromium")


# ---------------------------------------------------------------------------
# 4. Schema file
# ---------------------------------------------------------------------------
print("\n-- Schema ------------------------------------------------------------")
schema = Path("schema.sql")
if schema.exists():
    ok("schema.sql found - paste its contents into Supabase -> SQL Editor -> Run")
else:
    fail("schema.sql not found - cannot create Supabase tables")


# ---------------------------------------------------------------------------
# 5. Supabase connection
# ---------------------------------------------------------------------------
print("\n-- Supabase connection -----------------------------------------------")
if url and key and "YOUR-PROJECT" not in url and not key.startswith("sb_publishable_"):
    try:
        from supabase import create_client
        sb = create_client(url, key)

        t_resp = sb.table("tenders").select("source_id", count="exact").limit(1).execute()
        j_resp = sb.table("jobs").select("source_id", count="exact").limit(1).execute()
        ok(f"tenders table reachable - {t_resp.count} rows")
        ok(f"jobs    table reachable - {j_resp.count} rows")

        TEST_ID = "__verify_test_row__"
        try:
            sb.table("tenders").upsert(
                {"source_id": TEST_ID, "title": "verify test"},
                on_conflict="source_id",
            ).execute()
            sb.table("tenders").delete().eq("source_id", TEST_ID).execute()
            ok("service key has WRITE access (upsert + delete worked)")
        except Exception as exc:
            fail(f"Write test failed - service key may be wrong: {exc}")
    except Exception as exc:
        fail(f"Cannot connect to Supabase: {exc}")
else:
    warn("Skipping Supabase connection check (credentials not ready)")


# ---------------------------------------------------------------------------
# 6. Local CSV fallback
# ---------------------------------------------------------------------------
print("\n-- Local data --------------------------------------------------------")
data = Path("data")
for name in ("tenders.csv", "jobs.csv"):
    p = data / name
    if p.exists():
        import csv
        with open(p, newline="", encoding="utf-8") as f:
            rows = sum(1 for _ in csv.reader(f)) - 1
        ok(f"data/{name} - {rows} rows (local fallback ready)")
    else:
        warn(f"data/{name} not found - run  python ingest.py  to generate it")


# ---------------------------------------------------------------------------
# 7. Phase 3 registries and runtime outputs
# ---------------------------------------------------------------------------
print("\n-- Phase 3 data engine -----------------------------------------------")
try:
    import json
    import source_registry

    registry = source_registry.load_registry()
    missing = [
        item.get("source_id", "<unnamed>") for item in registry
        if not set(source_registry.REGISTRY_FIELDS).issubset(item)
    ]
    if not registry:
        fail("source registry is empty")
    elif missing:
        fail(f"{len(missing)} registry entries are missing required fields")
    else:
        ok(f"source registry - {len(registry)} configured sources")
    if Path("newspaper_sources.json").exists():
        papers = json.loads(Path("newspaper_sources.json").read_text(encoding="utf-8"))
        ok(f"newspaper registry - {len(papers)} configured sources")
    else:
        fail("newspaper_sources.json not found")
    queue_path = data / "manual_review_queue.json"
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        ok(f"manual review queue - {int(queue.get('count', 0))} pending")
    else:
        warn("manual review queue not generated - run python ingest.py")
except Exception as exc:
    fail(f"Phase 3 registry validation failed: {exc}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "-" * 60)
if _FAILURES:
    print(f"  {len(_FAILURES)} check(s) FAILED - fix above before launching.\n")
    sys.exit(1)
else:
    print("  All checks passed. Launch with:\n")
    print("    py -m streamlit run app.py\n")
