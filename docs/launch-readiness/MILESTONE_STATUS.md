# Milestone status

Last updated: 2026-07-28 (Asia/Kolkata)

| Milestone | Status | Branch | Commits | Tests | Remaining blockers | Deployment | Production validation |
|---|---|---|---|---|---|---|---|
| M0 Production Baseline | MERGED | `agent/launch-readiness` | `5ccc113` squash merge | See `VALIDATION_LOG.md` | Baseline risks transferred to focused milestones | Existing `main` deployment evidence only; M0 itself was documentation/audit tooling | Limited public landing check only |
| M0.1 Launch Engineering Gates | VALIDATED LOCALLY — remote CI/protection evidence pending | `agent/m0-launch-gates` | `b274e4d`, `1be9c22`, `a545532`, `4bf4483` plus evidence update | Frontend and Python gates pass; see `VALIDATION_LOG.md` | Historical private-key revocation is unconfirmed; draft PR, CI run, and `main` protection pending | Not deployed | Not production-validated |
| M1 Reliable Ingestion | NOT STARTED | — | — | — | Requires M0.1 review | — | — |
| M2 Reproducible Database | NOT STARTED | — | — | — | Requires M1 and production-schema access/backup plan | — | — |
| M3 Security and AI Abuse Protection | NOT STARTED | — | — | — | Requires reproducible schema and threat-model review | — | — |
| M4 Data Trust and Verification | NOT STARTED | — | — | — | Requires lifecycle/schema foundations | — | — |
| M5 True Personalisation | NOT STARTED | — | — | — | Requires honest labels and profile schema | — | — |
| M6 Core User Experience | NOT STARTED | — | — | — | Requires role-specific product behaviour | — | — |
| M7 Testing, CI, Observability, Backups | NOT STARTED | — | — | — | Requires stable interfaces and migrations | — | — |
| M8 Payments and Legal Readiness | NOT STARTED | — | — | — | Production payments must remain disabled | — | — |
| M9 Closed Beta Readiness | NOT STARTED | — | — | — | Requires all critical launch gates | — | — |
| M10 Controlled Public Launch | NOT STARTED | — | — | — | Requires human launch approval | — | — |
| M11 Investment Readiness | NOT STARTED | — | — | — | Requires real operational/product evidence | — | — |

## M0 files changed

- `scripts/baseline_inventory.py`
- `scripts/__init__.py`
- `test_baseline_inventory.py`
- `docs/architecture.md`
- `docs/environment-variables.md`
- `docs/database-map.md`
- `docs/workflow-map.md`
- `docs/DEFERRED_PAID_SERVICES.md`
- `docs/launch-readiness/**`

No application behaviour, database schema, workflow, scraper, Streamlit, or
Flutter source was changed in M0.

## M0 publication

- Baseline audit commit: `17c5f75 Document M0 production baseline`
- Remote branch: `origin/agent/launch-readiness`
- Draft pull request:
  `https://github.com/akashhs1034/cg_tender_app/pull/51`
- Merge: squash commit `5ccc113f7b16c0f30819565921bb773e24bad2a1`
  verified on `origin/main`
- M1: not started

## M0.1 publication

- Branch: `agent/m0-launch-gates`
- Milestone:
  [M0_1_LAUNCH_GATES.md](milestones/M0_1_LAUNCH_GATES.md)
- Local frontend, Python, audit-tooling, and current-tree secret gates pass.
- GitHub native secret scanning: enabled on 2026-07-28.
- Draft pull request and remote workflow evidence: pending.
- `main` protection: pending the first workflow run and exact check names.
- Deployment: not performed.
- M1: not started.

## M0 validation summary

- Passed: frontend dependency install, production build, Python compileall,
  20 unit tests after adding audit-tool tests, two Streamlit card smoke tests,
  Playwright browser launch, no-write ingestion smoke, workflow YAML parsing,
  PostgreSQL parsing, Python dependency audit, current-tree high-confidence
  secret-pattern scan, and public production HTTP reachability.
- Failed: frontend lint cannot start, standalone TypeScript check has one error,
  npm audit reports seven findings, and GitHub secret scanning is disabled.
- Not executable from this checkout: Supabase migration replay/RLS tests
  (no `supabase/config.toml`, migrations directory, CLI, Docker, or authorised
  production database session).
