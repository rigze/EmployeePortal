from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import random
import json
from datetime import datetime

# Import from our new files
from . import models, schemas, auth, database
from .database import engine, get_db

# Create Tables (New Schema)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW AUTH ENDPOINTS ---

@app.post("/api/auth/login")
async def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # 1. CAPTCHA CHECK (Mock)
    if data.captcha and data.captcha.lower() == "invalid":
        return {"success": False, "message": "Invalid Captcha"}

    # 2. FIND USER
    user = db.query(models.UserModel).filter(models.UserModel.employee_id == data.employee_id).first()
    
    # 3. VERIFY CREDENTIALS (Only if password provided)
    if data.password:
        if not user or not auth.verify_password(data.password, user.password):
            return {"success": False, "message": "Invalid Employee ID or Password"}
    elif not user:
         return {"success": False, "message": "User not found"}

    # 4. GENERATE MOCK OTP
    otp = f"{random.randint(100000, 999999)}"
    user.otp_code = otp
    user.otp_generated_at = datetime.now()
    db.commit()
    
    print(f"!!! MOCK OTP FOR {user.employee_id}: {otp} !!!")

    return {
        "success": True,
        "message": "OTP Sent",
        "requires_otp": True,
        # In a real app, don't send OTP in response. For dev, it's helpful.
        "dev_hint_otp": otp 
    }

@app.post("/api/auth/verify-otp")
async def verify_otp(data: schemas.OTPVerify, db: Session = Depends(get_db)):
    user = db.query(models.UserModel).filter(models.UserModel.employee_id == data.employee_id).first()
    
    if not user or user.otp_code != data.otp_code:
        return {"success": False, "message": "Invalid OTP"}
    
    # Optional: Check expiry here using user.otp_generated_at
    
    # Clear OTP
    user.otp_code = None
    db.commit()
    
    # Return a session token (Mocking it with the employee_id for now, or a simple uuid)
    # In real app, create a session record.
    return {
        "success": True, 
        "message": "Login Successful",
        "token": f"session_{user.employee_id}", 
        "employee_id": user.employee_id
    }


# --- EMPLOYEE DATA ENDPOINTS ---

@app.get("/api/employee/{employee_id}", response_model=schemas.UserProfile)
async def get_employee_profile(employee_id: str, db: Session = Depends(get_db)):
    user = db.query(models.UserModel).filter(models.UserModel.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Construct profile (mocking details since UserModel is simple)
    # In a real app, you would join with an EmployeeModel
    return schemas.UserProfile(
        id=0, # Dummy integer ID to satisfy schema
        employee_id=user.employee_id,
        first_name=f"User",
        last_name=user.employee_id,
        full_name=f"User {user.employee_id}",
        department="General Administration",
        position="Officer",
        email=f"{user.employee_id}@example.com",
        status="active"
    )


# --- PAYSLIP DATA ENDPOINTS ---

@app.get("/api/payslips")
async def get_payslip(
    employee_id: str,
    month: str,
    year: int,
    db: Session = Depends(get_db)
):
    # Retrieve payslip
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
        return {"success": False, "message": "No payslip found for this period"}
        
    # Return the stored JSON data directly
    # The frontend expects a certain structure, which we will store in data_json
    try:
        raw_data = json.loads(payslip.data_json)
        # Flatten the data for the frontend
        data = {
            "id": payslip.id,
            "employee_id": payslip.employee_id,
            "year": payslip.year,
            "month": payslip.month,
            "pay_period": f"{payslip.month} {payslip.year}",
            
            # Earnings
            "basic_salary": raw_data.get("earnings", {}).get("Basic Pay", 0),
            "house_rent_allowance": raw_data.get("earnings", {}).get("HRA", 0),
            "travel_allowance": raw_data.get("earnings", {}).get("Travel", 0), # Added default
            "medical_allowance": raw_data.get("earnings", {}).get("Medical", 0), # Added default
            "special_allowance": raw_data.get("earnings", {}).get("Special", 0),
            
            # Deductions
            "provident_fund": raw_data.get("deductions", {}).get("Provident Fund", 0),
            "professional_tax": raw_data.get("deductions", {}).get("Professional Tax", 0),
            "income_tax": raw_data.get("deductions", {}).get("Income Tax", 0),
            "other_deductions": raw_data.get("deductions", {}).get("Other", 0),
            
            # Totals
            "gross_salary": raw_data.get("summary", {}).get("Gross Salary", 0),
            "total_deductions": raw_data.get("summary", {}).get("Total Deductions", 0),
            "net_salary": raw_data.get("summary", {}).get("Net Salary", 0),
            "status": "paid"
        }
    except:
        data = {}

    return {
        "success": True,
        "data": data
    }

@app.get("/api/payslips/download")
async def download_payslip(employee_id: str, month: str, year: int):
    # Placeholder for PDF generation
    return {"message": "PDF Download not implemented yet"}

