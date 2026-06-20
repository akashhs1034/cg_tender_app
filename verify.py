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
    fail("SUPABASE_URL is not set (still has placeholder value)")
else:
    ok(f"SUPABASE_URL  = {url}")

if not key or "YOUR-SERVICE-KEY" in key:
    fail("SUPABASE_KEY is not set (still has placeholder value)")
elif key.startswith("sb_publishable_"):
    fail(
        "SUPABASE_KEY is a publishable/anon key - upserts WILL fail.\n"
        "        Dashboard -> Project Settings -> API -> service_role (secret key)."
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
        browser = pw.chromium.launch(headless=True)
        browser.close()
    ok("Chromium browser launches OK")
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
# Summary
# ---------------------------------------------------------------------------
print("\n" + "-" * 60)
if _FAILURES:
    print(f"  {len(_FAILURES)} check(s) FAILED - fix above before launching.\n")
    sys.exit(1)
else:
    print("  All checks passed. Launch with:\n")
    print("    py -m streamlit run app.py\n")
