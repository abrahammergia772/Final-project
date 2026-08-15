-- =============================================================================
-- MedIQ Pro — Supabase schema
-- Run this in Supabase → SQL Editor (create a new project, paste, Run).
-- Creates the core tables + row-level-security policies.
-- =============================================================================

-- Users / accounts (used by POST /auth/login and /auth/signup)
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,          -- sha256 hex (upgrade to bcrypt/argon2 in production)
  name text not null default '',
  role text not null default 'patient', -- admin|manager|doctor|nurse|pharmacist|laboratory|reception|patient
  phone text default '',
  dob text default '',
  gender text default '',
  blood text default '',
  emergency_contact text default '',
  status text default 'active',         -- active|pending|inactive
  created_at timestamptz default now()
);

-- Patients
create table if not exists public.patients (
  id text primary key,
  first_name text, last_name text, age int, gender text,
  phone text, email text, blood text, address text,
  emergency text, condition text, last_visit text, status text default 'active'
);

-- Appointments
create table if not exists public.appointments (
  id text primary key,
  patient text, doctor text, dept text, date text, time text,
  type text, status text, no_show int default 0
);

-- Prescriptions
create table if not exists public.prescriptions (
  id text primary key,
  patient text, doctor text, date text, status text default 'active',
  drugs jsonb default '[]'::jsonb
);

-- Inventory
create table if not exists public.inventory (
  id text primary key,
  name text, category text, stock int, unit text, expiry text, status text
);

-- Lab requests & results
create table if not exists public.lab_requests (
  id text primary key, patient text, test text, doctor text,
  date text, priority text default 'Routine', status text default 'pending'
);
create table if not exists public.lab_results (
  id text primary key, patient text, test text, date text,
  status text, ai_flag text, values jsonb default '[]'::jsonb
);

-- Medications & care plans
create table if not exists public.medications (
  id text primary key, patient text, drug text, dose text,
  due text, status text default 'pending', time text default ''
);
create table if not exists public.care_plans (
  id text primary key, patient text, plan text, created text,
  updated text, status text, steps jsonb default '[]'::jsonb
);

-- Bills
create table if not exists public.bills (
  id text primary key, date text, description text, amount numeric, status text
);

-- Complaints (patient -> manager)
create table if not exists public.complaints (
  id text primary key, reporter text, reporter_role text default 'patient',
  category text, subject text, description text, priority text default 'normal',
  date text, status text default 'pending', solution text default '',
  resolved_by text default '', resolved_date text default ''
);

-- Messages
create table if not exists public.messages (
  id text primary key, "from" text, from_role text, subject text, body text,
  date text, read boolean default false, priority text default 'normal',
  replies jsonb default '[]'::jsonb
);

-- Announcements
create table if not exists public.announcements (
  id text primary key, title text, message text, audience text, author text,
  publish_date text, priority text default 'normal', status text default 'draft', views int default 0
);

-- Shifts / roster / attendance
create table if not exists public.shifts (
  id text primary key, name text, start text, end text, color text, css text, workers int default 0
);
create table if not exists public.roster (
  id text primary key, staff text, dept text, date text, shift text, start text, end text
);
create table if not exists public.attendance (
  id text primary key, staff text, dept text, date text, shift text,
  check_in text, check_out text, status text, source text default 'fingerprint', device text
);

-- Documents
create table if not exists public.documents (
  id text primary key, patient text, patient_id text, type text, title text,
  date text, size text, uploaded_by text, summary text
);

-- Other misc tables
create table if not exists public.audit_logs (
  id text primary key, ts text, "user" text, role text, action text,
  detail text default '', ip text, status text
);
create table if not exists public.insurance (
  id text primary key, patient text, provider text, policy text,
  coverage int, valid_until text, status text
);
create table if not exists public.samples (
  id text primary key, patient text, test text, type text,
  collected text, stage text default 'collected', tat text default '—'
);
create table if not exists public.queue (
  id text primary key, name text, dept text, arrived text, status text
);
create table if not exists public.departments (
  id text primary key, name text, head text, staff int, beds int, occupied int, status text
);
create table if not exists public.staff (
  id text primary key, name text, role text, dept text, shift text, status text, contact text
);
create table if not exists public.observations (
  id text primary key, time text, patient text, pain int, intake int,
  output int, temp numeric, nurse text, notes text
);
create table if not exists public.referrals (
  id text primary key, patient text, "to" text, specialty text, reason text,
  priority text, date text, status text default 'pending'
);
create table if not exists public.suppliers (
  id text primary key, name text, contact text, phone text, categories text,
  lead_time int, rating numeric
);
create table if not exists public.purchase_orders (
  id text primary key, supplier text, items jsonb default '[]'::jsonb,
  total numeric, date text, status text
);

-- =============================================================================
-- Row Level Security
-- =============================================================================
alter table public.users enable row level security;
alter table public.patients enable row level security;
alter table public.appointments enable row level security;

-- Allow anonymous read for demo simplicity; tighten in production:
create policy "anon read users" on public.users for select using (true);
create policy "anon read patients" on public.patients for select using (true);
create policy "anon read appointments" on public.appointments for select using (true);

-- Allow authenticated/service writes (adjust per role in production):
create policy "service full access users" on public.users for all using (true) with check (true);
create policy "service full access patients" on public.patients for all using (true) with check (true);
create policy "service full access appointments" on public.appointments for all using (true) with check (true);
