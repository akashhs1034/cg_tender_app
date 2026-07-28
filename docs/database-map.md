# Database map

This is a code/static-SQL baseline, not a verified production schema dump.
No production database query was made in M0.

## Reproducibility status

- `supabase/config.toml`: missing.
- `supabase/migrations/`: missing.
- Versioned seed/fixture contract: missing.
- Root SQL files: seven overlapping/manual scripts.
- Local Supabase CLI and Docker: unavailable in the audit environment.
- Fresh migration replay, advisors, schema diff, backup, restore, and RLS tests:
  not possible from the current repository.

Suggested manual order inferred from comments:

1. `schema.sql`
2. `migrate_security.sql`
3. `phase3_rich_columns.sql`
4. `phase4_discovery_sources.sql`
5. `phase4b_discovery_approval.sql`
6. `phase4b_discovered_files.sql`
7. `alerts_schema.sql`

This order is undocumented automation, not an acceptable production migration
history.

## Tables created by version-controlled SQL

| Table | Consumers | Intended exposure / ownership | Baseline concerns |
|---|---|---|---|
| `tenders` | Next.js, Python, Streamlit, Flutter | Public read; service-role write | Expired rows deleted; incomplete provenance/verification; global `ai_score` marketed as personal |
| `jobs` | Next.js, Python, Streamlit, Flutter | Public read; service-role write | Same lifecycle/trust issues as tenders |
| `offline_tenders` | Python, Streamlit, Flutter, analytics | Public read | No verification workflow |
| `corrigendums` | Python, Next.js, Flutter | Public read | Old rows permanently deleted |
| `profiles` | Next.js, Streamlit, Flutter, alerts | User-owned by JWT email | Must migrate to `auth.users.id`; mixed contractor/job-seeker columns |
| `saved_tenders` | Next.js, Streamlit, Flutter | User-owned by JWT email | No foreign key to auth user/opportunity |
| `documents` | Streamlit, Flutter | User-owned metadata by JWT email | Storage bucket/policies are manual; upload validation baseline unknown |
| `alert_log` | Python alerts | Allow-all policy | Any Data API role with grants could read/write all rows; contains user email |
| `discovered_sources` | scanner, Streamlit/admin, Next.js admin | RLS enabled, no public policy | Next.js admin uses anon client, likely empty; actual grants unknown |
| `approved_sources` | scanner/admin | RLS, anon/auth revoked, service-role grants | No migration ordering/tooling |
| `discovered_files` | scanner/admin | RLS, anon/auth revoked, service-role grants | No migration ordering/tooling |

## Literal code references absent from SQL

| Reference | Consumers | Effect |
|---|---|---|
| `source_health` | ingestion and Next.js admin | Ingestion push degrades to warning; admin health can be empty |
| `saved_jobs` | Next.js saved-job context | Job saves fail unless table was created manually in production |
| `payments` | create-order/webhook | Payment audit/state writes fail or are silently skipped when admin client absent |
| `user_profiles` | Python alerts | Alerts try this table, then fall back to `profiles`; schema drift is hidden |

The `vault` Storage bucket is referenced by Flutter and documented in comments,
but bucket creation and policies are not version-controlled.

## RLS baseline

- Public opportunity policies use `using (true)` for `SELECT`.
- User tables use verified JWT email equality, not user-editable metadata, but
  ownership is still email-based and mutable.
- No `TO anon` / `TO authenticated` clauses are used, and explicit Data API
  grants are inconsistent across scripts.
- `alert_log` allows all operations with `using (true) with check (true)`.
- No two-user integration tests exist.
- No version-controlled Storage object policies exist.
- Production grants/policies may differ from Git because dashboard SQL is the
  current setup mechanism.

## Missing launch schema

The following required concepts are absent or not reproducible:

- `contractor_profiles`, `jobseeker_profiles`, UUID-owned `user_profiles`
- `alerts`, robust `alert_log`
- `source_health`
- `ingestion_runs`, `ingestion_failures`
- lifecycle/history events
- `manual_review_queue`
- `payments`, `payment_events`, entitlements/subscriptions
- `ai_usage`, quota/rate-limit state
- admin audit log
- correction/report audit
- versioned Storage bucket and policies

## M2 acceptance evidence

M2 must provide additive migrations, a fresh replay, existing-production upgrade,
backup/restore/rollback instructions, schema verification, RLS tests with two
users, indexes/constraints/foreign keys, and compatibility notes. No destructive
production migration is authorised by this baseline.
