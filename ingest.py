"""
ingest.py — the ONE pipeline.

Replaces master_pipeline.py, engine.py, scraper_entry.py and the gspread half of
spider.py. It:
  1. reads seed CSVs (your existing real-ish data) into the unified schema,
  2. (optionally) runs registered live scrapers,
  3. de-duplicates by source_id,
  4. writes data/tenders.csv + data/jobs.csv so the app works with NO database,
  5. upserts to Supabase if SUPABASE_URL / SUPABASE_KEY are set.

Run:  python ingest.py
"""

from __future__ import annotations

import os
import csv
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

import core

load_dotenv()

ROOT = Path(__file__).parent
SEED = ROOT / "seed"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Seed loaders — map each historical CSV into the unified shape
# ---------------------------------------------------------------------------
def _read_csv(name) -> list[dict]:
    path = SEED / name
    if not path.exists():
        print(f"   (skipped {name} — not found)")
        return []
    return pd.read_csv(path).fillna("").to_dict("records")


def load_master_leads():
    tenders, jobs = [], []
    for r in _read_csv("master_leads.csv"):
        is_job = "/mo" in str(r.get("project_value", "")) or r.get("category") == "Government Jobs"
        if is_job:
            jobs.append(core.job_record(
                title=r.get("title"), state=r.get("state"),
                department=r.get("organization"), salary=r.get("project_value"),
                deadline=r.get("deadline"), qualification=r.get("detailed_requirements"),
                description=r.get("description"), document_url=r.get("direct_url"),
                ai_score=core.parse_int(r.get("ai_score")),
                source_portal="seed:master_leads",
            ))
        else:
            tenders.append(core.tender_record(
                title=r.get("title"), state=r.get("state"),
                organization=r.get("organization"), category=r.get("category"),
                value_text=r.get("project_value"), deadline=r.get("deadline"),
                emd=r.get("emd"), contractor_class=r.get("contractor_class"),
                experience=r.get("experience"), eligibility=r.get("eligibility"),
                description=r.get("description"), requirements=r.get("detailed_requirements"),
                document_url=r.get("direct_url"),
                ai_score=core.parse_int(r.get("ai_score")),
                source_portal="seed:master_leads",
            ))
    return tenders, jobs


def load_master_tenders():
    out = []
    for r in _read_csv("master_tenders.csv"):
        out.append(core.tender_record(
            title=f"{r.get('work_category','Tender')} — {r.get('department','')}".strip(" —"),
            state=r.get("state"), organization=r.get("department"),
            category=r.get("work_category"), district=r.get("location_district"),
            value_lakhs=core.parse_value_to_lakhs(r.get("estimated_value_lakhs")),
            deadline=r.get("closing_deadline"),
            source_portal="seed:master_tenders",
        ))
    return out


def load_master_jobs():
    out = []
    for r in _read_csv("master_jobs.csv"):
        out.append(core.job_record(
            title=r.get("job_title"), state=r.get("state"),
            department=r.get("department"), vacancies=r.get("vacancies"),
            qualification=r.get("qualification"), deadline=r.get("deadline"),
            source_portal="seed:master_jobs",
        ))
    return out


# ---------------------------------------------------------------------------
# 2. Live scrapers — plug real ones in here as you build them
# ---------------------------------------------------------------------------
def run_live_scrapers():
    """Return (tenders, jobs, counts) from live sources.

    counts is an OrderedDict mapping scraper_label -> int so the caller can
    print a summary and emit GitHub Actions warnings for zero-result scrapers.
    A broken scraper returns [] — it never crashes the whole pipeline.
    """
    from collections import OrderedDict
    tenders: list[dict] = []
    jobs: list[dict] = []
    counts: OrderedDict[str, int] = OrderedDict()

    from scrapers import cg_eproc, up_etender, cppp_state

    _SCRAPERS = [
        ("cg_eproc     (eproc.cgstate.gov.in) ", cg_eproc.scrape),
        ("up_etender   (etender.up.nic.in)    ", up_etender.scrape),
        ("cppp_state   (eprocure.gov.in/cppp) ", cppp_state.scrape),
    ]

    for label, fn in _SCRAPERS:
        batch = fn()
        tenders += batch
        counts[label] = len(batch)

    return tenders, jobs, counts


# ---------------------------------------------------------------------------
# 3. Dedup + persist
# ---------------------------------------------------------------------------
def dedup(records):
    seen, out = set(), []
    for rec in records:
        if rec["source_id"] in seen:
            continue
        seen.add(rec["source_id"])
        out.append(rec)
    return out


def write_local(tenders, jobs):
    for name, rows in [("tenders", tenders), ("jobs", jobs)]:
        if not rows:
            continue
        keys = sorted({k for row in rows for k in row})
        with open(DATA / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"   wrote data/{name}.csv ({len(rows)} rows)")


def push_supabase(tenders, jobs):
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not (url and key):
        print("   Supabase keys not set — skipping cloud push (local CSVs are ready).")
        return
    from supabase import create_client
    sb = create_client(url, key)
    for table, rows in [("tenders", tenders), ("jobs", jobs)]:
        if not rows:
            continue
        # upsert on source_id avoids the duplicate-row problem the old scripts had
        sb.table(table).upsert(rows, on_conflict="source_id").execute()
        print(f"   upserted {len(rows)} rows -> {table}")


def _print_scraper_summary(counts: dict, total_tenders: int, total_jobs: int) -> None:
    """Print a formatted per-scraper table and emit GitHub Actions warnings for zeros."""
    bar = "=" * 60
    print(f"\n{bar}")
    print("  SCRAPER SUMMARY")
    print(bar)
    for label, n in counts.items():
        flag = "  [OK]" if n > 0 else "  [WARN] 0 RESULTS"
        print(f"  {label}: {n:>4} tenders{flag}")
    print(bar)
    print(f"  Total after dedup : {total_tenders} tenders, {total_jobs} jobs")
    print(f"{bar}\n")

    # GitHub Actions workflow commands — no-ops outside of CI
    for label, n in counts.items():
        if n == 0:
            short = label.split("(")[0].strip()
            print(f"::warning::{short} returned 0 results - check portal availability")


def main():
    print("=== Opporta ingestion ===")
    print("1. Loading seed data…")
    t1, j1 = load_master_leads()
    t2 = load_master_tenders()
    j2 = load_master_jobs()

    print("2. Running live scrapers…")
    t3, j3, scraper_counts = run_live_scrapers()

    tenders = dedup(t1 + t2 + t3)
    jobs = dedup(j1 + j2 + j3)

    _print_scraper_summary(scraper_counts, len(tenders), len(jobs))

    print("3. Writing local fallback…")
    write_local(tenders, jobs)

    print("4. Pushing to cloud…")
    push_supabase(tenders, jobs)
    print("=== done ===")


if __name__ == "__main__":
    main()
