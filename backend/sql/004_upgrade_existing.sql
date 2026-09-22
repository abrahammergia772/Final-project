-- =============================================================================
-- Wolaita Sodo Hospital — 004 upgrade
-- Run this if you already executed the older backend/supabase_schema.sql.
-- It adds missing columns and the new hospital tables. It does not delete data
-- and it does not change users.id if that column is already uuid.
-- After this file, run 002_security.sql again.
-- =============================================================================

create extension if not exists pgcrypto;

create table if not exists public.schema_migrations (
  id text primary key,
  applied_at timestamptz not null default now()
);

alter table public.users add column if not exists department text not null default '';
alter table public.users add column if not exists last_login text not null default '';
alter table public.users add column if not exists details jsonb not null default '{}'::jsonb;

alter table public.patients add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.patients add column if not exists created_at timestamptz not null default now();

alter table public.appointments add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.appointments add column if not exists created_at timestamptz not null default now();

alter table public.prescriptions add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.prescriptions add column if not exists created_at timestamptz not null default now();

alter table public.inventory add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.inventory add column if not exists created_at timestamptz not null default now();

alter table public.lab_requests add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.lab_requests add column if not exists created_at timestamptz not null default now();

alter table public.lab_results add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.lab_results add column if not exists created_at timestamptz not null default now();

alter table public.medications add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.medications add column if not exists created_at timestamptz not null default now();

alter table public.care_plans add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.care_plans add column if not exists created_at timestamptz not null default now();

alter table public.bills add column if not exists patient text not null default '';
alter table public.bills add column if not exists service text not null default '';
alter table public.bills add column if not exists method text not null default '';
alter table public.bills add column if not exists paid numeric not null default 0;
alter table public.bills add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.bills add column if not exists created_at timestamptz not null default now();

alter table public.complaints add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.complaints add column if not exists created_at timestamptz not null default now();

alter table public.messages add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.messages add column if not exists created_at timestamptz not null default now();

alter table public.announcements add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.announcements add column if not exists created_at timestamptz not null default now();

alter table public.shifts add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.shifts add column if not exists created_at timestamptz not null default now();

alter table public.roster add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.roster add column if not exists created_at timestamptz not null default now();

alter table public.attendance add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.attendance add column if not exists created_at timestamptz not null default now();

alter table public.documents add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.documents add column if not exists created_at timestamptz not null default now();

alter table public.audit_logs add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.audit_logs add column if not exists created_at timestamptz not null default now();

alter table public.insurance add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.insurance add column if not exists created_at timestamptz not null default now();

alter table public.samples add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.samples add column if not exists created_at timestamptz not null default now();

alter table public.queue add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.queue add column if not exists created_at timestamptz not null default now();

alter table public.departments add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.departments add column if not exists created_at timestamptz not null default now();

alter table public.staff add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.staff add column if not exists created_at timestamptz not null default now();

alter table public.observations add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.observations add column if not exists created_at timestamptz not null default now();

alter table public.referrals add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.referrals add column if not exists created_at timestamptz not null default now();

alter table public.suppliers add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.suppliers add column if not exists created_at timestamptz not null default now();

alter table public.purchase_orders add column if not exists details jsonb not null default '{}'::jsonb;
alter table public.purchase_orders add column if not exists created_at timestamptz not null default now();

-- New tables. Same definitions as 001, kept here so an old project can upgrade
-- without recreating patients, users, or appointments.
create table if not exists public.notifications (
  id text primary key,
  title text not null default '',
  body text not null default '',
  audience text not null default 'all',
  read boolean not null default false,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.fingerprint_devices (
  id text primary key,
  name text not null default '',
  location text not null default '',
  status text not null default 'online',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.videos (
  id text primary key,
  title text not null default '',
  url text not null default '',
  topic text not null default '',
  audience text not null default 'all',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.vitals (
  id text primary key,
  patient text not null default '',
  t text not null default '',
  hr numeric, sys numeric, dia numeric, temp numeric, spo2 numeric, rr numeric,
  nurse text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.finance (
  id text primary key,
  date text not null default '',
  category text not null default '',
  description text not null default '',
  amount numeric not null default 0,
  status text not null default 'posted',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.beds (
  id text primary key,
  ward text not null,
  status text not null default 'available',
  patient text not null default '',
  dx text not null default '',
  since text not null default '',
  doctor text not null default '',
  mrn text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.bed_requests (
  id text primary key,
  name text not null,
  mrn text not null default '',
  sex text not null default '',
  age text not null default '',
  dx text not null default '',
  ward text not null,
  priority text not null default 'Urgent',
  note text not null default '',
  doctor text not null default '',
  status text not null default 'pending',
  bed_id text not null default '',
  at text not null default '',
  approved_at text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.blood_units (
  id text primary key,
  type text not null,
  donor text not null default '',
  collected text not null default '',
  expires text not null default '',
  status text not null default 'available',
  "for" text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.ambulances (
  id text primary key,
  crew text not null default '',
  status text not null default 'available',
  place text not null default '',
  eta text not null default '',
  "case" text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.ambulance_missions (
  id text primary key,
  unit_id text not null default '',
  time text not null default '',
  "text" text not null default '',
  place text not null default '',
  status text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.theatre_cases (
  id text primary key,
  theatre text not null default '',
  time text not null default '',
  patient text not null default '',
  proc text not null default '',
  surgeon text not null default '',
  anaesth text not null default '',
  status text not null default 'scheduled',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.imaging_studies (
  id text primary key,
  patient text not null default '',
  study text not null default '',
  priority text not null default 'Routine',
  status text not null default 'scheduled',
  note text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.cashier_invoices (
  id text primary key,
  patient text not null default '',
  service text not null default '',
  amount numeric not null default 0,
  paid numeric not null default 0,
  method text not null default '',
  status text not null default 'unpaid',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists beds_ward_idx on public.beds (ward);
create index if not exists beds_status_idx on public.beds (status);
create index if not exists bed_requests_status_idx on public.bed_requests (status);
create index if not exists blood_units_type_idx on public.blood_units (type);

insert into public.schema_migrations (id)
values ('004_upgrade_existing')
on conflict (id) do nothing;
