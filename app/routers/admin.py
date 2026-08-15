from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.deps import require_admin
from app.auth import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=schemas.AdminDashboardOut)
def admin_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    total_doctors = db.query(models.Doctor).count()
    total_patients = db.query(models.Patient).count()
    total_appointments = db.query(models.Appointment).count()
    total_clinics = db.query(models.Clinic).count()
    successful_payments = (
        db.query(models.Payment).filter(models.Payment.payment_status == models.PaymentStatus.success).all()
    )
    pending_approvals = (
        db.query(models.Doctor)
        .filter(models.Doctor.approval_status == models.DoctorApprovalStatus.pending)
        .count()
    )

    return schemas.AdminDashboardOut(
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_clinics=total_clinics,
        total_payments_success=len(successful_payments),
        total_earnings=sum(p.amount for p in successful_payments),
        pending_doctor_approvals=pending_approvals,
    )


# ---------------------------------------------------------------------------
# DOCTORS
# ---------------------------------------------------------------------------
def _doctor_out(doctor: models.Doctor) -> schemas.DoctorOut:
    return schemas.DoctorOut(
        id=doctor.id,
        full_name=doctor.user.full_name,
        email=doctor.user.email,
        phone=doctor.user.phone,
        bio=doctor.bio,
        experience_years=doctor.experience_years,
        consultation_fee=doctor.consultation_fee,
        approval_status=doctor.approval_status,
        is_active=doctor.is_active,
        clinic=schemas.ClinicOut.model_validate(doctor.clinic) if doctor.clinic else None,
        specialization=schemas.SpecializationOut.model_validate(doctor.specialization)
        if doctor.specialization
        else None,
    )


