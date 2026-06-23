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

import argparse
import os
import re
import csv
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

import core

_PRIVATE_ORG = re.compile(
    r"\b(hospitals?|pvt\.?|limited|ltd\.?|private|corporate)\b", re.I
)

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
            if _PRIVATE_ORG.search(str(r.get("organization", ""))):
                continue  # skip private company postings
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

    from scrapers import (
        cg_eproc, up_etender, cppp_state, cg_jobs, up_jobs,
        cg_vyapam, up_upsssc, cspdcl,
        gem, secl, pwd_cg, uppcl, cppp_central, dprcg,
    )

    # cppp_cg: reuse cppp_state module with CG env override
    import os as _os
    def _cppp_cg_scrape():
        prev = _os.environ.get("CPPP_STATE")
        _os.environ["CPPP_STATE"] = "Chhattisgarh"
        try:
            # re-import to pick up new env var
            import importlib
            import scrapers.cppp_state as _cppp
            importlib.reload(_cppp)
            return _cppp.scrape()
        finally:
            if prev is None:
                _os.environ.pop("CPPP_STATE", None)
            else:
                _os.environ["CPPP_STATE"] = prev

    _TENDER_SCRAPERS = [
        ("cg_eproc     (eproc.cgstate.gov.in)      ", cg_eproc.scrape),
        ("up_etender   (etender.up.nic.in)         ", up_etender.scrape),
        ("cppp_up      (eprocure.gov.in/cppp - UP) ", cppp_state.scrape),
        ("cppp_cg      (eprocure.gov.in/cppp - CG) ", _cppp_cg_scrape),
        ("cspdcl       (cspdcl.co.in/cseb)         ", cspdcl.scrape),
        ("secl         (secl-cil.in)               ", secl.scrape),
        ("pwd_cg       (pwd.cg.gov.in)             ", pwd_cg.scrape),
        ("uppcl        (uppclonline.com)            ", uppcl.scrape),
        ("gem          (gem.gov.in)                ", gem.scrape),
        ("cppp_central (eprocure.gov.in - central) ", cppp_central.scrape),
        ("dprcg        (dprcg.gov.in - DPR/Samvad)  ", dprcg.scrape),
    ]
    _JOB_SCRAPERS = [
        ("cg_jobs      (psc.cg.gov.in)             ", cg_jobs.scrape),
        ("cg_vyapam    (vyapamcg.cgstate.gov.in)   ", cg_vyapam.scrape),
        ("up_jobs      (uppsc.up.nic.in)           ", up_jobs.scrape),
        ("up_upsssc    (upsssc.gov.in)             ", up_upsssc.scrape),
    ]

    for label, fn in _TENDER_SCRAPERS:
        batch = fn()
        tenders += batch
        counts[label] = len(batch)

    for label, fn in _JOB_SCRAPERS:
        batch = fn()
        jobs += batch
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
    url = os.getenv("SUPABASE_URL")
    # Prefer service_role key for ingest (bypasses RLS); fall back to anon key
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not (url and key):
        print("   Supabase keys not set — skipping cloud push (local CSVs are ready).")
        return
    using_service = bool(os.getenv("SUPABASE_SERVICE_KEY"))
    if not using_service:
        print("   Note: using anon key — add SUPABASE_SERVICE_KEY to .env to bypass RLS.")
    try:
        from supabase import create_client
        sb = create_client(url, key)
        for table, rows in [("tenders", tenders), ("jobs", jobs)]:
            if not rows:
                continue
            # Chunk upserts to avoid request-size limits
            chunk = 200
            for i in range(0, len(rows), chunk):
                sb.table(table).upsert(rows[i:i+chunk], on_conflict="source_id").execute()
            print(f"   upserted {len(rows)} rows -> {table}")
        _cleanup_expired(sb)
    except Exception as e:
        print(f"   Supabase push failed: {e}")
        print("   Local CSVs are up-to-date — app will use them as fallback.")


def push_corrigendums(corrigs):
    """Upsert scraped corrigendums to Supabase; clean ones whose closing date passed."""
    if not corrigs:
        print("   corrigendums: none scraped — skipping push.")
        return
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not (url and key):
        print("   corrigendums: Supabase keys not set — skipping push.")
        return
    try:
        from supabase import create_client
        sb = create_client(url, key)
        chunk = 200
        for i in range(0, len(corrigs), chunk):
            sb.table("corrigendums").upsert(corrigs[i:i+chunk], on_conflict="source_id").execute()
        print(f"   upserted {len(corrigs)} rows -> corrigendums")
        # Drop corrigendums whose bid-closing date passed > 3 days ago
        from datetime import timedelta
        cutoff = (date.today() - timedelta(days=3)).isoformat()
        try:
            resp = (sb.table("corrigendums").delete()
                      .lt("closing_date", cutoff)
                      .not_.is_("closing_date", "null").execute())
            n = len(resp.data) if resp.data else 0
            if n:
                print(f"   cleaned {n} expired corrigendums")
        except Exception as e:
            print(f"   corrigendum cleanup warning: {e}")
    except Exception as e:
        print(f"   corrigendums push failed: {e}")


