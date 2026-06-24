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

create index if not exists idx_tenders_state    on tenders (state);
create index if not exists idx_tenders_deadline on tenders (deadline);
create index if not exists idx_jobs_state       on jobs (state);
create index if not exists idx_jobs_category    on jobs (category);

-- Row Level Security
alter table tenders enable row level security;
alter table jobs    enable row level security;

-- Public read (browser + app)
create policy "public read tenders"  on tenders for select using (true);
create policy "public read jobs"     on jobs    for select using (true);

-- Pipeline write: tenders and jobs are public government data, no user-specific secrets.
-- The anon key is used by the local ingest pipeline (no user auth context).
create policy "pipeline insert tenders" on tenders for insert with check (true);
create policy "pipeline update tenders" on tenders for update using (true);
create policy "pipeline insert jobs"    on jobs    for insert with check (true);
create policy "pipeline update jobs"    on jobs    for update using (true);


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
create policy "documents own rows" on documents for all
    using      ((auth.jwt() ->> 'email') = email)
    with check ((auth.jwt() ->> 'email') = email);
