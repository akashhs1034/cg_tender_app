-- schema.sql — run this once in the Supabase SQL editor.
-- This is the schema the app AND the pipeline agree on. The old code wrote
-- mismatched columns to differently-named tables; that is what this fixes.

create table if not exists tenders (
    id               bigint generated always as identity primary key,
    source_id        text unique not null,      -- dedup / upsert key
    title            text not null,
    state            text,
    district         text,
    organization     text,
    category         text,
    value_text       text,                      -- human-readable, e.g. "₹ 45.00 L"
    value_lakhs      numeric,                   -- normalized for sorting/filtering
    deadline         date,
    emd              text,
    contractor_class text,
    experience       text,
    eligibility      text,
    description      text,
    requirements     text,
    document_url     text,
    ai_score         int,
    source_portal    text,
    scraped_at       timestamptz default now()
);

create table if not exists jobs (
    id            bigint generated always as identity primary key,
    source_id     text unique not null,
    title         text not null,
    state         text,
    district      text,
    department    text,
    category      text,
    vacancies     int,
    qualification text,
    salary        text,
    deadline      date,
    description   text,
    document_url  text,
    apply_link    text,                   -- direct URL to apply or view the official notice
    ai_score      int,
    source_portal text,
    scraped_at    timestamptz default now()
);

-- Phase 3 is an additive migration. Existing deployments keep every original
-- column and can apply this block safely with live data in place.
alter table if exists tenders
    add column if not exists department text,
    add column if not exists source_type text,
    add column if not exists source_name text,
    add column if not exists source_url text,
    add column if not exists tender_no text,
    add column if not exists subcategory text,
    add column if not exists sector text,
    add column if not exists estimated_value text,
    add column if not exists opening_date date,
    add column if not exists published_date date,
    add column if not exists location text,
    add column if not exists required_turnover text,
    add column if not exists required_experience text,
    add column if not exists required_documents jsonb default '[]'::jsonb,
    add column if not exists submission_mode text,
    add column if not exists online_or_offline text,
    add column if not exists newspaper_name text,
    add column if not exists page_no text,
    add column if not exists confidence_score int,
    add column if not exists ocr_text text,
    add column if not exists language text,
    add column if not exists is_corrigendum boolean default false,
    add column if not exists linked_original_tender text,
    add column if not exists all_sources jsonb default '[]'::jsonb,
    add column if not exists source_count int default 1,
    add column if not exists first_seen_at timestamptz,
    add column if not exists last_seen_at timestamptz,
    add column if not exists status text default 'active',
    add column if not exists requires_manual_review boolean default false;

alter table if exists jobs
    add column if not exists source_type text,
    add column if not exists source_name text,
    add column if not exists source_url text,
    add column if not exists advertisement_no text,
    add column if not exists subcategory text,
    add column if not exists field text,
    add column if not exists age_limit text,
    add column if not exists published_date date,
    add column if not exists application_start_date date,
    add column if not exists application_end_date date,
    add column if not exists exam_date date,
    add column if not exists application_fee text,
    add column if not exists selection_process text,
    add column if not exists reservation_info text,
    add column if not exists language text,
    add column if not exists ocr_text text,
    add column if not exists confidence_score int,
    add column if not exists online_or_offline text,
    add column if not exists all_sources jsonb default '[]'::jsonb,
    add column if not exists source_count int default 1,
    add column if not exists first_seen_at timestamptz,
    add column if not exists last_seen_at timestamptz,
    add column if not exists status text default 'active',
    add column if not exists requires_manual_review boolean default false;

create table if not exists offline_tenders (
    source_id       text primary key,
    title           text not null,
    state           text,
    district        text,
    organization    text,
    nit_no          text,
    category        text,
    value_text      text,
    value_lakhs     numeric,
    emd             text,
    published_date  date,
    deadline        date,
    opening_date    date,
    newspaper       text,
    document_url    text,
    description     text,
    source_portal   text,
    added_by        text,
    scraped_at      timestamptz default now()
);

create table if not exists corrigendums (
    source_id        text primary key,
    title            text not null,
    state            text,
    published_date   date,
    closing_date     date,
    opening_date     date,
    corrigendum_url  text,
    tender_url       text,
    source_portal    text,
    scraped_at       timestamptz default now()
);

