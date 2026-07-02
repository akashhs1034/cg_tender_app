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
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

import core
import source_registry

_PRIVATE_ORG = re.compile(
    r"\b(hospitals?|pvt\.?|limited|ltd\.?|private|corporate)\b", re.I
)

load_dotenv()

ROOT = Path(__file__).parent
SEED = ROOT / "seed"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
_LAST_SOURCE_REPORT: dict[str, dict] = {}


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
        gem, secl, pwd_cg, uppcl, cppp_central, dprcg, samvad,
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
        ("samvad       (samvad.cg.nic.in - Samvad)  ", samvad.scrape_tenders),
    ]
    _JOB_SCRAPERS = [
        ("cg_jobs      (psc.cg.gov.in)             ", cg_jobs.scrape),
        ("cg_vyapam    (vyapamcg.cgstate.gov.in)   ", cg_vyapam.scrape),
        ("up_jobs      (uppsc.up.nic.in)           ", up_jobs.scrape),
        ("up_upsssc    (upsssc.gov.in)             ", up_upsssc.scrape),
    ]

    _LAST_SOURCE_REPORT.clear()

    def run_one(label, fn, kind):
        source_id = label.split("(")[0].strip()
        try:
            batch = fn() or []
            if not isinstance(batch, list):
                raise TypeError(f"expected list, got {type(batch).__name__}")
            error = None
            status = "healthy" if batch else "no_records"
        except Exception as exc:
            batch = []
            error = f"{type(exc).__name__}: {exc}"[:1000]
            status = "failed"
            print(f"   {source_id}: failed safely — {error}")
        counts[label] = len(batch)
        _LAST_SOURCE_REPORT[source_id] = {
            "source_id": source_id, "kind": kind, "count": len(batch),
            "status": status, "error": error,
        }
        return batch

    for label, fn in _TENDER_SCRAPERS:
        tenders += run_one(label, fn, "Tender")

    for label, fn in _JOB_SCRAPERS:
        jobs += run_one(label, fn, "Job")

    return tenders, jobs, counts


# ---------------------------------------------------------------------------
# 3. Dedup + persist
# ---------------------------------------------------------------------------
def dedup(records, kind: str = "tender"):
    """Compatibility wrapper around the cross-source provenance-aware merger."""
    return core.merge_duplicate_records(records, kind)


def _csv_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def write_local(tenders, jobs, offline_tenders=None):
    datasets = [
        ("tenders", tenders, core.TENDER_SCHEMA_FIELDS),
        ("jobs", jobs, core.JOB_SCHEMA_FIELDS),
    ]
    if offline_tenders is not None:
        datasets.append(("offline_tenders", offline_tenders,
                         core.TENDER_SCHEMA_FIELDS))
    for name, rows, schema_fields in datasets:
        if name == "offline_tenders":
            rows = [
                {
                    **row,
                    "nit_no": row.get("tender_no") or row.get("nit_no"),
                    "newspaper": (
                        row.get("newspaper_name") or row.get("newspaper")),
                }
                for row in rows
            ]
        keys = list(schema_fields)
        extras = sorted({k for row in rows for k in row if k not in keys})
        keys.extend(extras)
        with open(DATA / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for row in rows:
                w.writerow({key: _csv_value(row.get(key)) for key in keys})
        print(f"   wrote data/{name}.csv ({len(rows)} rows)")


def write_source_health(counts: dict, *, report: dict | None = None,
                        registry: list[dict] | None = None) -> None:
    """Persist the latest per-source counts for the read-only UI dashboard.

    A zero count is reported as ``no_records`` rather than ``failed`` because the
    legacy scraper API returns counts, not structured exceptions. This keeps the
    dashboard factual; a future pipeline can add an ``error`` value per source
    without changing the UI contract.
    """
    report = report or {}
    sources = []
    if registry:
        for item in registry:
            result = report.get(item["source_id"], {})
            status = result.get("status") or (
                "inactive" if not item.get("active", True) else "not_run")
            error = result.get("error")
            if not error and result.get("errors"):
                error = "; ".join(
                    str(e.get("error") if isinstance(e, dict) else e)
                    for e in result["errors"][:3])
            sources.append({
                "source": item["source_id"],
                "display_name": item.get("source_name") or item["source_id"],
                "kind": item.get("category") or "both",
                "source_type": item.get("source_type"),
                "state": item.get("state"), "district": item.get("district"),
                "record_count": int(result.get(
                    "count", result.get("record_count", item.get("last_count", 0))) or 0),
                "status": status, "error": str(error)[:1000] if error else None,
            })
    else:
        for label, count in counts.items():
            source_id = label.split("(")[0].strip()
            result = report.get(source_id, {})
            sources.append({
                "source": source_id,
                "display_name": " ".join(label.split()),
                "kind": ("Job" if source_id in {
                    "cg_jobs", "cg_vyapam", "up_jobs", "up_upsssc"
                } else "Tender"),
                "record_count": int(count),
                "status": result.get(
                    "status", "healthy" if int(count) > 0 else "no_records"),
                "error": result.get("error"),
            })
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "ingest_report",
        "sources": sources,
    }
    path = DATA / "source_health.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   wrote data/source_health.json ({len(sources)} sources)")


