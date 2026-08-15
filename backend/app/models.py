import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Time,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    patient = "patient"


class DoctorApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    booked = "booked"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# PATIENTS
# ---------------------------------------------------------------------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    address = Column(String, nullable=True)

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")


# ---------------------------------------------------------------------------
# SPECIALIZATIONS
# ---------------------------------------------------------------------------
class Specialization(Base):
    __tablename__ = "specializations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False)

    doctors = relationship("Doctor", back_populates="specialization")


# ---------------------------------------------------------------------------
# CLINICS
# ---------------------------------------------------------------------------
class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    doctors = relationship("Doctor", back_populates="clinic")


# ---------------------------------------------------------------------------
# DOCTORS
# ---------------------------------------------------------------------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=True)
    specialization_id = Column(String, ForeignKey("specializations.id"), nullable=True)
    bio = Column(Text, nullable=True)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Float, default=100.0)
    approval_status = Column(Enum(DoctorApprovalStatus), default=DoctorApprovalStatus.approved)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor")
    clinic = relationship("Clinic", back_populates="doctors")
    specialization = relationship("Specialization", back_populates="doctors")
    availability = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")


# ---------------------------------------------------------------------------
# DOCTOR AVAILABILITY (weekly recurring slots)
# ---------------------------------------------------------------------------
class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id = Column(String, primary_key=True, default=gen_uuid)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    slot_time = Column(String, nullable=False)      # e.g. "10:00 AM"
    is_active = Column(Boolean, default=True)

    doctor = relationship("Doctor", back_populates="availability")

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", "slot_time", name="uq_doctor_day_slot"),
    )


# ---------------------------------------------------------------------------
# APPOINTMENTS
# ---------------------------------------------------------------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String, nullable=False)  # e.g. "10:00 AM"
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.pending)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    payment = relationship("Payment", foreign_keys=[payment_id], uselist=False)
    review = relationship("Review", back_populates="appointment", uselist=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "appointment_date", "appointment_time",
                          name="uq_doctor_date_time_slot"),
    )


# ---------------------------------------------------------------------------
# PAYMENTS
# ---------------------------------------------------------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    amount = Column(Float, default=100.0)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    payment_method = Column(String, default="dummy")
    transaction_id = Column(String, unique=True, default=gen_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment", foreign_keys=[appointment_id], uselist=False)


# ---------------------------------------------------------------------------
# REVIEWS
# ---------------------------------------------------------------------------
class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=gen_uuid)
    appointment_id = Column(String, ForeignKey("appointments.id"), unique=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    rating = Column(Integer, default=5)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment", back_populates="review")
