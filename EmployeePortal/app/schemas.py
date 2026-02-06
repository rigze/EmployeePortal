from pydantic import BaseModel
from typing import Optional, List, Any


# --- AUTH SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    employee_id: str
    password: Optional[str] = None  # Made optional for OTP-only flow
    captcha_id: Optional[str] = None  # CAPTCHA session ID
    captcha_text: Optional[str] = None  # User's CAPTCHA input



class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Any] = None
    employee_id: Optional[str] = None
    requires_otp: Optional[bool] = False
    otp_sent_to: Optional[str] = None
    employee_data: Optional[Any] = None


class OTPVerify(BaseModel):
    employee_id: str
    otp_code: str  # Frontend sends 'otp_code', backend model has 'otp_code'


class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    employee_data: Optional[Any] = None


# --- USER/EMPLOYEE SCHEMAS ---
class UserProfile(BaseModel):
    id: int
    employee_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[str] = None
    hire_date: Optional[str] = None
    profile_image: Optional[str] = None
    status: Optional[str] = "active"

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    username: str
    role: str | None = None

    class Config:
        from_attributes = True


# --- EMPLOYEE SCHEMAS (Legacy/Existing) ---
class EmployeeCreate(BaseModel):
    name: str
    designation: str
    department: str
    joining_date: str


class EmployeeResponse(EmployeeCreate):
    id: int

    class Config:
        from_attributes = True


# --- SALARY SCHEMAS ---
class SalaryCreate(BaseModel):
    employee_id: int
    month: str
    year: int
    basic_pay: float
    hra: float
    medical_allowance: float
    donation_fund: float


class SalaryResponse(BaseModel):
    id: int
    employee_id: int
    net_salary: float

    # Additional fields expected by frontend PaySlipData
    house_rent_allowance: Optional[float] = None
    travel_allowance: Optional[float] = 0.0
    special_allowance: Optional[float] = 0.0
    provident_fund: Optional[float] = 0.0
    professional_tax: Optional[float] = 0.0
    income_tax: Optional[float] = None
    other_deductions: Optional[float] = 0.0
    gross_salary: Optional[float] = 0.0
    payment_date: Optional[str] = None
    status: Optional[str] = "paid"

    class Config:
        from_attributes = True
