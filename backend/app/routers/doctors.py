from datetime import date as date_type, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_doctor

router = APIRouter(tags=["Doctors"])


def _doctor_to_list_out(doctor: models.Doctor) -> schemas.DoctorListOut:
    return schemas.DoctorListOut(
        id=doctor.id,
        full_name=doctor.user.full_name,
        bio=doctor.bio,
        experience_years=doctor.experience_years,
        consultation_fee=doctor.consultation_fee,
        clinic=schemas.ClinicOut.model_validate(doctor.clinic) if doctor.clinic else None,
        specialization=schemas.SpecializationOut.model_validate(doctor.specialization)
        if doctor.specialization
        else None,
    )


@router.get("/doctors", response_model=List[schemas.DoctorListOut])
def list_doctors(
    city: Optional[str] = None,
    specialization_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    # NOTE: no role restriction here on purpose. Any logged-in user
    # (patient, doctor, or admin) can browse the doctor directory.
    current_user: models.User = Depends(get_current_user),
):
    """
    Public-to-any-logged-in-user endpoint. Returns only doctors that are
    active AND approved by admin, since those are the only ones patients
    should be able to book.
    """
    query = (
        db.query(models.Doctor)
        .options(
            joinedload(models.Doctor.user),
            joinedload(models.Doctor.clinic),
            joinedload(models.Doctor.specialization),
        )
        .join(models.User, models.Doctor.user_id == models.User.id)
        .filter(
            models.Doctor.is_active == True,  # noqa: E712
            models.Doctor.approval_status == models.DoctorApprovalStatus.approved,
        )
    )

    if specialization_id:
        query = query.filter(models.Doctor.specialization_id == specialization_id)
    if clinic_id:
        query = query.filter(models.Doctor.clinic_id == clinic_id)
    if city:
        query = query.join(models.Clinic).filter(models.Clinic.city.ilike(f"%{city}%"))
    if search:
        query = query.filter(models.User.full_name.ilike(f"%{search}%"))

    doctors = query.all()
    return [_doctor_to_list_out(d) for d in doctors]


@router.get("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def get_doctor(
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doctor = (
        db.query(models.Doctor)
        .options(
            joinedload(models.Doctor.user),
            joinedload(models.Doctor.clinic),
            joinedload(models.Doctor.specialization),
        )
        .filter(models.Doctor.id == doctor_id)
        .first()
    )
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

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


@router.get("/doctors/{doctor_id}/slots", response_model=List[schemas.SlotAvailabilityOut])
def get_doctor_slots(
    doctor_id: str,
    date: date_type = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    day_of_week = date.weekday()  # 0=Monday

    available_slots = (
        db.query(models.DoctorAvailability)
        .filter(
            models.DoctorAvailability.doctor_id == doctor_id,
            models.DoctorAvailability.day_of_week == day_of_week,
            models.DoctorAvailability.is_active == True,  # noqa: E712
        )
        .all()
    )

    booked_times = {
        a.appointment_time
        for a in db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.appointment_date == date,
            models.Appointment.status.in_(
                [
                    models.AppointmentStatus.pending,
                    models.AppointmentStatus.booked,
                    models.AppointmentStatus.accepted,
                    models.AppointmentStatus.completed,
                ]
            ),
        )
    }

    return [
        schemas.SlotAvailabilityOut(
            time=slot.slot_time, available=slot.slot_time not in booked_times
        )
        for slot in available_slots
    ]


@router.put("/doctor/profile", response_model=schemas.DoctorOut)
def update_own_profile(
    payload: schemas.DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)

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


@router.get("/doctor/dashboard", response_model=schemas.DoctorDashboardOut)
def doctor_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    appts = db.query(models.Appointment).filter(models.Appointment.doctor_id == doctor.id).all()
    today = datetime.utcnow().date()

    total = len(appts)
    today_count = sum(1 for a in appts if a.appointment_date == today)
    upcoming = sum(
        1
        for a in appts
        if a.appointment_date >= today
        and a.status in (models.AppointmentStatus.booked, models.AppointmentStatus.accepted)
    )
    completed = sum(1 for a in appts if a.status == models.AppointmentStatus.completed)
    pending = sum(
        1
        for a in appts
        if a.status in (models.AppointmentStatus.pending, models.AppointmentStatus.booked)
    )
    rejected = sum(1 for a in appts if a.status == models.AppointmentStatus.rejected)

    earnings = (
        db.query(models.Payment)
        .filter(
            models.Payment.doctor_id == doctor.id,
            models.Payment.payment_status == models.PaymentStatus.success,
        )
        .all()
    )
    total_earnings = sum(p.amount for p in earnings)

    return schemas.DoctorDashboardOut(
        total_appointments=total,
        today_appointments=today_count,
        upcoming_appointments=upcoming,
        completed_appointments=completed,
        pending_appointments=pending,
        rejected_appointments=rejected,
        total_earnings=total_earnings,
    )
