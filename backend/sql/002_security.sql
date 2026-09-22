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
