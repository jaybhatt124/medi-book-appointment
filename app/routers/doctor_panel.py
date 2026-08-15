from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import require_doctor

router = APIRouter(prefix="/doctor", tags=["Doctor Panel"])


@router.get("/payments", response_model=List[schemas.PaymentOut])
def doctor_payment_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    payments = db.query(models.Payment).filter(models.Payment.doctor_id == doctor.id).all()

    result = []
    for p in payments:
        patient = db.query(models.Patient).filter(models.Patient.id == p.patient_id).first()
        result.append(
            schemas.PaymentOut(
                id=p.id,
                amount=p.amount,
                payment_status=p.payment_status,
                payment_method=p.payment_method,
                transaction_id=p.transaction_id,
                created_at=p.created_at,
                patient_name=patient.user.full_name if patient else None,
                appointment_id=p.appointment_id,
            )
        )
    return result


@router.get("/availability", response_model=List[schemas.AvailabilityOut])
def get_own_availability(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id == doctor.id).all()


@router.post("/availability", response_model=schemas.AvailabilityOut)
def add_own_availability(
    payload: schemas.AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    existing = (
        db.query(models.DoctorAvailability)
        .filter(
            models.DoctorAvailability.doctor_id == doctor.id,
            models.DoctorAvailability.day_of_week == payload.day_of_week,
            models.DoctorAvailability.slot_time == payload.slot_time,
        )
        .first()
    )
    if existing:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    slot = models.DoctorAvailability(
        doctor_id=doctor.id, day_of_week=payload.day_of_week, slot_time=payload.slot_time
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/availability/{availability_id}")
def remove_own_availability(
    availability_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    slot = (
        db.query(models.DoctorAvailability)
        .filter(models.DoctorAvailability.id == availability_id, models.DoctorAvailability.doctor_id == doctor.id)
        .first()
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Availability slot not found")
    db.delete(slot)
    db.commit()
    return {"detail": "Availability slot removed"}