def push_offline_tenders(offline):
    """Upsert district-collectorate offline tenders; clean ones long expired."""
    if not offline:
        print("   offline tenders: none scraped — skipping push.")
        return
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not (url and key):
        print("   offline tenders: Supabase keys not set — skipping push.")
        return
    try:
        from supabase import create_client
        sb = create_client(url, key)
        chunk = 200
        for i in range(0, len(offline), chunk):
            sb.table("offline_tenders").upsert(offline[i:i+chunk], on_conflict="source_id").execute()
        print(f"   upserted {len(offline)} rows -> offline_tenders")
        # Drop offline tenders whose closing date passed > 3 days ago.
        from datetime import timedelta
        cutoff = (date.today() - timedelta(days=3)).isoformat()
        try:
            resp = (sb.table("offline_tenders").delete()
                      .lt("deadline", cutoff)
                      .not_.is_("deadline", "null").execute())
            n = len(resp.data) if resp.data else 0
            if n:
                print(f"   cleaned {n} expired offline tenders")
        except Exception as e:
            print(f"   offline tender cleanup warning: {e}")
    except Exception as e:
        print(f"   offline tenders push failed: {e}")


def _cleanup_expired(sb):
    """Delete records whose deadline passed more than 3 days ago from Supabase."""
    from datetime import timedelta
    cutoff = (date.today() - timedelta(days=3)).isoformat()
    for table in ("tenders", "jobs"):
        try:
            resp = (sb.table(table)
                      .delete()
                      .lt("deadline", cutoff)
                      .not_.is_("deadline", "null")
                      .execute())
            deleted = len(resp.data) if resp.data else 0
            if deleted:
                print(f"   cleaned {deleted} expired rows from {table}")
        except Exception as e:
            print(f"   cleanup warning ({table}): {e}")


def _print_scraper_summary(counts: dict, total_tenders: int, total_jobs: int) -> None:
    """Print a formatted per-scraper table and emit GitHub Actions warnings for zeros."""
    bar = "=" * 60
    print(f"\n{bar}")
    print("  SCRAPER SUMMARY")
    print(bar)
    for label, n in counts.items():
        flag = "  [OK]" if n > 0 else "  [WARN] 0 RESULTS"
        print(f"  {label}: {n:>4} records{flag}")
    print(bar)
    print(f"  Total after dedup : {total_tenders} tenders, {total_jobs} jobs")
    print(f"{bar}\n")

    # GitHub Actions workflow commands — no-ops outside of CI
    for label, n in counts.items():
        if n == 0:
            short = label.split("(")[0].strip()
            print(f"::warning::{short} returned 0 results - check portal availability")


def main():
    ap = argparse.ArgumentParser(description="Opporta ingestion pipeline")
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Scrape and deduplicate but do not write CSV, push to Supabase, or send emails.",
    )
    ap.add_argument(
        "--no-alerts", action="store_true",
        help="Normal pipeline run (write + push) but skip sending email alerts.",
    )
    args = ap.parse_args()

    if args.dry_run:
        print("=== Opporta ingestion [DRY RUN -- no writes, no emails] ===")
    else:
        print("=== Opporta ingestion ===")

    print("1. Loading seed data...")
    t1, j1 = load_master_leads()
    t2 = load_master_tenders()

    print("2. Running live scrapers...")
    t3, j3, scraper_counts = run_live_scrapers()

    tenders = dedup(t1 + t2 + t3)
    jobs    = dedup(j1 + j3)

    print("2b. Scraping tender corrigendums (amendments)...")
    try:
        from scrapers import cppp_corrigendum
        corrigs = dedup(cppp_corrigendum.scrape())
    except Exception as e:
        print(f"   corrigendum scrape failed: {e}")
        corrigs = []
    scraper_counts["cppp_corrig  (eprocure.gov.in/cppp)     "] = len(corrigs)

    print("2c. Scraping district-collectorate OFFLINE tenders...")
    try:
        from scrapers import district_notices
        offline = dedup(district_notices.scrape())
    except Exception as e:
        print(f"   offline tender scrape failed: {e}")
        offline = []
    scraper_counts["district_off (CG/UP collectorate sites)  "] = len(offline)

    _print_scraper_summary(scraper_counts, len(tenders), len(jobs))

    if args.dry_run:
        print("3. [DRY RUN] Skipping CSV write.")
        print("4. [DRY RUN] Skipping Supabase push.")
    else:
        print("3. Writing local fallback...")
        write_local(tenders, jobs)
        print("4. Pushing to cloud...")
        push_supabase(tenders, jobs)
        push_corrigendums(corrigs)
        push_offline_tenders(offline)

    if args.dry_run or args.no_alerts:
        label = "DRY RUN" if args.dry_run else "--no-alerts"
        print(f"5. [{label}] Skipping email alerts.")
    else:
        print("5. Sending email alerts...")
        from alerts import send_alerts
        import logging
        logging.basicConfig(level=logging.INFO, format="   %(message)s")
        n = send_alerts(tenders)
        if n:
            print(f"   {n} digest email(s) queued.")
        else:
            print("   No new matches to alert (or RESEND_API_KEY not set).")

    print("=== done ===")


if __name__ == "__main__":
    main()
