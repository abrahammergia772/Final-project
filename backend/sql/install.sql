-- =============================================================================
-- Wolaita Sodo Hospital — full install for a NEW Supabase project
-- Paste this file in Supabase → SQL Editor and run it once.
-- It creates tables and locks them down. It does not insert demo patients.
-- Training data is backend/sql/003_seed.sql and must be run separately.
-- An existing project should run backend/sql/004_upgrade_existing.sql, then
-- backend/sql/002_security.sql. Do not run this file on an existing database.
-- =============================================================================

-- =============================================================================
-- Wolaita Sodo Hospital — 001 schema
-- Run this first in Supabase → SQL Editor on a NEW project.
-- Safe to re-run: uses IF NOT EXISTS. It will not alter tables that already
-- exist. If you already ran the old backend/supabase_schema.sql, run
-- 004_upgrade_existing.sql instead of this file.
--
-- The API stores dates as text because the frontend sends display dates
-- ("2026-09-22", "09:00"). Do not change those columns to date/time unless
-- the API is changed at the same time.
-- Password hashes are written by the API. Never insert a plaintext password.
-- =============================================================================

create extension if not exists pgcrypto;

create table if not exists public.schema_migrations (
  id text primary key,
  applied_at timestamptz not null default now()
);

-- Accounts. id is text so both generated ids and U-001 style ids work.
create table if not exists public.users (
  id text primary key default gen_random_uuid()::text,
  email text not null,
  password_hash text not null,
  name text not null default '',
  role text not null default 'patient',
  phone text not null default '',
  dob text not null default '',
  gender text not null default '',
  blood text not null default '',
  emergency_contact text not null default '',
  status text not null default 'active',
  department text not null default '',
  last_login text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint users_email_unique unique (email),
  constraint users_role_chk check (
    role in ('admin','manager','doctor','nurse','pharmacist','laboratory','reception','patient')
  ),
  constraint users_status_chk check (status in ('active','pending','inactive'))
);