def write_manual_review_queue(items: list[dict]) -> None:
    path = DATA / "manual_review_queue.json"
    unique = {
        item.get("queue_id") or core.make_source_id(
            item.get("record_type"), item.get("source_url"),
            (item.get("record") or {}).get("source_id")): item
        for item in items if isinstance(item, dict)
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(unique),
        "items": list(unique.values()),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"   wrote data/manual_review_queue.json ({len(unique)} items)")


def _read_generated(name: str, kind: str) -> list[dict]:
    """Read the prior snapshot so expired opportunities remain archived."""
    path = DATA / f"{name}.csv"
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        normalise = (core.canonicalize_tender_record
                     if kind == "tender" else core.canonicalize_job_record)
        return [normalise(row) for row in rows if row.get("title")]
    except Exception as exc:
        print(f"   archive read warning ({name}): {exc}")
        return []


def _json_safe_row(row: dict) -> dict:
    out = {}
    for key, value in row.items():
        if isinstance(value, float) and pd.isna(value):
            out[key] = None
        elif isinstance(value, (date, datetime)):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


def _upsert_with_schema_fallback(sb, table: str, rows: list[dict],
                                 legacy_fields: set[str]) -> None:
    """Try Phase 3 fields, then retry using the original table schema."""
    rich_schema_supported = True
    chunk_size = 200
    for i in range(0, len(rows), chunk_size):
        chunk = [_json_safe_row(row) for row in rows[i:i + chunk_size]]
        if rich_schema_supported:
            try:
                sb.table(table).upsert(
                    chunk, on_conflict="source_id").execute()
                continue
            except Exception as exc:
                message = str(exc).lower()
                if not any(token in message for token in (
                        "column", "schema cache", "pgrst204", "does not exist")):
                    raise
                rich_schema_supported = False
                print(
                    f"   {table}: Phase 3 columns unavailable; using "
                    f"backward-compatible fields ({type(exc).__name__})")
        legacy = [
            {key: value for key, value in row.items() if key in legacy_fields}
            for row in chunk
        ]
        sb.table(table).upsert(legacy, on_conflict="source_id").execute()


def _upsert_resilient(sb, table: str, rows: list[dict], legacy_fields: set[str]) -> int:
    """Upsert a table so a single bad row (e.g. a secondary unique-constraint
    clash) never aborts the whole batch. Tries chunks, then falls back to
    row-by-row, skipping only the offending rows. Returns rows successfully
    written."""
    ok = 0
    chunk_size = 100
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        try:
            _upsert_with_schema_fallback(sb, table, chunk, legacy_fields)
            ok += len(chunk)
        except Exception:
            for row in chunk:
                try:
                    _upsert_with_schema_fallback(sb, table, [row], legacy_fields)
                    ok += 1
                except Exception:
                    pass  # duplicate / bad row — skip it, keep the rest
    return ok


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
        if tenders:
            _upsert_with_schema_fallback(sb, "tenders", tenders, core.TENDER_DB_FIELDS)
            print(f"   upserted {len(tenders)} rows -> tenders")
        # Jobs have a second unique constraint (source_url, title) besides the
        # source_id PK. A single pre-existing job used to raise and abort the
        # WHOLE jobs batch (0 jobs written for days). Push resiliently so dups
        # are skipped while all genuinely-new jobs still land.
        if jobs:
            ok = _upsert_resilient(sb, "jobs", jobs, core.JOB_DB_FIELDS)
            print(f"   upserted {ok}/{len(jobs)} rows -> jobs")
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
    """Upsert district/newspaper notices using the established offline schema."""
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
        fields = {
            "source_id", "title", "state", "district", "organization", "nit_no",
            "category", "value_text", "value_lakhs", "emd", "published_date",
            "deadline", "opening_date", "newspaper", "document_url",
            "description", "source_portal", "added_by", "scraped_at",
        }
        safe_rows = []
        for row in offline:
            compatible = dict(row)
            compatible["nit_no"] = row.get("tender_no") or row.get("nit_no")
            compatible["newspaper"] = (
                row.get("newspaper_name") or row.get("newspaper"))
            safe_rows.append({
                key: value for key, value in compatible.items() if key in fields
            })
        chunk = 200
        for i in range(0, len(safe_rows), chunk):
            sb.table("offline_tenders").upsert(
                safe_rows[i:i+chunk], on_conflict="source_id").execute()
        print(f"   upserted {len(offline)} rows -> offline_tenders")
    except Exception as e:
        print(f"   offline tenders push failed: {e}")


