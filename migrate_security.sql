-- migrate_security.sql
-- Run once in the Supabase SQL editor (Dashboard → SQL Editor → New query).
--
-- What this does:
--   1. Replaces the permissive MVP "allow everything" RLS policies with strict
--      per-user policies: each user can only read/write their OWN rows.
--   2. Adds job-seeker columns to the profiles table.
--
-- After running this, even the project owner cannot query another user's
-- profile, saved tenders, or documents through the app — only through the
-- Supabase service-role key (which is never exposed in the app).

-- ===========================================================================
-- STEP 0 — Ensure all user tables have an email column
--           (saved_tenders was originally created with user_id, not email)
-- ===========================================================================
alter table profiles      add column if not exists email     text;
alter table saved_tenders add column if not exists email     text;
alter table saved_tenders add column if not exists source_id text;
alter table saved_tenders add column if not exists note      text;
alter table documents     add column if not exists email     text;

-- ===========================================================================
-- STEP 1 — Drop the permissive MVP policies
-- ===========================================================================
drop policy if exists "mvp profiles rw"  on profiles;
drop policy if exists "mvp saved rw"     on saved_tenders;
drop policy if exists "mvp documents rw" on documents;

-- ===========================================================================
-- STEP 2 — Strict per-user RLS (JWT email must match row email)
-- ===========================================================================

-- profiles: each user sees and edits only their own profile
create policy "profiles own row"
    on profiles for all
    using      (auth.email() = email)
    with check (auth.email() = email);

-- saved_tenders: each user sees only their own saved tenders
create policy "saved own rows"
    on saved_tenders for all
    using      (auth.email() = email)
    with check (auth.email() = email);

-- documents: each user sees only their own document metadata
create policy "documents own rows"
    on documents for all
    using      (auth.email() = email)
    with check (auth.email() = email);

-- ===========================================================================
-- STEP 3 — Add job-seeker columns to profiles
-- ===========================================================================
alter table profiles add column if not exists full_name             text;
alter table profiles add column if not exists qualification         text;
alter table profiles add column if not exists degree_type           text;
alter table profiles add column if not exists job_experience_years  int     default 0;
alter table profiles add column if not exists job_skills            text[]  default '{}';
alter table profiles add column if not exists job_category          text    default 'General';
alter table profiles add column if not exists languages             text[]  default '{}';

-- ===========================================================================
-- NOTE on Supabase Storage (vault bucket)
-- ===========================================================================
-- In the Supabase Dashboard → Storage → vault bucket:
--   • Set bucket to PRIVATE (not public)
--   • Enable RLS on the bucket
--   • Add a storage policy:
--       Allowed operations: SELECT, INSERT, DELETE
--       Using expression:   (storage.foldername(name))[1] = auth.email()
-- This ensures users can only access files in their own email-named folder.
