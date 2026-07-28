# OPPORTA launch readiness

This directory is the evidence ledger for taking OPPORTA from its current
baseline to a controlled production launch. It records facts, risks, decisions,
validation results, release gates, and milestone status. It does not imply that
the product is launch-ready.

## Current position

- Primary product: `frontend/` Next.js web application/PWA on Vercel, backed by
  Supabase.
- Primary ingestion: `ingest.py`, `scrapers/`, scheduled GitHub Actions, and
  optional India-hosted runners.
- Primary database: Supabase PostgreSQL/Auth/Storage.
- Frozen legacy clients: root Streamlit application and `mobile/` Flutter
  application. Preserve them; make only security, data-loss, or build-critical
  changes.
- M0 merge commit: `5ccc113f7b16c0f30819565921bb773e24bad2a1`.
- Working branch: `agent/m0-launch-gates`.
- Current milestone: M0.1 Launch Engineering Gates.
- Launch status: **not ready**. See
  [M0.1 launch gates](milestones/M0_1_LAUNCH_GATES.md) and
  [risk register](RISK_REGISTER.md).

## Source of truth

| Document | Purpose |
|---|---|
| [MILESTONE_STATUS.md](MILESTONE_STATUS.md) | Delivery state, commits, validation, deployment, blockers |
| [RISK_REGISTER.md](RISK_REGISTER.md) | Prioritised technical/product/operational risks |
| [DECISION_LOG.md](DECISION_LOG.md) | Dated architecture and product decisions |
| [VALIDATION_LOG.md](VALIDATION_LOG.md) | Exact commands, results, and limitations |
| [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) | Human-gated release checklist |
| [milestones/](milestones/) | Scope, evidence, and exit criteria per milestone |
| [../architecture.md](../architecture.md) | System and trust-boundary map |
| [../environment-variables.md](../environment-variables.md) | Secret-safe configuration inventory |
| [../database-map.md](../database-map.md) | Code-to-schema coverage and RLS baseline |
| [../workflow-map.md](../workflow-map.md) | CI, ingestion, deployment, and runner map |
| [../DEFERRED_PAID_SERVICES.md](../DEFERRED_PAID_SERVICES.md) | Paid integrations intentionally disabled/deferred |

## Status vocabulary

- **PREPARED**: code or documentation exists locally.
- **VALIDATED LOCALLY**: the stated local checks ran; any failures are listed.
- **COMMITTED**: changes are committed on the feature branch.
- **PUSHED**: the branch exists on the remote.
- **PR OPENED**: a pull request exists.
- **MERGED**: the commit exists in `main`.
- **DEPLOYED**: a production deployment completed.
- **PRODUCTION VALIDATED**: the relevant real production behaviour was checked.

Each state is independent. A successful build is not a deployment, and an HTTP
200 response is not end-to-end production validation.

## Updating this ledger

1. Work in an isolated milestone branch/worktree, never directly on `main`.
2. Update the milestone file, risk register, decision log, and validation log
   with every material change.
3. Record exact commands and failures. Do not erase failed evidence after a fix;
   append the successful rerun.
4. Keep secrets out of all output. Record variable names and configuration
   presence only.
5. Stop at a failed milestone exit criterion.
6. Open or update a draft PR. Do not merge or advance milestones without review.

Run the secret-safe inventory from the repository root:

```powershell
python scripts/baseline_inventory.py
```
