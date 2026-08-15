"""
Seed the database with default data so the app is usable immediately:
- 1 admin user
- 1 doctor user (Dr. D.P. Singh) + doctor profile, approved
- 1 patient test user
- 1 specialization (General Physician)
- 1 clinic (D.P. Singh Clinic, Himatnagar)
- Doctor availability: Monday-Saturday, 9 time slots per day

Run with:  python -m app.seed
"""
from app.database import SessionLocal, Base, engine
from app import models
from app.auth import hash_password

DEFAULT_SLOTS = [
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM",
    "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM",
]

# Monday=0 ... Saturday=5 (doctor works Mon-Sat, closed Sunday=6)
WORKING_DAYS = [0, 1, 2, 3, 4, 5]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # --- Specialization ---------------------------------------------------
        spec = db.query(models.Specialization).filter_by(name="General Physician").first()
        if not spec:
            spec = models.Specialization(name="General Physician")
            db.add(spec)
            db.flush()
            print("Created specialization: General Physician")

        # --- Clinic --------------------------------------------------------
        clinic = db.query(models.Clinic).filter_by(name="D.P. Singh Clinic").first()
        if not clinic:
            clinic = models.Clinic(
                name="D.P. Singh Clinic",
                address="Himatnagar, Gujarat",
                city="Himatnagar",
                phone="9999999999",
            )
            db.add(clinic)
            db.flush()
            print("Created clinic: D.P. Singh Clinic")

        # --- Admin user ------------------------------------------------------
        admin_user = db.query(models.User).filter_by(email="admin@medibook.com").first()
        if not admin_user:
            admin_user = models.User(
                full_name="MediBook Admin",
                email="admin@medibook.com",
                phone="9000000001",
                password_hash=hash_password("admin123"),
                role=models.UserRole.admin,
            )
            db.add(admin_user)
            print("Created admin user: admin@medibook.com / admin123")

        # --- Doctor user (Dr. D.P. Singh) ------------------------------------
        doctor_user = db.query(models.User).filter_by(email="doctor@medibook.com").first()
        if not doctor_user:
            doctor_user = models.User(
                full_name="Dr. D.P. Singh",
                email="doctor@medibook.com",
                phone="9000000002",
                password_hash=hash_password("doctor123"),
                role=models.UserRole.doctor,
            )
            db.add(doctor_user)
            db.flush()
            print("Created doctor user: doctor@medibook.com / doctor123")

        db.flush()

        doctor = db.query(models.Doctor).filter_by(user_id=doctor_user.id).first()
        if not doctor:
            doctor = models.Doctor(
                user_id=doctor_user.id,
                clinic_id=clinic.id,
                specialization_id=spec.id,
                bio="Experienced General Physician serving the Himatnagar community.",
                experience_years=10,
                consultation_fee=100.0,
                approval_status=models.DoctorApprovalStatus.approved,
                is_active=True,
            )
            db.add(doctor)
            db.flush()
            print("Created doctor profile for Dr. D.P. Singh (approved, active)")

        # --- Doctor availability ---------------------------------------------
        existing_slot_count = (
            db.query(models.DoctorAvailability).filter_by(doctor_id=doctor.id).count()
        )
        if existing_slot_count == 0:
            for day in WORKING_DAYS:
                for slot_time in DEFAULT_SLOTS:
                    db.add(
                        models.DoctorAvailability(
                            doctor_id=doctor.id, day_of_week=day, slot_time=slot_time
                        )
                    )
            print(f"Created availability: Mon-Sat x {len(DEFAULT_SLOTS)} slots/day")

        # --- Patient test user -------------------------------------------------
        patient_user = db.query(models.User).filter_by(email="patient@medibook.com").first()
        if not patient_user:
            patient_user = models.User(
                full_name="Test Patient",
                email="patient@medibook.com",
                phone="9000000003",
                password_hash=hash_password("patient123"),
                role=models.UserRole.patient,
            )
            db.add(patient_user)
            db.flush()
            print("Created patient user: patient@medibook.com / patient123")

        db.flush()
        patient = db.query(models.Patient).filter_by(user_id=patient_user.id).first()
        if not patient:
            db.add(models.Patient(user_id=patient_user.id))
            print("Created patient profile")

        db.commit()
        print("\nSeed complete. You can now log in with:")
        print("  Admin:   admin@medibook.com   / admin123")
        print("  Doctor:  doctor@medibook.com  / doctor123")
        print("  Patient: patient@medibook.com / patient123")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
