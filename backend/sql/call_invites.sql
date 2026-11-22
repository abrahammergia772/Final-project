-- Run in the Supabase SQL editor. The FastAPI backend uses the service-role
-- key; browsers must never receive this key or access this table directly.
create table if not exists public.call_invites (
  call_id text not null,
  user_id text not null references public.users(id),
  caller_id text not null references public.users(id),
  caller_name text not null,
  mode text not null check (mode in ('audio', 'video')),
  room text not null,
  status text not null check (status in ('pending', 'accepted', 'declined', 'left', 'ended')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  primary key (call_id, user_id)
);
create index if not exists call_invites_user_status_idx on public.call_invites(user_id, status, expires_at);
alter table public.call_invites enable row level security;
revoke all on public.call_invites from anon, authenticated;
grant all on public.call_invites to service_role;
-- No browser-facing policies: access is only via the authenticated API.