def _cleanup_expired(sb):
    """Retain history; the public app filters expired deadlines by default."""
    print("   expired records retained internally (public app filters them)")


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


def _canonical_records(records: list[dict], kind: str,
                       source_label: str) -> list[dict]:
    normalise = (core.canonicalize_tender_record
                 if kind == "tender" else core.canonicalize_job_record)
    out = []
    for record in records:
        try:
            out.append(normalise(record))
        except Exception as exc:
            print(
                f"   {source_label}: skipped one invalid {kind} record "
                f"({type(exc).__name__}: {exc})")
    return out


def _merge_health(report: dict[str, dict], source_id: str, result: dict) -> None:
    if source_id not in report:
        report[source_id] = dict(result)
        return
    existing = report[source_id]
    existing["count"] = int(existing.get("count", 0) or 0) + int(
        result.get("count", 0) or 0)
    if result.get("error"):
        existing["error"] = result["error"]
    if result.get("status") == "failed":
        existing["status"] = "failed"


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
    ap.add_argument(
        "--skip-live", action="store_true",
        help="Use seed/archive data only (fast local smoke test; daily runs omit this).",
    )
    args = ap.parse_args()

    if args.dry_run:
        print("=== Opporta ingestion [DRY RUN -- no writes, no emails] ===")
    else:
        print("=== Opporta ingestion ===")

    print("1. Loading source registry and seed data...")
    registry = source_registry.load_registry()
    print(f"   source registry: {len(registry)} configured sources")
    t1, j1 = load_master_leads()
    t2 = load_master_tenders()

    print("2. Running live scrapers...")
    if args.skip_live:
        from collections import OrderedDict
        t3, j3, scraper_counts = [], [], OrderedDict()
        source_report: dict[str, dict] = {}
        print("   skipped by --skip-live")
    else:
        t3, j3, scraper_counts = run_live_scrapers()
        source_report = dict(_LAST_SOURCE_REPORT)

    print("2b. Scraping tender corrigendums (amendments)...")
    if args.skip_live:
        corrigs = []
    else:
        try:
            from scrapers import cppp_corrigendum
            corrigs = cppp_corrigendum.scrape() or []
            corrig_error = None
        except Exception as e:
            print(f"   corrigendum scrape failed safely: {e}")
            corrigs = []
            corrig_error = f"{type(e).__name__}: {e}"[:1000]
        source_report["cppp_corrigendum"] = {
            "source_id": "cppp_corrigendum", "count": len(corrigs),
            "status": ("failed" if corrig_error else
                       "healthy" if corrigs else "no_records"),
            "error": corrig_error,
        }
    scraper_counts["cppp_corrig  (eprocure.gov.in/cppp)     "] = len(corrigs)

    print("2c. Discovering district tenders/jobs across S3WaaS categories...")
    district_tenders, district_jobs = [], []
    if not args.skip_live:
        try:
            from scrapers import district_notices
            district_result = district_notices.collect()
            district_tenders = district_result["tenders"]
            district_jobs = district_result["jobs"]
            source_report.update(district_result.get("report") or {})
        except Exception as exc:
            print(f"   district collector failed safely: {exc}")
    scraper_counts["district     (CG/UP S3WaaS notices)       "] = (
        len(district_tenders) + len(district_jobs))

    print("2d. Collecting public government newspaper/offline notices...")
    newspaper_tenders, newspaper_jobs, manual_review = [], [], []
    if not args.skip_live:
        try:
            from scrapers import newspapers
            newspaper_result = newspapers.collect()
            newspaper_tenders = newspaper_result.get("tenders") or []
            newspaper_jobs = newspaper_result.get("jobs") or []
            manual_review = newspaper_result.get("manual_review") or []
            source_report.update(newspaper_result.get("report") or {})
            print(
                f"   newspapers: {len(newspaper_tenders)} tenders, "
                f"{len(newspaper_jobs)} jobs, "
                f"{len(manual_review)} queued for review")
        except Exception as exc:
            print(f"   newspaper collector failed safely: {exc}")
    scraper_counts["newspapers   (public PDF/image OCR)        "] = (
        len(newspaper_tenders) + len(newspaper_jobs))

    if not args.skip_live:
        try:
            from scrapers import discovery
            discovery.discover()   # weekly-guarded; appends new URLs to ai_sources.json
        except Exception as exc:
            print(f"   discovery failed safely: {exc}")

    print("2e. AI-extracting from config-driven sources (data/ai_sources.json)...")
    ai_tenders, ai_jobs = [], []
    if not args.skip_live:
        try:
            from scrapers import generic_ai
            ai_result = generic_ai.collect()
            ai_tenders = ai_result.get("tenders") or []
            ai_jobs = ai_result.get("jobs") or []
            source_report.update(ai_result.get("report") or {})
        except Exception as exc:
            print(f"   generic_ai collector failed safely: {exc}")
    scraper_counts["generic_ai   (config AI extractor)         "] = (
        len(ai_tenders) + len(ai_jobs))

    samvad_offline = []
    if not args.skip_live:
        try:
            from scrapers import samvad as _samvad
            samvad_offline = _samvad.scrape_published_ads() or []
            samvad_error = None
        except Exception as exc:
            samvad_error = f"{type(exc).__name__}: {exc}"[:1000]
            print(f"   samvad newspaper-ad scrape failed safely: {samvad_error}")
        _merge_health(source_report, "samvad", {
            "source_id": "samvad", "count": len(samvad_offline),
            "status": ("failed" if samvad_error else
                       "healthy" if samvad_offline else "no_records"),
            "error": samvad_error,
        })

    online_tenders = _canonical_records(t1 + t2 + t3, "tender", "online")
    online_jobs = _canonical_records(j1 + j3, "job", "online")
    ai_tenders = _canonical_records(ai_tenders, "tender", "ai")
    ai_jobs = _canonical_records(ai_jobs, "job", "ai")
    district_tenders = _canonical_records(
        district_tenders, "tender", "district")
    district_jobs = _canonical_records(district_jobs, "job", "district")
    newspaper_tenders = _canonical_records(
        newspaper_tenders, "tender", "newspaper")
    newspaper_jobs = _canonical_records(
        newspaper_jobs, "job", "newspaper")
    samvad_offline = _canonical_records(
        samvad_offline, "tender", "samvad offline")

    previous_tenders = _read_generated("tenders", "tender")
    previous_jobs = _read_generated("jobs", "job")
    all_new_tenders = (
        online_tenders + district_tenders + newspaper_tenders
        + samvad_offline + ai_tenders)
    all_new_jobs = online_jobs + district_jobs + newspaper_jobs + ai_jobs
    tenders = dedup(previous_tenders + all_new_tenders, "tender")
    jobs = dedup(previous_jobs + all_new_jobs, "job")
    offline = dedup(
        district_tenders + newspaper_tenders + samvad_offline, "tender")

    _print_scraper_summary(scraper_counts, len(tenders), len(jobs))

    if args.dry_run:
        print("3. [DRY RUN] Skipping CSV write.")
        print("4. [DRY RUN] Skipping Supabase push.")
    else:
        print("3. Writing local fallback...")
        write_local(tenders, jobs, offline)
        write_manual_review_queue(manual_review)
        registry = source_registry.apply_health(registry, source_report)
        source_registry.write_registry(registry)
        write_source_health(
            scraper_counts, report=source_report, registry=registry)
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
