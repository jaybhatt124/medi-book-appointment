from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models import UserRole, DoctorApprovalStatus, AppointmentStatus, PaymentStatus


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.patient


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    full_name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole


# ---------------------------------------------------------------------------
# SPECIALIZATION
# ---------------------------------------------------------------------------
class SpecializationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class SpecializationCreate(BaseModel):
    name: str


# ---------------------------------------------------------------------------
# CLINIC
# ---------------------------------------------------------------------------
class ClinicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    city: str
    phone: Optional[str] = None


class ClinicCreate(BaseModel):
    name: str
    address: str
    city: str
    phone: Optional[str] = None


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None


# ---------------------------------------------------------------------------
# DOCTOR AVAILABILITY
# ---------------------------------------------------------------------------
class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    day_of_week: int
    slot_time: str
    is_active: bool


class AvailabilityCreate(BaseModel):
    day_of_week: int
    slot_time: str


# ---------------------------------------------------------------------------
# DOCTOR
# ---------------------------------------------------------------------------
class DoctorOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    experience_years: int
    consultation_fee: float
    approval_status: DoctorApprovalStatus
    is_active: bool
    clinic: Optional[ClinicOut] = None
    specialization: Optional[SpecializationOut] = None


class DoctorListOut(BaseModel):
    id: str
    full_name: str
    bio: Optional[str] = None
    experience_years: int
    consultation_fee: float
    clinic: Optional[ClinicOut] = None
    specialization: Optional[SpecializationOut] = None


class DoctorProfileUpdate(BaseModel):
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    clinic_id: Optional[str] = None
    specialization_id: Optional[str] = None


class AdminDoctorCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    clinic_id: Optional[str] = None
    specialization_id: Optional[str] = None
    bio: Optional[str] = None
    experience_years: int = 0
    consultation_fee: float = 100.0


class AdminDoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_id: Optional[str] = None
    specialization_id: Optional[str] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    is_active: Optional[bool] = None


class SlotAvailabilityOut(BaseModel):
    time: str
    available: bool


# ---------------------------------------------------------------------------
# APPOINTMENT
# ---------------------------------------------------------------------------
class AppointmentDoctorInfo(BaseModel):
    id: str
    full_name: str
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: float


class AppointmentPatientInfo(BaseModel):
    id: str
    full_name: str
    phone: Optional[str] = None
    email: EmailStr


class AppointmentOut(BaseModel):
    id: str
    appointment_date: date
    appointment_time: str
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    doctor: Optional[AppointmentDoctorInfo] = None
    patient: Optional[AppointmentPatientInfo] = None
    payment_status: Optional[PaymentStatus] = None
    amount: Optional[float] = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


# ---------------------------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------------------------
class PaymentCreateRequest(BaseModel):
    doctor_id: str
    appointment_date: date
    appointment_time: str


class PaymentCreateResponse(BaseModel):
    payment_id: str
    amount: float
    payment_status: PaymentStatus
    transaction_id: str


class PaymentOrderResponse(BaseModel):
    payment_id: str
    amount: float
    amount_paise: int
    currency: str
    razorpay_order_id: str
    razorpay_key_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyResponse(BaseModel):
    success: bool
    message: str
    payment_status: PaymentStatus
    appointment_status: str
    appointment: Optional[AppointmentOut] = None


class PaymentSuccessRequest(BaseModel):
    payment_id: str


class PaymentOut(BaseModel):
    id: str
    amount: float
    payment_status: PaymentStatus
    payment_method: str
    transaction_id: str
    created_at: datetime
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    appointment_id: Optional[str] = None


# ---------------------------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------------------------
class AdminDashboardOut(BaseModel):
    total_doctors: int
    total_patients: int
    total_appointments: int
    total_clinics: int
    total_payments_success: int
    total_earnings: float
    pending_doctor_approvals: int


class DoctorDashboardOut(BaseModel):
    total_appointments: int
    today_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    pending_appointments: int
    rejected_appointments: int
    total_earnings: float


class PatientOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool
