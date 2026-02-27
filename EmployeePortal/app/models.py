from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
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
