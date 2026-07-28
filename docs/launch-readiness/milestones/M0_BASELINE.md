# M0 — Production baseline

## Status

**VALIDATED LOCALLY — baseline complete with launch blockers.**
Branch: `agent/launch-readiness`
Baseline commit: `7190213351562a431d1bbe86ad00ae7e6d3c6466`
Application deployment: existing `main` deployment only
Production validation: public landing HTTP check only

M0 intentionally contains documentation and read-only audit tooling, not broad
functional fixes.

## Repository state

- The pasted repository path did not exist. The connected checkout was found at
  `C:\cg_tender_app-main\_github_repo` and matched
  `akashhs1034/cg_tender_app`.
- The original checkout was on `main` with one unrelated generated edit:
  `frontend/next-env.d.ts` changed its route-types import. It was not reset,
  stashed, edited, staged, or moved.
- M0 uses a clean separate worktree at
  `C:\cg_tender_app-main\agent-launch-readiness`.
- `main` is not protected according to the GitHub API.
- No repository `AGENTS.md` was present.

## Production evidence

- GitHub/Vercel recorded a successful Production deployment for commit
  `7190213351562a431d1bbe86ad00ae7e6d3c6466` on 2026-07-23.
- `https://opporta.vercel.app` returned HTTP 200 on 2026-07-28.
- The deployment-specific URL redirected to Vercel SSO; the canonical URL was
  used for the public availability check.
- Auth, role selection, Supabase reads/writes, AI, admin, Storage, alert,
  payment, and rollback behaviour were not production-validated.

## Inventory

The deterministic inventory is produced by
`python scripts/baseline_inventory.py`.

| Area | Baseline |
|---|---|
| Next.js pages | 18 route pages |
| HTTP route files | 7: 6 API routes plus `/auth/callback` |
| API groups | admin cleanup, 3 AI, 2 payments |
| Python entry points | 32 after M0: 30 pre-existing plus audit tool/test |
| Scraper modules | 24 under `scrapers/` |
| Runtime source registry | 137 sources: 50 CG, 82 UP, 5 unspecified |
| Workflows | 4 |
| SQL files | 7 root manual SQL files |
| SQL-created tables | 11 |
| Literal referenced tables absent from SQL | `payments`, `saved_jobs`, `source_health`, `user_profiles` |
| Storage | `vault` bucket configured only by manual instructions |
| Environment/repository variable names | 67, values excluded |
| Supabase local project | No `config.toml`, migrations directory, or seed contract |
| Clients | Primary Next.js, legacy Streamlit, legacy Flutter |

Detailed maps:

- [Architecture](../../architecture.md)
- [Environment variables](../../environment-variables.md)
- [Database](../../database-map.md)
- [Workflows](../../workflow-map.md)

## Route security classification

| Classification | Routes |
|---|---|
| Public pages | `/`, `/tenders`, `/tenders/[id]`, `/jobs`, `/jobs/[id]`, `/analytics`, login/signup/reset flows, `/bid-documents`, `/exam-planner` |
| Authenticated server page | `/dashboard` |
| Client-auth-dependent pages | `/profile`, `/saved`, `/select-role` |
| Admin server pages | `/admin`, `/admin/discovery` |
| Public/auth callback | `/auth/callback` with same-origin `next` validation |
| Admin API | `POST /api/admin/cleanup`; admin email allowlist, but hardcoded fallback |
| AI APIs | `POST /api/ai/analyze`, `/draft`, `/eligibility`; currently unauthenticated |
| Authenticated payment API | `POST /api/payments/create-order`; feature-flagged |
| Webhook | `POST /api/payments/webhook`; HMAC checked, event model incomplete |
| Edge Functions | `bid-engine`, `intelligence`; code has no explicit user/quota validation and deployment auth posture is not reproducible |

## Validation results

### Passed

- Frontend `npm ci`.
- Next.js production build (with type validation explicitly skipped).
- Python compileall.
- 18 existing unit tests and 2 new audit-tool tests.
- Two Streamlit card rendering smoke tests.
- Playwright-managed Chromium launch.
- No-write/no-live ingestion seed smoke.
- Four workflow files parse as YAML.
- Seven SQL files parse as PostgreSQL.
- Current tracked tree has no high-confidence secret-pattern match.
- Python dependency audit found no known issue in the currently resolved set.
- Public production landing returned HTTP 200.

### Failed or blocked

- Lint cannot run: ESLint dependency absent.
- Typecheck fails at `frontend/app/profile/page.tsx:128`.
- Build ignores TypeScript errors.
- npm production dependency tree has 5 high and 2 moderate findings.
- Historical secret-pattern matches exist; rotation status unknown.
- GitHub secret scanning is disabled.
- No local Supabase stack/migrations/RLS tests are possible from Git.
- No frontend/Python/database/security pull-request CI.
- Recent ingestion reliability is poor: 5 successes, 5 failures, 7
  cancellations, and 1 in-progress run in the observed ingestion set.

See [VALIDATION_LOG.md](../VALIDATION_LOG.md) for exact commands.

## Prioritised blockers

1. Confirm revocation/rotation of historically exposed credentials and enable
   automated secret scanning.
2. Prevent unauthenticated AI abuse and canonical-cache poisoning.
3. Stop routine deletion of opportunity history and remove unsafe purge paths.
4. Create a reproducible, backed-up, additive Supabase migration baseline.
5. Fix and enforce lint/typecheck/dependency gates in pull-request CI.
6. Add run/failure/checkpoint/freshness records and tune strict ingestion health.
7. Replace false personal-recommendation labels until profile-specific matching
   exists.
8. Migrate tenant ownership to `auth.users.id` and prove two-user RLS/Storage
   isolation.
9. Fail admin access closed and add admin audit logs.
10. Add observability, backup/restore rehearsal, rollback, and incident response.

## Exit criteria

| Criterion | Evidence | Result |
|---|---|---|
| Production commit recorded | Full SHA above and deployment evidence | MET |
| Repository state understood | Isolated branch/worktree and dirty-file record | MET |
| Frontend build recorded | Build passes while skipping types | MET |
| Typecheck recorded | One exact failure recorded | MET |
| Python test result recorded | 20 unit + 2 card smoke pass | MET |
| Workflows inventoried | 4 workflows plus operational history | MET |
| Tables inventoried | Code/SQL/RLS/Storage map | MET |
| Environment names inventoried | 67 names, no values | MET |
| Baseline blockers documented | Risk register and priority list | MET |

M0 exit criteria are met because the baseline is factual and reproducible.
Launch criteria are not met.

## Next safe action

Review the draft M0 pull request. Do not merge automatically and do not begin M1
until the baseline, priorities, and historical-secret response are approved.
