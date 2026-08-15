from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_patient, require_doctor

router = APIRouter(tags=["Appointments"])


def _appointment_to_out(appt: models.Appointment) -> schemas.AppointmentOut:
    doctor_info = None
    if appt.doctor:
        doctor_info = schemas.AppointmentDoctorInfo(
            id=appt.doctor.id,
            full_name=appt.doctor.user.full_name,
            clinic_name=appt.doctor.clinic.name if appt.doctor.clinic else None,
            specialization=appt.doctor.specialization.name if appt.doctor.specialization else None,
            consultation_fee=appt.doctor.consultation_fee,
        )
    patient_info = None
    if appt.patient:
        patient_info = schemas.AppointmentPatientInfo(
            id=appt.patient.id,
            full_name=appt.patient.user.full_name,
            phone=appt.patient.user.phone,
            email=appt.patient.user.email,
        )
    return schemas.AppointmentOut(
        id=appt.id,
        appointment_date=appt.appointment_date,
        appointment_time=appt.appointment_time,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        doctor=doctor_info,
        patient=patient_info,
        payment_status=appt.payment.payment_status if appt.payment else None,
        amount=appt.payment.amount if appt.payment else None,
    )


@router.post("/appointments/book-after-payment", response_model=schemas.AppointmentOut)
def book_after_payment(
    payload: schemas.PaymentCreateRequest,
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    """
    Final step of booking flow. Requires an already-successful payment.
    An appointment is created ONLY if payment_status == success, and only
    if the slot hasn't been taken by someone else in the meantime.
    """
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id, models.Payment.patient_id == patient.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status != models.PaymentStatus.success:
        raise HTTPException(
            status_code=402,
            detail="Payment not successful. Appointment cannot be created until payment succeeds.",
        )

    if payment.appointment_id:
        # Already booked for this payment - return existing appointment (idempotent)
        existing = db.query(models.Appointment).filter(models.Appointment.id == payment.appointment_id).first()
        return _appointment_to_out(existing)

    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Re-check slot is still free right before booking (race condition guard)
    taken = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.appointment_date == payload.appointment_date,
            models.Appointment.appointment_time == payload.appointment_time,
            models.Appointment.status.in_(
                [
                    models.AppointmentStatus.pending,
                    models.AppointmentStatus.booked,
                    models.AppointmentStatus.accepted,
                    models.AppointmentStatus.completed,
                ]
            ),
        )
        .first()
    )
    if taken:
        raise HTTPException(status_code=409, detail="This slot was just booked by someone else. Please choose another slot.")

    appointment = models.Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time,
        status=models.AppointmentStatus.booked,
        payment_id=payment.id,
    )
    db.add(appointment)
    db.flush()

    payment.appointment_id = appointment.id
    db.commit()
    db.refresh(appointment)

    return _appointment_to_out(appointment)


@router.get("/appointments/my", response_model=List[schemas.AppointmentOut])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appts = (
        db.query(models.Appointment)
        .options(
            joinedload(models.Appointment.doctor).joinedload(models.Doctor.user),
            joinedload(models.Appointment.doctor).joinedload(models.Doctor.clinic),
            joinedload(models.Appointment.doctor).joinedload(models.Doctor.specialization),
            joinedload(models.Appointment.payment),
        )
        .filter(models.Appointment.patient_id == patient.id)
        .order_by(models.Appointment.appointment_date.desc())
        .all()
    )
    return [_appointment_to_out(a) for a in appts]


@router.get("/doctor/appointments", response_model=List[schemas.AppointmentOut])
def doctor_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    appts = (
        db.query(models.Appointment)
        .options(
            joinedload(models.Appointment.patient).joinedload(models.Patient.user),
            joinedload(models.Appointment.payment),
        )
        .filter(models.Appointment.doctor_id == doctor.id)
        .order_by(models.Appointment.appointment_date.desc())
        .all()
    )
    return [_appointment_to_out(a) for a in appts]


def _get_doctor_owned_appointment(db: Session, current_user: models.User, appointment_id: str) -> models.Appointment:
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    appt = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id, models.Appointment.doctor_id == doctor.id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.patch("/doctor/appointments/{appointment_id}/accept", response_model=schemas.AppointmentOut)
def accept_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    appt = _get_doctor_owned_appointment(db, current_user, appointment_id)
    appt.status = models.AppointmentStatus.accepted
    db.commit()
    db.refresh(appt)
    return _appointment_to_out(appt)


@router.patch("/doctor/appointments/{appointment_id}/reject", response_model=schemas.AppointmentOut)
def reject_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    appt = _get_doctor_owned_appointment(db, current_user, appointment_id)
    appt.status = models.AppointmentStatus.rejected
    db.commit()
    db.refresh(appt)
    return _appointment_to_out(appt)


@router.patch("/doctor/appointments/{appointment_id}/complete", response_model=schemas.AppointmentOut)
def complete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_doctor),
):
    appt = _get_doctor_owned_appointment(db, current_user, appointment_id)
    appt.status = models.AppointmentStatus.completed
    db.commit()
    db.refresh(appt)
    return _appointment_to_out(appt)
