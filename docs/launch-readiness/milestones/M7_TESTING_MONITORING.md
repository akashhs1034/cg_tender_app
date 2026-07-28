# M7 — Testing, CI, observability, and backups

Status: **NOT STARTED**
Dependency: stable M1–M6 contracts and migrations

## Objective

Block unsafe releases, detect incidents quickly, and restore service/data within
defined objectives.

## Baseline inputs

- Lint cannot start, standalone typecheck fails, build skips types.
- No primary pull-request CI or branch protection.
- No migration/RLS suite, E2E suite, provider-neutral monitoring, restore
  rehearsal, or incident runbook.

## Planned scope

- Blocking frontend, Python, database, security, and browser E2E CI.
- Critical auth/role/profile/search/save/AI/alert/admin/session flows.
- Structured provider-neutral logs/metrics for frontend, API, auth, Supabase, AI,
  ingestion, payment, and latency.
- Free/local/GitHub alert adapters with documented optional paid upgrades.
- Database/Storage backup, restore rehearsal, application/database rollback, and
  incident response.

## Exit criteria

- Failing checks block merge.
- Critical paths are automated.
- Production failures generate actionable alerts.
- Restore and rollback have evidence.
- No unresolved critical test failure.
