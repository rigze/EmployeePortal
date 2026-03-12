from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .database import Base


class UserModel(Base):
    __tablename__ = "users"
    
    # Employee ID with support for special chars like 'GOV/EMP/001'
    employee_id = Column(String(50), primary_key=True, index=True)
    password = Column(String(255)) # Storing raw/hashed password
    phone_number = Column(String(15), nullable=True)  # Mobile number for OTP SMS
    email = Column(String(100), nullable=True)  # Email for OTP delivery
    
    # OTP fields
    otp_code = Column(String(10), nullable=True)
    otp_generated_at = Column(DateTime, nullable=True)
    
    # Relationship
    payslips = relationship("PayslipModel", back_populates="employee")


class PayslipModel(Base):
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("users.employee_id"))
    
    month = Column(String(20)) # e.g., "January"
    year = Column(Integer)     # e.g., 2024
    
    # Storing all dynamic data (Basic, HRA, Deductions) as JSON string
    # This allows flexibility for different government departments
    data_json = Column(Text) 
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("UserModel", back_populates="payslips")


class PayslipVerificationToken(Base):
    """
    QR Verification Tokens — for payslip authenticity proof.
    When a bank scans the QR code on a printed payslip,
    this token is used to look up and display the real data.
    """
    __tablename__ = "payslip_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)  # UUID token
    employee_id = Column(String(50), ForeignKey("users.employee_id"))
    payslip_id = Column(Integer, ForeignKey("payslips.id"))
    
    # Snapshot of key data at time of generation (tamper-proof)
    employee_name = Column(String(255))
    month = Column(String(20))
    year = Column(Integer)
    net_salary = Column(Float)
    gross_salary = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Token expires after 6 months