create index if not exists idx_tenders_state    on tenders (state);
create index if not exists idx_tenders_deadline on tenders (deadline);
create index if not exists idx_tenders_status   on tenders (status);
create index if not exists idx_jobs_state       on jobs (state);
create index if not exists idx_jobs_category    on jobs (category);
create index if not exists idx_jobs_status      on jobs (status);

-- Row Level Security
alter table tenders enable row level security;
alter table jobs    enable row level security;
alter table offline_tenders enable row level security;
alter table corrigendums enable row level security;

-- Public READ only (browser + app). Writes are intentionally NOT granted to
-- anon/authenticated: the ingest pipeline writes with the SUPABASE_SERVICE_KEY,
-- which bypasses RLS. This way the public anon key (it ships in the mobile app)
-- can never insert, modify, or delete this authoritative scraped data.
drop policy if exists "public read tenders" on tenders;
drop policy if exists "public read jobs" on jobs;
drop policy if exists "public read offline tenders" on offline_tenders;
drop policy if exists "public read corrigendums" on corrigendums;
create policy "public read tenders"  on tenders for select using (true);
create policy "public read jobs"     on jobs    for select using (true);
create policy "public read offline tenders" on offline_tenders
    for select using (true);
create policy "public read corrigendums" on corrigendums
    for select using (true);


-- ===========================================================================
-- SaaS multi-tenant tables (added for the per-contractor product)
-- ===========================================================================

-- One profile per contractor account. In production, `user_id` should be the
-- Supabase Auth uid; for the MVP we key by email.
create table if not exists profiles (
    id               bigint generated always as identity primary key,
    email            text unique not null,
    company_name     text,
    turnover_lakhs   numeric default 0,
    contractor_class text default 'Class C',
    experience_years int default 0,
    sectors          text[] default '{}',
    states           text[] default '{Chhattisgarh,Uttar Pradesh}',
    districts        text[] default '{}',
    plan             text default 'free',          -- free | pro | premium
    created_at       timestamptz default now()
);

-- Workflow lock-in: tenders a contractor has saved to their pipeline.
create table if not exists saved_tenders (
    id         bigint generated always as identity primary key,
    email      text not null,
    source_id  text not null,                       -- references tenders.source_id
    status     text default 'interested',           -- interested | preparing | submitted | won | lost
    note       text,
    saved_at   timestamptz default now(),
    unique (email, source_id)
);

alter table profiles      enable row level security;
alter table saved_tenders enable row level security;

-- Strict per-user RLS: a signed-in user can read/write ONLY their own rows —
-- the JWT's verified email claim must equal the row's email. Even the project
-- owner cannot reach another user's data through the app; only the service-role
-- key (never shipped in the app) bypasses this.
drop policy if exists "profiles own row" on profiles;
drop policy if exists "saved own rows" on saved_tenders;
create policy "profiles own row" on profiles for all
    using      ((auth.jwt() ->> 'email') = email)
    with check ((auth.jwt() ->> 'email') = email);
create policy "saved own rows" on saved_tenders for all
    using      ((auth.jwt() ->> 'email') = email)
    with check ((auth.jwt() ->> 'email') = email);


-- ===========================================================================
-- Document vault (added for the certificate upload / reuse feature)
-- ===========================================================================

-- Metadata only — raw bytes live in Supabase Storage bucket "vault"
-- (local fallback: data/vault/<email_hash>/<doc_id>.bin + data/documents.json)
--
-- Storage bucket setup (run once in the Supabase dashboard or via CLI):
--   supabase storage create vault --public=false
create table if not exists documents (
    id          bigint generated always as identity primary key,
    doc_id      text unique not null,           -- uuid hex, used as storage path segment
    email       text not null,
    name        text not null,                  -- user-supplied label, e.g. "GST Registration"
    filename    text not null,                  -- original upload filename
    mime_type   text default 'application/octet-stream',
    size_bytes  int,
    uploaded_at timestamptz default now()
);

create index if not exists idx_documents_email on documents (email);

alter table documents enable row level security;
-- Strict per-user RLS — a user can only ever touch their own document metadata.
drop policy if exists "documents own rows" on documents;
create policy "documents own rows" on documents for all
    using      ((auth.jwt() ->> 'email') = email)
    with check ((auth.jwt() ->> 'email') = email);
