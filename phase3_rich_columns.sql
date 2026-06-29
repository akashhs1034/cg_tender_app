-- OPPORTA Phase 3: additive rich-column migration only.
-- Safe to run repeatedly. No tables, rows, policies, or existing columns are removed.

begin;

alter table if exists public.tenders
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
    add column if not exists required_documents jsonb,
    add column if not exists submission_mode text,
    add column if not exists online_or_offline text,
    add column if not exists newspaper_name text,
    add column if not exists page_no text,
    add column if not exists confidence_score integer,
    add column if not exists ocr_text text,
    add column if not exists language text,
    add column if not exists is_corrigendum boolean,
    add column if not exists linked_original_tender text,
    add column if not exists all_sources jsonb,
    add column if not exists source_count integer,
    add column if not exists first_seen_at timestamptz,
    add column if not exists last_seen_at timestamptz,
    add column if not exists status text,
    add column if not exists requires_manual_review boolean;

alter table if exists public.jobs
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
    add column if not exists confidence_score integer,
    add column if not exists online_or_offline text,
    add column if not exists all_sources jsonb,
    add column if not exists source_count integer,
    add column if not exists first_seen_at timestamptz,
    add column if not exists last_seen_at timestamptz,
    add column if not exists status text,
    add column if not exists requires_manual_review boolean;

commit;
