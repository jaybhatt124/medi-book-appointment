# MediBook — Doctor Appointment Booking System

Full stack rebuild: FastAPI + PostgreSQL backend, React Native (Expo) patient app,
React.js doctor panel, React.js admin panel.

## Why doctors/clinics weren't showing (root causes fixed)

Since no existing codebase was provided to inspect, this project was built fresh
to the exact spec, with the two most common causes of "empty doctor list after
patient login" deliberately engineered around:

1. **Role-restricted `GET /doctors` / `GET /clinics`.** A very common bug is
   putting an admin-only or doctor-only dependency on these endpoints. Here,
   `GET /doctors` and `GET /clinics` only require *any authenticated user*
   (`get_current_user`, not `require_admin`/`require_doctor`) — see
   `backend/app/routers/doctors.py` and `backend/app/routers/clinics.py`. Any
   logged-in patient can call them.
2. **JWT token not attached to requests.** The mobile app's axios instance
   (`mobile-app/src/api/api.js`) uses a request interceptor that reads the
   token from `AsyncStorage` and attaches `Authorization: Bearer <token>` to
   *every* request automatically, so screens never forget to send it.
3. **Doctor not approved / not active.** `GET /doctors` only returns doctors
   where `is_active = true` AND `approval_status = 'approved'`. The seed
   script creates Dr. D.P. Singh already approved and active so he shows up
   immediately.
4. **Empty database.** `backend/app/seed.py` populates a default admin,
   doctor (Dr. D.P. Singh / D.P. Singh Clinic), patient, specialization, and
   Mon–Sat availability so there's always something to see.

If you paste in your actual existing code later, check those same four things
first — they cover the overwhelming majority of "list is empty" bugs.

## Project structure

```
backend/         FastAPI + SQLAlchemy + PostgreSQL + Alembic (all APIs)
mobile-app/       React Native Expo — patient app
doctor-panel/    React.js — doctor website
admin-panel/     React.js — admin website
docker-compose.yml  Postgres + backend, one command to run the API
```

## Quick start (backend)

```bash
cd backend
cp .env.example .env          # edit DATABASE_URL if needed
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A: run migrations
alembic revision --autogenerate -m "init"
alembic upgrade head

# Option B (simplest for local dev): let the app create tables itself
python -m app.seed             # creates tables + seeds default data
uvicorn app.main:app --reload  # http://localhost:8000
```

Or with Docker (Postgres + backend in one shot):

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs

### Default logins (seeded)

| Role    | Email                 | Password   |
|---------|------------------------|-----------|
| Admin   | admin@medibook.com     | admin123  |
| Doctor  | doctor@medibook.com    | doctor123 |
| Patient | patient@medibook.com   | patient123|

## Quick start (doctor panel)

```bash
cd doctor-panel
cp .env.example .env      # VITE_API_URL=http://localhost:8000
npm install
npm run dev                # http://localhost:5174
```

## Quick start (admin panel)

```bash
cd admin-panel
cp .env.example .env      # VITE_API_URL=http://localhost:8000
npm install
npm run dev                # http://localhost:5175
```

## Quick start (patient mobile app)

```bash
cd mobile-app
npm install
npx expo start
```

Open in Expo Go on your phone, or press `w` for web / `a` for Android emulator.

**Important:** edit `mobile-app/src/api/api.js` and set `DEV_API_URL` to your
computer's LAN IP (e.g. `http://192.168.1.5:8000`) if testing on a physical
phone — `localhost` only resolves correctly for the iOS simulator, and
Android emulators need `http://10.0.2.2:8000`.

## Booking flow (pay-then-book, as required)

1. Patient picks a doctor, date, and time slot (`GET /doctors/{id}/slots`).
2. `POST /payments/create` — creates a `pending` Payment row for that
   doctor/date/slot. No appointment exists yet.
3. `POST /payments/success` — dummy payment gateway, always succeeds on
   button click, marks the Payment `success`.
4. `POST /appointments/book-after-payment` — only creates the Appointment
   row if the linked Payment is `success`; re-checks the slot is still free
   (race-condition guard) before inserting.
5. The `appointments` table has a unique constraint on
   `(doctor_id, appointment_date, appointment_time)` so the same slot can
   never be double-booked at the database level, on top of the application
   checks.

## Notes

- All money amounts are in ₹ (INR), fee defaults to ₹100 per the spec.
- Payment integration is a dummy/fake flow as requested — no real gateway.
  It's a genuine two-step flow (`/payments/create` → `/payments/success` →
  `/appointments/book-after-payment`), just without a real payment provider
  behind it, so swapping in Razorpay/Stripe later only touches the
  `payments` router, nothing else.
- **CORS is dev-friendly by default**: the backend allows any
  `http://localhost:<port>` or `http://127.0.0.1:<port>` origin
  automatically (see `allow_origin_regex` in `app/main.py`), so it doesn't
  matter which port Vite/Expo happen to pick for the doctor panel, admin
  panel, or web preview. `CORS_ORIGINS` in `.env` is only needed for
  non-localhost origins once you deploy.
- Confirmed working dependency versions as of this build: Expo SDK
  `54.0.36`, React `19.1.0`, React Native `0.81.5`. If `npx expo install
  --fix` ever suggests different versions later, that's expected — Expo
  SDKs get patched over time; just follow its suggestions.
