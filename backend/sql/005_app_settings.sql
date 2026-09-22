-- Run this if you already created the other tables and need the settings table.

create table if not exists public.app_settings (
  id text primary key,
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.app_settings enable row level security;
revoke all on table public.app_settings from public, anon, authenticated;
grant select, insert, update, delete on table public.app_settings to service_role;
