# Workflow and deployment map

Baseline: 2026-07-28.

## GitHub Actions

| Workflow | Trigger / runner | Main command | Configuration | Baseline concerns |
|---|---|---|---|---|
| Daily Tender Ingestion | Three daily cron windows plus manual; `SCRAPER_RUNNER` or `ubuntu-latest`; 120 min | `python ingest.py` | Supabase, Gemini, Resend, proxy secrets; scraper tuning vars | Strict health not enabled; long run; recent failures/cancellations; external scheduler concurrency not covered |
| OPPORTA Discovery Scan | Weekly Sunday plus manual; Ubuntu; 30 min | `python source_discovery.py` | Supabase secrets; bounded scan mode/counts | Artifact fallback only in scanner counterpart; no central monitoring |
| OPPORTA Approved Source Scan | Weekly Wednesday plus manual; Ubuntu; 30 min | `python approved_source_scanner.py` | Supabase secrets; bounded scan mode/counts | Missing-table fallback can hide schema drift |
| Build Release AAB | Mobile pull requests plus manual; Ubuntu; 30 min | `flutter build appbundle --release` | Optional signing secrets | Legacy/frozen client only; disposable CI signing fallback must never be published |

All four files parse as YAML. M0 did not run GitHub expression/action validation.
Actions are pinned to version tags, not immutable commit SHAs.

## Missing primary CI

There is no pull-request workflow that runs:

- frontend `npm ci`, lint, standalone typecheck, build, unit/API/E2E tests;
- Python compileall, unit/parser/health/data-quality tests;
- Supabase migration replay, schema verification, or RLS tests;
- dependency, secret, or static security scans.

`main` is not branch-protected according to the GitHub API, so no required check
currently blocks merging.

## Observed workflow state

From the latest 30 GitHub runs at audit time:

- Daily ingestion: 5 success, 5 failure, 7 cancelled, 1 in progress.
- Build Release AAB: 2 success, 6 failure.
- Approved Source Scan: 3 success.
- Discovery Scan: 1 success.

The latest ingestion had been in progress for more than two hours at the audit
snapshot. The concurrency group prevents overlapping GitHub workflow runs but
causes queued schedule windows to wait and later cancel; it does not coordinate
with systemd or Windows tasks.

## Deployment

- Vercel’s GitHub integration is inferred from GitHub deployment records; there
  is no deployment workflow or Vercel configuration in the repository.
- Latest Production record for the baseline commit: provider state `success`,
  created 2026-07-23.
- Canonical `https://opporta.vercel.app` returned HTTP 200 on 2026-07-28.
- The deployment-specific URL required Vercel SSO.
- No repository-defined preview/production environment contract, smoke suite,
  rollback command, or environment-promotion process exists.

## India-hosted execution

Three alternatives exist:

1. GitHub-hosted runner, optionally using an India HTTPS proxy.
2. India self-hosted GitHub runner (`deploy/india-vm/setup-runner.sh` or Windows
   runner setup).
3. Standalone Linux systemd or Windows Scheduled Task.

Risks:

- Linux VM `setup.sh` defaults to
  `claude/project-review-optimize-9x3z45`, not `main`.
- Standalone timers are outside the GitHub concurrency lock.
- Scripts install unpinned latest dependencies/runners.
- Runner hosts receive production repository secrets and need patching,
  least-privilege service accounts, log retention, and incident procedures.
- A free/local runner fallback exists; a reliable always-on India endpoint or
  proxy may eventually require paid infrastructure.

## Required M7 workflow state

- One authoritative release and ingestion scheduler.
- Blocking primary CI with least-privilege permissions.
- Immutable or reviewed action pinning.
- Environment-specific secrets/variables documented by name.
- Saved validation artifacts and actionable alerts.
- Production deployment/rollback and post-deploy smoke evidence.