create table if not exists public.patients (
  id text primary key,
  first_name text not null default '',
  last_name text not null default '',
  age int,
  gender text not null default '',
  phone text not null default '',
  email text not null default '',
  blood text not null default '',
  address text not null default '',
  emergency text not null default '',
  condition text not null default '',
  last_visit text not null default '',
  status text not null default 'active',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.appointments (
  id text primary key,
  patient text not null default '',
  doctor text not null default '',
  dept text not null default '',
  date text not null default '',
  time text not null default '',
  type text not null default '',
  status text not null default 'confirmed',
  no_show int not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.prescriptions (
  id text primary key,
  patient text not null default '',
  doctor text not null default '',
  date text not null default '',
  status text not null default 'active',
  drugs jsonb not null default '[]'::jsonb,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.inventory (
  id text primary key,
  name text not null default '',
  category text not null default '',
  stock int not null default 0,
  unit text not null default '',
  expiry text not null default '',
  status text not null default 'in-stock',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.lab_requests (
  id text primary key,
  patient text not null default '',
  test text not null default '',
  doctor text not null default '',
  date text not null default '',
  priority text not null default 'Routine',
  status text not null default 'pending',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.lab_results (
  id text primary key,
  patient text not null default '',
  test text not null default '',
  date text not null default '',
  status text not null default '',
  ai_flag text not null default '',
  values jsonb not null default '[]'::jsonb,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.medications (
  id text primary key,
  patient text not null default '',
  drug text not null default '',
  dose text not null default '',
  due text not null default '',
  status text not null default 'pending',
  time text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.care_plans (
  id text primary key,
  patient text not null default '',
  plan text not null default '',
  created text not null default '',
  updated text not null default '',
  status text not null default 'active',
  steps jsonb not null default '[]'::jsonb,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.bills (
  id text primary key,
  date text not null default '',
  description text not null default '',
  amount numeric not null default 0,
  status text not null default 'pending',
  patient text not null default '',
  service text not null default '',
  method text not null default '',
  paid numeric not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.complaints (
  id text primary key,
  reporter text not null default '',
  reporter_role text not null default 'patient',
  category text not null default '',
  subject text not null default '',
  description text not null default '',
  priority text not null default 'normal',
  date text not null default '',
  status text not null default 'pending',
  solution text not null default '',
  resolved_by text not null default '',
  resolved_date text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  id text primary key,
  "from" text not null default '',
  from_role text not null default '',
  subject text not null default '',
  body text not null default '',
  date text not null default '',
  read boolean not null default false,
  priority text not null default 'normal',
  replies jsonb not null default '[]'::jsonb,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.announcements (
  id text primary key,
  title text not null default '',
  message text not null default '',
  audience text not null default 'all',
  author text not null default '',
  publish_date text not null default '',
  priority text not null default 'normal',
  status text not null default 'draft',
  views int not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.shifts (
  id text primary key,
  name text not null default '',
  start text not null default '',
  "end" text not null default '',
  color text not null default '',
  css text not null default '',
  workers int not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.roster (
  id text primary key,
  staff text not null default '',
  dept text not null default '',
  date text not null default '',
  shift text not null default '',
  start text not null default '',
  "end" text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.attendance (
  id text primary key,
  staff text not null default '',
  dept text not null default '',
  date text not null default '',
  shift text not null default '',
  check_in text not null default '',
  check_out text not null default '',
  status text not null default '',
  source text not null default 'manual',
  device text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.documents (
  id text primary key,
  patient text not null default '',
  patient_id text not null default '',
  type text not null default '',
  title text not null default '',
  date text not null default '',
  size text not null default '',
  uploaded_by text not null default '',
  summary text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id text primary key,
  ts text not null default '',
  "user" text not null default '',
  role text not null default '',
  action text not null default '',
  detail text not null default '',
  ip text not null default '',
  status text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.insurance (
  id text primary key,
  patient text not null default '',
  provider text not null default '',
  policy text not null default '',
  coverage int not null default 0,
  valid_until text not null default '',
  status text not null default 'active',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.samples (
  id text primary key,
  patient text not null default '',
  test text not null default '',
  type text not null default '',
  collected text not null default '',
  stage text not null default 'collected',
  tat text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.queue (
  id text primary key,
  name text not null default '',
  dept text not null default '',
  arrived text not null default '',
  status text not null default 'waiting',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.departments (
  id text primary key,
  name text not null default '',
  head text not null default '',
  staff int not null default 0,
  beds int not null default 0,
  occupied int not null default 0,
  status text not null default 'active',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.staff (
  id text primary key,
  name text not null default '',
  role text not null default '',
  dept text not null default '',
  shift text not null default '',
  status text not null default 'active',
  contact text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.observations (
  id text primary key,
  time text not null default '',
  patient text not null default '',
  pain int,
  intake int,
  output int,
  temp numeric,
  nurse text not null default '',
  notes text not null default '',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.referrals (
  id text primary key,
  patient text not null default '',
  "to" text not null default '',
  specialty text not null default '',
  reason text not null default '',
  priority text not null default 'routine',
  date text not null default '',
  status text not null default 'pending',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.suppliers (
  id text primary key,
  name text not null default '',
  contact text not null default '',
  phone text not null default '',
  categories text not null default '',
  lead_time int not null default 0,
  rating numeric,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.purchase_orders (
  id text primary key,
  supplier text not null default '',
  items jsonb not null default '[]'::jsonb,
  total numeric not null default 0,
  date text not null default '',
  status text not null default 'draft',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

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
  hr numeric,
  sys numeric,
  dia numeric,
  temp numeric,
  spo2 numeric,
  rr numeric,
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

-- Wards. Other staff should only be shown occupied/isolation rows in the UI.
-- The table still stores empty beds so a doctor can approve a request into one.
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
  created_at timestamptz not null default now(),
  constraint beds_status_chk check (
    status in ('occupied','available','cleaning','reserved','isolation')
  )
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
  created_at timestamptz not null default now(),
  constraint bed_requests_status_chk check (status in ('pending','approved','cancelled'))
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
  created_at timestamptz not null default now(),
  constraint blood_units_status_chk check (status in ('available','reserved','issued','discarded'))
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

-- Lookups the API and the ward board use most often.
create unique index if not exists users_email_lower_idx on public.users (lower(email));
create index if not exists patients_email_idx on public.patients (lower(email));
create index if not exists patients_status_idx on public.patients (status);
create index if not exists appointments_date_idx on public.appointments (date);
create index if not exists appointments_status_idx on public.appointments (status);
create index if not exists beds_ward_idx on public.beds (ward);
create index if not exists beds_status_idx on public.beds (status);
create index if not exists bed_requests_status_idx on public.bed_requests (status);
create index if not exists bed_requests_doctor_idx on public.bed_requests (doctor);
create index if not exists blood_units_type_idx on public.blood_units (type);
create index if not exists blood_units_expires_idx on public.blood_units (expires);
create index if not exists bills_status_idx on public.bills (status);
create index if not exists cashier_status_idx on public.cashier_invoices (status);
create index if not exists lab_requests_status_idx on public.lab_requests (status);
create index if not exists messages_read_idx on public.messages (read);

insert into public.schema_migrations (id)
values ('001_schema')
on conflict (id) do nothing;

-- =============================================================================
-- Wolaita Sodo Hospital — 002 security
-- Run after 001_schema.sql, or after 004_upgrade_existing.sql.
--
-- The FastAPI server connects with the Supabase service_role key and enforces
-- roles itself. service_role bypasses row level security. The anon key and
-- the logged-in Supabase Auth role get no access. Do not put the service_role
-- key in the frontend, and do not add an anon SELECT policy.
-- =============================================================================

create table if not exists public.schema_migrations (
  id text primary key,
  applied_at timestamptz not null default now()
);

do $$
declare
  t text;
  tables text[] := array[
    'users','patients','appointments','prescriptions','inventory',
    'lab_requests','lab_results','medications','care_plans','bills',
    'complaints','messages','announcements','shifts','roster','attendance',
    'documents','audit_logs','insurance','samples','queue','departments',
    'staff','observations','referrals','suppliers','purchase_orders',
    'notifications','fingerprint_devices','videos','vitals','finance',
    'beds','bed_requests','blood_units','ambulances','ambulance_missions',
    'theatre_cases','imaging_studies','cashier_invoices'
  ];
begin
  foreach t in array tables loop
    if to_regclass('public.' || t) is null then
      raise exception 'Missing table public.%. Run 001_schema.sql first.', t;
    end if;
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on table public.%I from public', t);
    execute format('revoke all on table public.%I from anon', t);
    execute format('revoke all on table public.%I from authenticated', t);
    execute format('grant select, insert, update, delete on table public.%I to service_role', t);
  end loop;
end $$;

revoke all on table public.schema_migrations from anon, authenticated;
grant select, insert, update, delete on table public.schema_migrations to service_role;

comment on table public.users is
  'Accounts. password_hash is an application hash (pbkdf2 or legacy sha256), never a plaintext password.';

insert into public.schema_migrations (id)
values ('002_security')
on conflict (id) do nothing;

-- Run this if you already created the other tables and need the settings table.

create table if not exists public.app_settings (
  id text primary key,
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.app_settings enable row level security;
revoke all on table public.app_settings from public, anon, authenticated;
grant select, insert, update, delete on table public.app_settings to service_role;