@router.get("/doctors", response_model=List[schemas.DoctorOut])
def list_all_doctors(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    doctors = (
        db.query(models.Doctor)
        .options(
            joinedload(models.Doctor.user),
            joinedload(models.Doctor.clinic),
            joinedload(models.Doctor.specialization),
        )
        .all()
    )
    return [_doctor_out(d) for d in doctors]


@router.post("/doctors", response_model=schemas.DoctorOut)
def add_doctor(payload: schemas.AdminDoctorCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=models.UserRole.doctor,
    )
    db.add(user)
    db.flush()

    doctor = models.Doctor(
        user_id=user.id,
        clinic_id=payload.clinic_id,
        specialization_id=payload.specialization_id,
        bio=payload.bio,
        experience_years=payload.experience_years,
        consultation_fee=payload.consultation_fee,
        approval_status=models.DoctorApprovalStatus.approved,
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return _doctor_out(doctor)


@router.patch("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def edit_doctor(doctor_id: str, payload: schemas.AdminDoctorUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data or "phone" in data:
        if data.get("full_name"):
            doctor.user.full_name = data.pop("full_name")
        if data.get("phone"):
            doctor.user.phone = data.pop("phone")

    for field, value in data.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    return _doctor_out(doctor)


@router.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    user = doctor.user
    db.delete(doctor)
    if user:
        db.delete(user)
    db.commit()
    return {"detail": "Doctor deleted"}


@router.patch("/doctors/{doctor_id}/approve", response_model=schemas.DoctorOut)
def approve_doctor(doctor_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.approval_status = models.DoctorApprovalStatus.approved
    doctor.is_active = True
    db.commit()
    db.refresh(doctor)
    return _doctor_out(doctor)


@router.patch("/doctors/{doctor_id}/reject", response_model=schemas.DoctorOut)
def reject_doctor(doctor_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.approval_status = models.DoctorApprovalStatus.rejected
    db.commit()
    db.refresh(doctor)
    return _doctor_out(doctor)


# ---------------------------------------------------------------------------
# PATIENTS
# ---------------------------------------------------------------------------
@router.get("/patients", response_model=List[schemas.PatientOut])
def list_patients(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    patients = db.query(models.Patient).options(joinedload(models.Patient.user)).all()
    return [
        schemas.PatientOut(
            id=p.id, full_name=p.user.full_name, email=p.user.email, phone=p.user.phone, is_active=p.user.is_active
        )
        for p in patients
    ]


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    user = patient.user
    db.delete(patient)
    if user:
        db.delete(user)
    db.commit()
    return {"detail": "Patient deleted"}


# ---------------------------------------------------------------------------
# CLINICS
# ---------------------------------------------------------------------------
@router.get("/clinics", response_model=List[schemas.ClinicOut])
def admin_list_clinics(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    return db.query(models.Clinic).all()


@router.post("/clinics", response_model=schemas.ClinicOut)
def admin_add_clinic(payload: schemas.ClinicCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    clinic = models.Clinic(**payload.model_dump())
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return clinic


@router.patch("/clinics/{clinic_id}", response_model=schemas.ClinicOut)
def admin_edit_clinic(clinic_id: str, payload: schemas.ClinicUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)
    db.commit()
    db.refresh(clinic)
    return clinic


@router.delete("/clinics/{clinic_id}")
def admin_delete_clinic(clinic_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    db.delete(clinic)
    db.commit()
    return {"detail": "Clinic deleted"}


# ---------------------------------------------------------------------------
# SPECIALIZATIONS
# ---------------------------------------------------------------------------
@router.get("/specializations", response_model=List[schemas.SpecializationOut])
def admin_list_specializations(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    return db.query(models.Specialization).all()


@router.post("/specializations", response_model=schemas.SpecializationOut)
def admin_add_specialization(payload: schemas.SpecializationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    existing = db.query(models.Specialization).filter(models.Specialization.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Specialization already exists")
    spec = models.Specialization(name=payload.name)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@router.delete("/specializations/{specialization_id}")
def admin_delete_specialization(specialization_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    spec = db.query(models.Specialization).filter(models.Specialization.id == specialization_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Specialization not found")
    db.delete(spec)
    db.commit()
    return {"detail": "Specialization deleted"}


# ---------------------------------------------------------------------------
# APPOINTMENTS (admin view)
# ---------------------------------------------------------------------------
@router.get("/appointments", response_model=List[schemas.AppointmentOut])
def admin_list_appointments(
    doctor_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    status: Optional[models.AppointmentStatus] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    from app.routers.appointments import _appointment_to_out

    query = db.query(models.Appointment).options(
        joinedload(models.Appointment.doctor).joinedload(models.Doctor.user),
        joinedload(models.Appointment.doctor).joinedload(models.Doctor.clinic),
        joinedload(models.Appointment.doctor).joinedload(models.Doctor.specialization),
        joinedload(models.Appointment.patient).joinedload(models.Patient.user),
        joinedload(models.Appointment.payment),
    )
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if status:
        query = query.filter(models.Appointment.status == status)
    if date:
        query = query.filter(models.Appointment.appointment_date == date)

    appts = query.order_by(models.Appointment.appointment_date.desc()).all()
    return [_appointment_to_out(a) for a in appts]


# ---------------------------------------------------------------------------
# PAYMENTS (admin view)
# ---------------------------------------------------------------------------
@router.get("/payments", response_model=List[schemas.PaymentOut])
def admin_list_payments(
    status: Optional[models.PaymentStatus] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    query = db.query(models.Payment).options(
        joinedload(models.Payment.appointment),
    )
    if status:
        query = query.filter(models.Payment.payment_status == status)
    if date:
        query = query.filter(func.date(models.Payment.created_at) == date)

    payments = query.order_by(models.Payment.created_at.desc()).all()

    result = []
    for p in payments:
        doctor = db.query(models.Doctor).filter(models.Doctor.id == p.doctor_id).first()
        patient = db.query(models.Patient).filter(models.Patient.id == p.patient_id).first()
        result.append(
            schemas.PaymentOut(
                id=p.id,
                amount=p.amount,
                payment_status=p.payment_status,
                payment_method=p.payment_method,
                transaction_id=p.transaction_id,
                created_at=p.created_at,
                doctor_name=doctor.user.full_name if doctor else None,
                patient_name=patient.user.full_name if patient else None,
                appointment_id=p.appointment_id,
            )
        )
    return result
