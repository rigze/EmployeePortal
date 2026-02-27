"""
Data Service — Adapter Layer
=============================
All data access goes through this file.

TODAY:  Reads from local MySQL database.
LATER: Just swap the internal functions to call the real Govt API.
       Everything else (main.py, PDF, OTP) stays untouched.

Config: Set DATA_SOURCE in .env to switch between "local_db" and "external_api"
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from . import models, auth

load_dotenv()

# Switch between data sources: "local_db" or "external_api"
DATA_SOURCE = os.getenv("DATA_SOURCE", "local_db")


# =============================================================
#  USER / AUTH FUNCTIONS
# =============================================================

def get_user(db: Session, employee_id: str) -> Optional[Dict]:
    """Find a user by employee_id. Returns a dict or None."""
    if DATA_SOURCE == "external_api":
        return _api_get_user(employee_id)
    return _db_get_user(db, employee_id)


def verify_password(db: Session, employee_id: str, password: str) -> bool:
    """Verify employee credentials. Returns True/False."""
    if DATA_SOURCE == "external_api":
        return _api_verify_password(employee_id, password)
    return _db_verify_password(db, employee_id, password)


def save_otp(db: Session, employee_id: str, otp_code: str) -> bool:
    """Store OTP code for a user. Returns True on success."""
    if DATA_SOURCE == "external_api":
        return _api_save_otp(employee_id, otp_code)
    return _db_save_otp(db, employee_id, otp_code)


def get_user_by_otp(db: Session, otp_code: str) -> Optional[Dict]:
    """Find user by OTP code (fallback when frontend doesn't send employee_id)."""
    if DATA_SOURCE == "external_api":
        return _api_get_user_by_otp(otp_code)
    return _db_get_user_by_otp(db, otp_code)


def verify_and_clear_otp(db: Session, employee_id: str, otp_code: str) -> Dict:
    """
    Verify OTP and clear it if valid.
    Returns: {"success": bool, "message": str, "employee_id": str (if success)}
    """
    if DATA_SOURCE == "external_api":
        return _api_verify_otp(employee_id, otp_code)
    return _db_verify_and_clear_otp(db, employee_id, otp_code)


# =============================================================
#  EMPLOYEE PROFILE FUNCTIONS
# =============================================================

def get_employee_profile(db: Session, employee_id: str) -> Optional[Dict]:
    """Get full employee profile. Returns dict or None."""
    if DATA_SOURCE == "external_api":
        return _api_get_employee_profile(employee_id)
    return _db_get_employee_profile(db, employee_id)


# =============================================================
#  PAYSLIP FUNCTIONS
# =============================================================

def get_payslip(db: Session, employee_id: str, month: str, year: int) -> Optional[Dict]:
    """Get formatted payslip data for frontend. Returns dict or None."""
    if DATA_SOURCE == "external_api":
        return _api_get_payslip(employee_id, month, year)
    return _db_get_payslip(db, employee_id, month, year)


def get_payslip_raw(db: Session, employee_id: str, month: str, year: int) -> Optional[Dict]:
    """Get raw payslip data for PDF generation. Returns dict or None."""
    if DATA_SOURCE == "external_api":
        return _api_get_payslip_raw(employee_id, month, year)
    return _db_get_payslip_raw(db, employee_id, month, year)


# =============================================================
#  LOCAL DB IMPLEMENTATIONS (current - works today)
# =============================================================

def _user_to_dict(user) -> Dict:
    """Convert SQLAlchemy UserModel to a plain dict."""
    return {
        "employee_id": user.employee_id,
        "password_hash": user.password,
        "phone_number": user.phone_number,
        "email": user.email,
        "otp_code": user.otp_code,
        "otp_generated_at": user.otp_generated_at,
    }


def _db_get_user(db: Session, employee_id: str) -> Optional[Dict]:
    user = db.query(models.UserModel).filter(
        models.UserModel.employee_id == employee_id
    ).first()
    return _user_to_dict(user) if user else None


def _db_verify_password(db: Session, employee_id: str, password: str) -> bool:
    user = db.query(models.UserModel).filter(
        models.UserModel.employee_id == employee_id
    ).first()
    if not user:
        return False
    try:
        return auth.verify_password(password, user.password)
    except Exception as e:
        import logging
        logging.getLogger("data_service").error(f"Password verification error: {e}")
        return False


def _db_save_otp(db: Session, employee_id: str, otp_code: str) -> bool:
    user = db.query(models.UserModel).filter(
        models.UserModel.employee_id == employee_id
    ).first()
    if not user:
        return False
    user.otp_code = otp_code
    user.otp_generated_at = datetime.now()
    db.commit()
    return True


def _db_get_user_by_otp(db: Session, otp_code: str) -> Optional[Dict]:
    user = db.query(models.UserModel).filter(
        models.UserModel.otp_code == otp_code
    ).first()
    return _user_to_dict(user) if user else None


def _db_verify_and_clear_otp(db: Session, employee_id: str, otp_code: str) -> Dict:
    from datetime import timedelta
    
    # Find user
    user = None
    if employee_id:
        user = db.query(models.UserModel).filter(
            models.UserModel.employee_id == employee_id
        ).first()
    
    # Fallback: find by OTP code
    if not user and otp_code:
        user = db.query(models.UserModel).filter(
            models.UserModel.otp_code == otp_code
        ).first()
    
    if not user or user.otp_code != otp_code:
        return {"success": False, "message": "Invalid OTP"}
    
    # Check expiry (1 minute)
    if user.otp_generated_at:
        otp_age = datetime.now() - user.otp_generated_at
        if otp_age > timedelta(minutes=1):
            user.otp_code = None
            db.commit()
            return {"success": False, "message": "OTP has expired. Please request a new one."}
    
    # Valid — clear OTP
    user.otp_code = None
    db.commit()
    return {
        "success": True,
        "message": "Login Successful",
        "employee_id": user.employee_id
    }


def _db_get_employee_profile(db: Session, employee_id: str) -> Optional[Dict]:
    user = db.query(models.UserModel).filter(
        models.UserModel.employee_id == employee_id
    ).first()
    if not user:
        return None
    return {
        "id": 0,
        "employee_id": user.employee_id,
        "first_name": "User",
        "last_name": user.employee_id,
        "full_name": f"User {user.employee_id}",
        "department": "General Administration",
        "position": "Officer",
        "email": user.email or f"{user.employee_id}@example.com",
        "status": "active"
    }


def _db_get_payslip(db: Session, employee_id: str, month: str, year: int) -> Optional[Dict]:
    payslip = (
        db.query(models.PayslipModel)
        .filter(
            models.PayslipModel.employee_id == employee_id,
            models.PayslipModel.month == month,
            models.PayslipModel.year == year
        )
        .first()
    )
    if not payslip:
        return None
    
    try:
        raw_data = json.loads(payslip.data_json)
        return {
            "id": payslip.id,
            "employee_id": payslip.employee_id,
            "year": payslip.year,
            "month": payslip.month,
            "pay_period": f"{payslip.month} {payslip.year}",
            # Earnings
            "basic_salary": raw_data.get("earnings", {}).get("Basic Pay", 0),
            "da": raw_data.get("earnings", {}).get("DA", 0),
            "hraws": raw_data.get("earnings", {}).get("HRAWS", 0),
            "npa": raw_data.get("earnings", {}).get("NPA", 0),
            "sbca": raw_data.get("earnings", {}).get("SBCA", 0),
            "ta": raw_data.get("earnings", {}).get("TA", 0),
            # Deductions
            "cpf_state": raw_data.get("deductions", {}).get("CPF State", 0),
            "gis_state": raw_data.get("deductions", {}).get("GIS State", 0),
            "professional_tax": raw_data.get("deductions", {}).get("Professional Tax", 0),
            "stamp_duty": raw_data.get("deductions", {}).get("Stamp Duty", 0),
            # Totals
            "gross_salary": raw_data.get("summary", {}).get("Gross Salary", 0),
            "total_deductions": raw_data.get("summary", {}).get("Total Deductions", 0),
            "net_salary": raw_data.get("summary", {}).get("Net Salary", 0),
            "status": "paid"
        }
    except:
        return None


def _db_get_payslip_raw(db: Session, employee_id: str, month: str, year: int) -> Optional[Dict]:
    """Returns raw earnings/deductions/summary dicts for PDF generation."""
    payslip = (
        db.query(models.PayslipModel)
        .filter(
            models.PayslipModel.employee_id == employee_id,
            models.PayslipModel.month == month,
            models.PayslipModel.year == year
        )
        .first()
    )
    if not payslip:
        return None
    try:
        return json.loads(payslip.data_json)
    except:
        return None


# =============================================================
#  EXTERNAL API IMPLEMENTATIONS (future — add when ready)
# =============================================================
#
#  When your manager provides the real API details, implement
#  these functions. Everything else stays untouched.
#
#  Example:
#    async def _api_get_user(employee_id: str) -> Optional[Dict]:
#        response = httpx.get(f"{GOVT_API_URL}/employees/{employee_id}")
#        if response.status_code == 200:
#            return response.json()
#        return None

def _api_get_user(employee_id: str) -> Optional[Dict]:
    raise NotImplementedError("External API not configured yet. Set DATA_SOURCE=local_db in .env")

def _api_verify_password(employee_id: str, password: str) -> bool:
    raise NotImplementedError("External API not configured yet")

def _api_save_otp(employee_id: str, otp_code: str) -> bool:
    raise NotImplementedError("External API not configured yet")

def _api_get_user_by_otp(otp_code: str) -> Optional[Dict]:
    raise NotImplementedError("External API not configured yet")

def _api_verify_otp(employee_id: str, otp_code: str) -> Dict:
    raise NotImplementedError("External API not configured yet")

def _api_get_employee_profile(employee_id: str) -> Optional[Dict]:
    raise NotImplementedError("External API not configured yet")

def _api_get_payslip(employee_id: str, month: str, year: int) -> Optional[Dict]:
    raise NotImplementedError("External API not configured yet")

def _api_get_payslip_raw(employee_id: str, month: str, year: int) -> Optional[Dict]:
    raise NotImplementedError("External API not configured yet")
