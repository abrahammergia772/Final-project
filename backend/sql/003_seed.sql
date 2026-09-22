-- =============================================================================
-- Wolaita Sodo Hospital — 003 training seed
-- If users.id is still uuid from the old schema, skip the users inserts below.
-- 001_schema.sql uses text ids. 004 does not convert an existing uuid column.
-- OPTIONAL. Run only on a training database, after 001 and 002.
-- These are the same demo accounts as the login page. Change or delete them
-- before any real patient data is stored.
--
-- password_hash values are SHA-256 of the demo passwords. The API accepts that
-- legacy form and writes a salted PBKDF2 hash when a password is changed.
--   python -c "import hashlib; print(hashlib.sha256(b'admin123').hexdigest())"
-- =============================================================================

insert into public.users (id, email, password_hash, name, role, status, department)
values
  ('U-001', 'admin@wsh.et',       '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Solomon Tadesse',  'admin',       'active', 'Administration'),
  ('U-002', 'manager@wsh.et',     '866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5', 'Hanna Bekele',     'manager',     'active', 'Management'),
  ('U-003', 'doctor@wsh.et',      'f348d5628621f3d8f59c8cabda0f8eb0aa7e0514a90be7571020b1336f26c113', 'Dr. Daniel Alemu', 'doctor',      'active', 'Internal Medicine'),
  ('U-004', 'nurse@wsh.et',       '35608f3146571aa100227a3e68290979ba8a452179a080f888625106076e7de2', 'Marta Tesfaye',    'nurse',       'active', 'General Ward'),
  ('U-005', 'pharmacist@wsh.et',  '64ebd689c7105960f79409d18408b9788122cdb02965c1674703a0383c5c9c69', 'Yonas Girma',      'pharmacist',  'active', 'Pharmacy'),
  ('U-006', 'laboratory@wsh.et',  '3705b578e8fcb1b82a94ad917881ec248bbd4111645e91aed3c19af12d82116f', 'Sara Worku',       'laboratory',  'active', 'Laboratory'),
  ('U-007', 'reception@wsh.et',   '5145dba3b6bda2d610d2c5c435a1c2481eefd3146b6a7e004ad73f794386e031', 'Liya Hailu',       'reception',   'active', 'Front Desk'),
  ('U-008', 'patient@wsh.et',     'd4587ea9ead060c13fd994f21ecfa7926272a78854a2c20136b10a3c9e53e71e', 'Abel Mekonnen',    'patient',     'active', '')
on conflict (email) do nothing;

-- Same laboratory password, for the older lab@wsh.et address used by the API demo list.
insert into public.users (id, email, password_hash, name, role, status, department)
values
  ('U-006b', 'lab@wsh.et', '3705b578e8fcb1b82a94ad917881ec248bbd4111645e91aed3c19af12d82116f', 'Sara Worku', 'laboratory', 'active', 'Laboratory')
on conflict (email) do nothing;

insert into public.patients (id, first_name, last_name, age, gender, phone, email, blood, address, condition, status)
values
  ('P-1001', 'Abel', 'Mekonnen', 34, 'Male', '+251 911 223 344', 'patient@wsh.et', 'O+', 'Sodo, Wolaita', 'Hypertension', 'active'),
  ('P-1002', 'Hanna', 'Bekele', 29, 'Female', '+251 912 334 455', 'hanna.bekele@wsh.et', 'A+', 'Sodo, Wolaita', 'Pneumonia', 'active')
on conflict (id) do nothing;

insert into public.departments (id, name, head, staff, beds, occupied, status)
values
  ('D-01', 'Internal Medicine', 'Dr. Daniel Alemu', 18, 6, 3, 'active'),
  ('D-02', 'Surgical', 'Dr. Mekdes', 12, 4, 3, 'active'),
  ('D-03', 'Maternity', 'Dr. Sara', 10, 3, 2, 'active'),
  ('D-04', 'Pediatrics', 'Dr. Fikru Debebe', 9, 3, 2, 'active'),
  ('D-05', 'ICU', 'Dr. Daniel Alemu', 8, 4, 2, 'active'),
  ('D-06', 'Emergency', 'Dr. on call', 11, 4, 2, 'active')
on conflict (id) do nothing;

insert into public.beds (id, ward, status, patient, dx, since, doctor)
values
  ('MED-01', 'Medical', 'occupied', 'Abel Mekonnen', 'Hypertension', '2d', 'Dr. Daniel Alemu'),
  ('MED-02', 'Medical', 'occupied', 'Hanna Bekele', 'Pneumonia', '1d', 'Dr. Daniel Alemu'),
  ('MED-03', 'Medical', 'available', '', '', '', ''),
  ('ICU-01', 'ICU', 'occupied', 'Daniel Alemu', 'DKA — critical', '8h', 'Dr. Daniel Alemu'),
  ('ICU-03', 'ICU', 'available', '', '', '', '')
on conflict (id) do nothing;

insert into public.bed_requests (id, name, mrn, sex, age, dx, ward, priority, note, doctor, status)
values
  ('BR-2041', 'Sara Worku', 'WSH-1044', 'F', '34', 'Respiratory distress', 'ICU', 'Emergency', 'Needs a monitored bed', 'Dr. Daniel Alemu', 'pending')
on conflict (id) do nothing;

insert into public.schema_migrations (id)
values ('003_seed')
on conflict (id) do nothing;
