# Supabase SQL — run order

There is no Supabase project connected in this repository. `SUPABASE_URL` and `SUPABASE_KEY` are empty, so these files could not be applied to a live database from here. Run them yourself in **Supabase → SQL Editor**.

## New project

1. `001_schema.sql` — every table the API uses, including wards, bed requests, blood bank, ambulance, theatre, imaging, and cashier.
2. `002_security.sql` — turn on row level security and remove anon access.
3. `003_seed.sql` — **training only**. Demo accounts and a few sample rows. Do not run this on a database that will hold real patients.

`backend/supabase_schema.sql` is the same as steps 1 and 2 in one paste. It does not include the seed.

## Project that already ran the old schema

1. `004_upgrade_existing.sql`
2. `002_security.sql`
3. `003_seed.sql` only if you want the demo accounts.

## Required API settings

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SECRET_KEY=a-long-random-value
CORS_ORIGINS=https://your-frontend-host
CORS_ALLOW_ALL=0
```

The service-role key stays on the server. The frontend keys in `config.js` should stay empty. The anon key cannot read these tables.
