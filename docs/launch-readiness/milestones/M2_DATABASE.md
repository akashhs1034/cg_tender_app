# M2 — Reproducible database

Status: **NOT STARTED**
Dependency: M1 schema requirements and verified production backup/upgrade access

## Objective

Recreate the complete Supabase database from version-controlled, additive
migrations with least-privilege RLS and a safe production upgrade path.

## Baseline inputs

- No `supabase/config.toml` or migrations directory.
- Seven overlapping manual SQL files.
- Four literal code-referenced tables absent from SQL.
- `vault` bucket/policies are manual.
- Private ownership is email-based; no two-user RLS test.

## Planned scope

- Inventory actual production schema/grants/policies without printing data.
- Establish `supabase/` config, ordered migrations, fixtures, and verification.
- Standardise ownership on `auth.users.id`.
- Add constraints, indexes, triggers, comments, grants, RLS, and Storage policies.
- Document fresh setup, backup/restore, existing-project upgrade, rollback, data
  migration, compatibility, and tests.

## Exit criteria

- Fresh database and Storage policy state can be recreated from Git.
- Every code reference has a migration.
- Private data has proven two-user isolation.
- Production upgrade/backup/restore/rollback procedures are documented and
  rehearsed locally where possible.
- No required dashboard-only SQL remains.
