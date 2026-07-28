# Decision log

## D-0001 — Primary architecture and legacy freeze

- Date: 2026-07-28
- Status: Accepted
- Decision: Treat `frontend/`, the Python ingestion pipeline, and Supabase as
  the launch architecture. Freeze new Streamlit and Flutter features while
  preserving both clients.
- Rationale: Launch-critical effort must converge on one supported product
  without deleting working legacy assets.

## D-0002 — Isolated feature worktree

- Date: 2026-07-28
- Status: Accepted
- Decision: Create `agent/launch-readiness` in a separate worktree at
  `C:\cg_tender_app-main\agent-launch-readiness`.
- Rationale: The original checkout contained an unrelated generated edit to
  `frontend/next-env.d.ts`. Isolation preserves it without reset, stash, or
  accidental staging.

## D-0003 — M0 is evidence-only

- Date: 2026-07-28
- Status: Accepted
- Decision: Restrict M0 changes to documentation and deterministic read-only
  audit tooling/tests.
- Rationale: Security, schema, lifecycle, and product changes require focused
  milestones, reviewable migrations, and dedicated validation.

## D-0004 — No production mutation during baseline

- Date: 2026-07-28
- Status: Accepted
- Decision: Do not connect to or write the production database, rotate
  credentials, invoke AI, send email, create payment orders, or purge data in
  M0.
- Rationale: M0 lacks an authorised secret-safe production session, verified
  backup, and reproducible schema.

## D-0005 — Secret-safe evidence

- Date: 2026-07-28
- Status: Accepted
- Decision: Record environment-variable names, secret types, file/commit
  locations, and presence only. Never record secret values or prefixes.
- Rationale: The repository has historical secret exposure; audit output must
  not compound it.

## D-0006 — Global scores are not personal recommendations

- Date: 2026-07-28
- Status: Accepted
- Decision: Treat current `ai_score` values as global opportunity/completeness
  indicators until an authenticated profile is demonstrably used.
- Rationale: The Next.js ranking path never loads the profile but uses personal
  recommendation language.

## D-0007 — No paid-service dependency

- Date: 2026-07-28
- Status: Accepted
- Decision: Build provider abstractions and safe disabled/free fallbacks before
  any paid activation. Track future requirements in
  `docs/DEFERRED_PAID_SERVICES.md`.
- Rationale: This is an explicit commercial constraint.

## D-0008 — M0 can exit with failed product gates

- Date: 2026-07-28
- Status: Accepted
- Decision: M0 exit means the baseline and every blocker are recorded, not that
  launch checks pass.
- Rationale: Lint, typecheck, dependency, security, schema, and operational
  failures are baseline findings that later milestones must resolve.

## D-0009 — M0.1 is a focused engineering-gates milestone

- Date: 2026-07-28
- Status: Accepted
- Decision: Merge the evidence-only M0 PR, then repair build, lint, dependency,
  secret-scanning, and pull-request gates in the isolated
  `agent/m0-launch-gates` worktree before starting M1.
- Rationale: Reliable enforcement is a prerequisite for reviewing ingestion
  changes, and the original checkout contains an unrelated generated edit that
  must remain untouched.

## D-0010 — Classify public client configuration separately

- Date: 2026-07-28
- Status: Accepted
- Decision: Treat Supabase anon/publishable keys and public mobile
  configuration as public client configuration, not automatically as private
  secrets. Treat Supabase secret/service-role keys and private provider keys as
  incidents requiring independent revocation evidence.
- Rationale: Accurate classification avoids false incident claims while
  preserving the requirement for least-privilege grants and tested RLS.

## D-0011 — Patch vulnerable dependency chains without a major upgrade

- Date: 2026-07-28
- Status: Accepted
- Decision: Upgrade within Next.js 16 and current shadcn/PostCSS releases, then
  use narrowly versioned npm/pnpm overrides for affected transitive packages.
  Do not use `npm audit fix --force`.
- Rationale: This produces a zero-finding production audit while keeping the
  application framework and behaviour stable. Every override is exercised by
  clean install, lint, typecheck, and production build.

## D-0012 — Solo-founder pull-request enforcement

- Date: 2026-07-28
- Status: Accepted
- Decision: Run four read-only PR checks and, after their exact names have run,
  require them on `main` with pull requests, up-to-date branches, force-push
  blocking, deletion blocking, zero mandatory human approvals, and
  administrator recovery.
- Rationale: The repository needs blocking automation without creating an
  impossible second-reviewer requirement or requiring production credentials.
