-- =============================================================================
-- MediBook — Doctor Appointment Booking System
-- Raw SQL schema for use with Neon (or any managed Postgres).
--
-- This matches backend/app/models.py exactly. Use THIS FILE **instead of**
-- letting the FastAPI app auto-create tables (i.e. remove/skip the
-- `Base.metadata.create_all(bind=engine)` line in app/main.py, or just run
-- this once and the app's create_all will see the tables already exist and
-- do nothing on subsequent runs — either works, but don't run this file
-- AND expect a totally empty DB after create_all also ran, to avoid
-- confusing duplicate-object errors).
--
-- How to run this on Neon:
--   1. Go to your Neon project -> SQL Editor
--   2. Paste this whole file and click "Run"
--   3. Copy your Neon connection string into backend/.env as DATABASE_URL
--      (Neon gives you a string like:
--       postgresql://<user>:<password>@<host>/<dbname>?sslmode=require)
-- =============================================================================

-- Extension for gen_random_uuid() (Neon has this available by default)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- ENUM TYPES
-- -----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'doctor', 'patient');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE doctor_approval_status AS ENUM ('pending', 'approved', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE appointment_status AS ENUM ('pending', 'booked', 'accepted', 'rejected', 'completed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('pending', 'success', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -----------------------------------------------------------------------------
-- USERS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    full_name      TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    phone          TEXT,
    password_hash  TEXT NOT NULL,
    role           user_role NOT NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- -----------------------------------------------------------------------------
-- SPECIALIZATIONS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS specializations (
    id    TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name  TEXT NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- CLINICS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinics (
    id       TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name     TEXT NOT NULL,
    address  TEXT NOT NULL,
    city     TEXT NOT NULL,
    phone    TEXT
);

-- -----------------------------------------------------------------------------
-- PATIENTS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id        TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    gender         TEXT,
    date_of_birth  DATE,
    address        TEXT
);

-- -----------------------------------------------------------------------------
-- DOCTORS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id             TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    clinic_id           TEXT REFERENCES clinics(id) ON DELETE SET NULL,
    specialization_id   TEXT REFERENCES specializations(id) ON DELETE SET NULL,
    bio                 TEXT,
    experience_years    INTEGER NOT NULL DEFAULT 0,
    consultation_fee    DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    approval_status     doctor_approval_status NOT NULL DEFAULT 'approved',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);

-- -----------------------------------------------------------------------------
-- DOCTOR AVAILABILITY (weekly recurring slots)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctor_availability (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    doctor_id     TEXT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    day_of_week   INTEGER NOT NULL,   -- 0=Monday ... 6=Sunday
    slot_time     TEXT NOT NULL,      -- e.g. '10:00 AM'
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_doctor_day_slot UNIQUE (doctor_id, day_of_week, slot_time)
);

-- -----------------------------------------------------------------------------
-- APPOINTMENTS
-- (payment_id FK added AFTER the payments table exists, since the two
--  tables reference each other)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id          TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id           TEXT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date    DATE NOT NULL,
    appointment_time    TEXT NOT NULL,   -- e.g. '10:00 AM'
    status              appointment_status NOT NULL DEFAULT 'pending',
    payment_id          TEXT,            -- FK added below
    notes               TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_doctor_date_time_slot UNIQUE (doctor_id, appointment_date, appointment_time)
);

-- -----------------------------------------------------------------------------
-- PAYMENTS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    id               TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    appointment_id   TEXT REFERENCES appointments(id) ON DELETE SET NULL,
    patient_id       TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id        TEXT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    amount           DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    payment_status   payment_status NOT NULL DEFAULT 'pending',
    payment_method   TEXT NOT NULL DEFAULT 'dummy',
    transaction_id   TEXT UNIQUE NOT NULL DEFAULT gen_random_uuid()::text,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Now that payments exists, wire up the appointments.payment_id FK
DO $$ BEGIN
    ALTER TABLE appointments
        ADD CONSTRAINT fk_appointments_payment
        FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -----------------------------------------------------------------------------
-- REVIEWS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id               TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    appointment_id   TEXT NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE CASCADE,
    patient_id       TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id        TEXT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    rating           INTEGER NOT NULL DEFAULT 5,
    comment          TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- SEED DATA — matches backend/app/seed.py exactly
-- Passwords below are bcrypt hashes of: admin123 / doctor123 / patient123
-- =============================================================================

-- Specialization
INSERT INTO specializations (id, name)
VALUES ('11111111-1111-1111-1111-111111111101', 'General Physician')
ON CONFLICT (name) DO NOTHING;

-- Clinic
INSERT INTO clinics (id, name, address, city, phone)
VALUES (
    '11111111-1111-1111-1111-111111111102',
    'D.P. Singh Clinic',
    'Himatnagar, Gujarat',
    'Himatnagar',
    '9999999999'
)
ON CONFLICT DO NOTHING;

-- Admin user
INSERT INTO users (id, full_name, email, phone, password_hash, role, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111103',
    'MediBook Admin',
    'admin@medibook.com',
    '9000000001',
    '$2b$12$xUA08e5tBQX2sbgqUIn5.O6tjAgkYGZyGyHA35G.gcnr5vXoP/QNS', -- admin123
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Doctor user + profile (Dr. D.P. Singh)
INSERT INTO users (id, full_name, email, phone, password_hash, role, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111104',
    'Dr. D.P. Singh',
    'doctor@medibook.com',
    '9000000002',
    '$2b$12$4xbP3TxFlTMIcTWCe3bCrutdoabWhpdlVP1Vw.ZRTyth40UMLAaeG', -- doctor123
    'doctor',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO doctors (
    id, user_id, clinic_id, specialization_id, bio,
    experience_years, consultation_fee, approval_status, is_active
)
VALUES (
    '11111111-1111-1111-1111-111111111105',
    '11111111-1111-1111-1111-111111111104',
    '11111111-1111-1111-1111-111111111102',
    '11111111-1111-1111-1111-111111111101',
    'Experienced General Physician serving the Himatnagar community.',
    10,
    100.0,
    'approved',
    TRUE
)
ON CONFLICT (user_id) DO NOTHING;

-- Doctor availability: Monday(0)-Saturday(5), 9 slots/day
INSERT INTO doctor_availability (doctor_id, day_of_week, slot_time)
SELECT '11111111-1111-1111-1111-111111111105', d, s
FROM unnest(ARRAY[0,1,2,3,4,5]) AS d
CROSS JOIN unnest(ARRAY[
    '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM', '12:00 PM',
    '05:00 PM', '05:30 PM', '06:00 PM', '06:30 PM'
]) AS s
ON CONFLICT (doctor_id, day_of_week, slot_time) DO NOTHING;

-- Patient test user
INSERT INTO users (id, full_name, email, phone, password_hash, role, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111106',
    'Test Patient',
    'patient@medibook.com',
    '9000000003',
    '$2b$12$ZcsdSnNGKk9s7tfJUFadv.SeQV/PIuTpdEpTFUQi.68BLuh.FK9JK', -- patient123
    'patient',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO patients (id, user_id)
VALUES (
    '11111111-1111-1111-1111-111111111107',
    '11111111-1111-1111-1111-111111111106'
)
ON CONFLICT (user_id) DO NOTHING;

-- =============================================================================
-- Done. You should now have:
--   Admin:   admin@medibook.com   / admin123
--   Doctor:  doctor@medibook.com  / doctor123
--   Patient: patient@medibook.com / patient123
-- and Dr. D.P. Singh / D.P. Singh Clinic ready to show up in the app.
-- =============================================================================
