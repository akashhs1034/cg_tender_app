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
    ai_score      int,
    source_portal text,
    scraped_at    timestamptz default now()
);

create index if not exists idx_tenders_state    on tenders (state);
create index if not exists idx_tenders_deadline on tenders (deadline);
create index if not exists idx_jobs_state       on jobs (state);
create index if not exists idx_jobs_category    on jobs (category);

-- Row Level Security: the public site only needs READ access. The pipeline
-- writes using the service key (server-side only, never in the browser).
alter table tenders enable row level security;
alter table jobs    enable row level security;

create policy "public read tenders" on tenders for select using (true);
create policy "public read jobs"    on jobs    for select using (true);


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

-- PRODUCTION NOTE: replace these permissive policies with per-user policies
-- once Supabase Auth is wired, e.g.  using (auth.jwt()->>'email' = email),
-- so each contractor can read/write ONLY their own profile and saved tenders.
create policy "mvp profiles rw"  on profiles      for all using (true) with check (true);
create policy "mvp saved rw"     on saved_tenders for all using (true) with check (true);


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
create policy "mvp documents rw" on documents for all using (true) with check (true);
