# Validation log

Audit date: 2026-07-28 (Asia/Kolkata)
Baseline: `7190213351562a431d1bbe86ad00ae7e6d3c6466`
Branch: `agent/launch-readiness`

Secret values were not supplied to any validation command. Cloud-dependent
tests ran with relevant credential variables explicitly empty.

## Repository and runtime

| Command | Result |
|---|---|
| `git status -sb` | Original checkout: `main`, one pre-existing `frontend/next-env.d.ts` edit. Isolated M0 worktree initially clean. |
| `git branch --show-current` | `agent/launch-readiness` in isolated worktree |
| `git log -1 --oneline` | `7190213 Simplify UI with role-aware user journeys` |
| `git remote -v` | `origin` is `https://github.com/akashhs1034/cg_tender_app.git` |
| `git --version` | 2.55.0.windows.2 |
| `node --version` | v24.18.0 |
| `npm --version` / `npx --version` | 11.16.0 |
| `python --version` | 3.12.10 |
| `python -m pip --version` | 25.0.1 |
| `gh --version` / `gh auth status` | 2.96.0; authenticated account confirmed, no credential value recorded |
| Tool discovery | `pnpm`, global Supabase CLI, and Docker not installed |

## Frontend

| Command | Result | Status |
|---|---|---|
| `npm ci` | Installed 367 packages from `package-lock.json`; 7 audit findings; npm warned that `sharp` install scripts were not approved under its allow-scripts model. | PASS with warnings |
| `npm run lint` | `'eslint' is not recognized`; ESLint is referenced by the script but absent from dependencies. | **FAIL** |
| `npx tsc --noEmit` | `app/profile/page.tsx(128,8): TS2339` because `PromiseLike<void>` has no `finally`. | **FAIL** |
| `npm run build` | Next.js 16.2.6 compiled and generated 16 static pages. Output explicitly said “Skipping validation of types”; missing Supabase env caused expected data-fetch warnings. | PASS, not a type gate |
| `npm audit --omit=dev --json` | 5 high, 2 moderate, 0 critical. Direct findings include `next` and `postcss`; reported fix path includes Next.js 16.2.12. | **FAIL** |

The typecheck generated `frontend/tsconfig.tsbuildinfo`; it was verified as an
M0-generated file and removed before documentation work. No generated frontend
file is intended for commit.

## Python and ingestion

An ignored `.venv` was used. The first dependency install exceeded the command
window, but the environment was inspected, the remaining package was installed,
and `pip check` passed.

| Command | Result | Status |
|---|---|---|
| `python -m compileall -q -x '(\.venv|frontend|mobile|\.git)' .` | All scoped Python sources compiled. | PASS |
| `python -m unittest discover -v` | 20 tests pass after including two M0 inventory tests (18 existing + 2 new). | PASS |
| `python test_card_smoke.py` | Tender Portal and Government Jobs render without raw HTML leakage. Streamlit emitted CORS/XSRF and deprecated `st.components.v1.html` warnings. | PASS with warnings |
| `python verify.py` with cloud/AI vars empty | Packages, Playwright Chromium, schema file, and registries pass. Cloud connection, local CSV, and review queue are warnings. Script exits 0 despite warnings. | PASS as local smoke only |
| `python ingest.py --dry-run --skip-live --no-alerts` with cloud/AI vars empty | 12 seed tenders and 5 seed jobs after dedup; no files, cloud writes, or email. Zero-result warnings are expected because live sources were skipped. | PASS |
| `python -m pip_audit -r requirements-dev.txt` | No known vulnerabilities in the currently resolved dependency set. Requirements are not pinned, so this does not prove reproducibility. | PASS with limitation |
| `python scripts/baseline_inventory.py` | Deterministic JSON inventory: 18 pages, 7 HTTP route files, 32 Python entry points after M0 (30 pre-existing + 2 audit-tool/test entry points), 24 scraper modules, 4 workflows, 7 SQL files, 11 SQL-created tables, 4 missing literal table references, 1 manual Storage bucket, and 67 environment/repository variable names. | PASS |

## Workflows, SQL, security, and production evidence

| Check | Result | Status |
|---|---|---|
| PyYAML `safe_load` for `.github/workflows/*.yml` | 4/4 parse. This is syntax parsing, not GitHub expression/action execution validation. | PASS with limitation |
| `pglast.parse_sql` for root `*.sql` | 7/7 parse as PostgreSQL. SQL was not applied because no local Supabase stack exists. | PASS with limitation |
| Literal table coverage | `payments`, `saved_jobs`, `source_health`, and `user_profiles` are referenced but not created. `vault` Storage setup is manual. | **FAIL** |
| Current tracked high-confidence secret-pattern scan | No match; values were never printed. | PASS |
| Reachable-history high-confidence scan | Matching material exists in commits/files including historical `client_secret.json` and mobile config; values suppressed. | **FAIL** |
| GitHub secret-scanning API | Repository reports secret scanning disabled. | **FAIL** |
| GitHub branch protection API | `main` reports “Branch not protected”. | **FAIL** |
| Latest GitHub deployment evidence | Production deployment for baseline commit reported `success` on 2026-07-23. | PASS as provider evidence |
| `curl -I https://opporta.vercel.app` | HTTP 200 from Vercel on 2026-07-28. | PASS for public reachability only |
| Auth/data/AI/admin/payment production flows | Not run; no authorised test credentials or non-destructive production test plan. | NOT VALIDATED |
| Supabase migration replay and RLS tests | Not run: config, migrations, CLI, Docker, and authorised project session unavailable. | BLOCKED BY REPOSITORY BASELINE |

## Reproduction notes

- Exact package versions are in `frontend/package-lock.json`.
- Python requirements use lower bounds and can resolve differently later.
- Government live-scraper network tests were deliberately not run in M0; they
  can be slow, geo-dependent, invoke OCR/AI, and would not be deterministic.
- Flutter/Android and Streamlit feature development is frozen. M0 only ran the
  existing Streamlit card smoke; no Flutter build was required for the primary
  launch baseline.
