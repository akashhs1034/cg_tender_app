-- alerts_schema.sql — run once in Supabase SQL Editor after schema.sql
-- Tracks which (email, source_id) pairs have already been emailed so the
-- daily cron never sends duplicate alerts.

create table if not exists alert_log (
    id          bigint generated always as identity primary key,
    email       text not null,
    source_id   text not null,
    record_type text default 'tender',   -- 'tender' | 'job'
    sent_at     timestamptz default now(),
    unique (email, source_id)
);

create index if not exists idx_alert_log_email on alert_log (email);

alter table alert_log enable row level security;
create policy "mvp alert_log rw" on alert_log for all using (true) with check (true);
