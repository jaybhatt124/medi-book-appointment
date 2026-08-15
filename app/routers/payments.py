import base64
import hashlib
import hmac
import json
import uuid
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_patient, require_doctor, require_admin

router = APIRouter(prefix="/payments", tags=["Payments"])


def _slot_taken(db: Session, doctor_id: str, appointment_date, appointment_time: str) -> bool:
    existing = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.appointment_date == appointment_date,
            models.Appointment.appointment_time == appointment_time,
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
    return existing is not None


def _create_razorpay_order(amount_paise: int, currency: str = "INR", notes: dict | None = None) -> dict:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials are not configured")

    auth_header = base64.b64encode(
        f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    ).decode()
    order_data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": str(uuid.uuid4()),
        "payment_capture": 1,
    }
    if notes:
        order_data["notes"] = notes
    payload = json.dumps(order_data).encode()
    request = Request(
        "https://api.razorpay.com/v1/orders",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_header}",
        },
    )
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode()
        detail = body
        try:
            detail = json.loads(body).get("error", {}).get("description", body)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {detail}")
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {exc.reason}")


def _get_razorpay_order(order_id: str) -> dict:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials are not configured")

    auth_header = base64.b64encode(
        f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    ).decode()
    request = Request(
        f"https://api.razorpay.com/v1/orders/{order_id}",
        headers={
            "Authorization": f"Basic {auth_header}",
        },
    )
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(status_code=404, detail="Razorpay order not found")
        body = exc.read().decode()
        detail = body
        try:
            detail = json.loads(body).get("error", {}).get("description", body)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Razorpay order fetch failed: {detail}")
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Razorpay order fetch failed: {exc.reason}")


def _verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials are not configured")

    payload = f"{order_id}|{payment_id}".encode()
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)


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


@router.post("/create-order", response_model=schemas.PaymentOrderResponse)
def create_payment_order(
    payload: schemas.PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if _slot_taken(db, doctor.id, payload.appointment_date, payload.appointment_time):
        raise HTTPException(status_code=409, detail="This slot is already booked. Please choose another slot.")

    consultation_fee = int(doctor.consultation_fee * 100)
    razorpay_order = _create_razorpay_order(
        consultation_fee,
        notes={
            "doctor_id": doctor.id,
            "appointment_date": payload.appointment_date.isoformat(),
            "appointment_time": payload.appointment_time,
        },
    )

    payment = models.Payment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        amount=doctor.consultation_fee,
        payment_status=models.PaymentStatus.pending,
        payment_method="razorpay",
        transaction_id=razorpay_order["id"],
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentOrderResponse(
        payment_id=payment.id,
        amount=payment.amount,
        amount_paise=10000,
        currency="INR",
        razorpay_order_id=razorpay_order["id"],
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify", response_model=schemas.PaymentVerifyResponse)
def verify_payment(
    payload: schemas.PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.transaction_id == payload.razorpay_order_id, models.Payment.patient_id == patient.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if not _verify_razorpay_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")

    if payment.payment_status == models.PaymentStatus.success and payment.appointment_id:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == payment.appointment_id).first()
        return schemas.PaymentVerifyResponse(
            success=True,
            message="Payment successful. Appointment confirmed.",
            payment_status=payment.payment_status,
            appointment_status="CONFIRMED",
            appointment=_appointment_to_out(appointment),
        )

    razorpay_order = _get_razorpay_order(payload.razorpay_order_id)
    notes = razorpay_order.get("notes", {}) or {}
    appointment_date = notes.get("appointment_date")
    appointment_time = notes.get("appointment_time")
    if not appointment_date or not appointment_time:
        raise HTTPException(status_code=400, detail="Razorpay order does not contain appointment details.")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == payment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if _slot_taken(db, doctor.id, appointment_date, appointment_time):
        raise HTTPException(status_code=409, detail="This slot was just booked by someone else. Please choose another slot.")

    payment.payment_status = models.PaymentStatus.success
    db.commit()

    appointment = models.Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status=models.AppointmentStatus.accepted,
        payment_id=payment.id,
    )
    db.add(appointment)
    db.flush()
    payment.appointment_id = appointment.id
    db.commit()
    db.refresh(appointment)

    return schemas.PaymentVerifyResponse(
        success=True,
        message="Payment successful. Appointment confirmed.",
        payment_status=payment.payment_status,
        appointment_status="CONFIRMED",
        appointment=_appointment_to_out(appointment),
    )


@router.post("/create", response_model=schemas.PaymentCreateResponse)
def create_payment(
    payload: schemas.PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    """
    Step 1 of booking: create a 'pending' payment for a chosen doctor/date/slot.
    No appointment row exists yet - it is only created after payment success
    (see /appointments/book-after-payment).
    """
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Block duplicate booking of the exact same doctor/date/time by anyone
    if _slot_taken(db, doctor.id, payload.appointment_date, payload.appointment_time):
        raise HTTPException(status_code=409, detail="This slot is already booked. Please choose another slot.")

    # Block the same patient re-booking the same doctor/date/time (extra guard)
    dup = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.patient_id == patient.id,
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.appointment_date == payload.appointment_date,
            models.Appointment.appointment_time == payload.appointment_time,
            models.Appointment.status != models.AppointmentStatus.cancelled,
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="You already booked this doctor for this date and time.")

    payment = models.Payment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        amount=doctor.consultation_fee,
        payment_status=models.PaymentStatus.pending,
        payment_method="dummy",
        transaction_id=str(uuid.uuid4()),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentCreateResponse(
        payment_id=payment.id,
        amount=payment.amount,
        payment_status=payment.payment_status,
        transaction_id=payment.transaction_id,
    )


@router.post("/success", response_model=schemas.PaymentCreateResponse)
def mark_payment_success(
    payload: schemas.PaymentSuccessRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    """
    Step 2 (dummy payment gateway): mark the payment as successful.
    In a real integration this would be a webhook from Razorpay/Stripe/etc.
    """
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payload.payment_id, models.Payment.patient_id == patient.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status == models.PaymentStatus.success:
        return schemas.PaymentCreateResponse(
            payment_id=payment.id,
            amount=payment.amount,
            payment_status=payment.payment_status,
            transaction_id=payment.transaction_id,
        )

    # Dummy payment always succeeds
    payment.payment_status = models.PaymentStatus.success
    db.commit()
    db.refresh(payment)

    return schemas.PaymentCreateResponse(
        payment_id=payment.id,
        amount=payment.amount,
        payment_status=payment.payment_status,
        transaction_id=payment.transaction_id,
    )


@router.get("/my", response_model=List[schemas.PaymentOut])
def my_payments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_patient),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    payments = db.query(models.Payment).filter(models.Payment.patient_id == patient.id).all()
    return [
        schemas.PaymentOut(
            id=p.id,
            amount=p.amount,
            payment_status=p.payment_status,
            payment_method=p.payment_method,
            transaction_id=p.transaction_id,
            created_at=p.created_at,
            doctor_name=p.appointment.doctor.user.full_name if p.appointment else None,
            appointment_id=p.appointment_id,
        )
        for p in payments
    ]
