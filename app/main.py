from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, doctors, clinics, appointments, payments, admin, doctor_panel

# Create tables if they don't exist yet (Alembic is still the recommended
# way to manage schema changes - see alembic/ folder - but this keeps a
# fresh dev DB usable without running migrations first).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MediBook - Doctor Appointment Booking System",
    description="FastAPI backend for patient mobile app, doctor panel, and admin panel",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS - required so the React Native app (Expo), the doctor panel (React),
# and the admin panel (React) can all call this API from different origins.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # In addition to the explicit list above (used for any non-localhost /
    # production origins you add later), allow ANY http://localhost:<port>
    # or http://127.0.0.1:<port> origin. Vite/Expo dev servers frequently
    # pick a different port if the default one is busy (5173 -> 5174 ->
    # 5175 ...), which otherwise causes exactly the CORS errors seen during
    # development. This keeps local development frictionless without
    # weakening production security (regex only matches localhost/127.0.0.1).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(clinics.router)
app.include_router(appointments.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(doctor_panel.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "MediBook API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
