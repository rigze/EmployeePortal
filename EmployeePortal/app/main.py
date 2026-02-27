from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from datetime import datetime

# Import from our modules
from . import models, schemas, captcha, otp_service, data_service
from .database import engine, get_db

# Create Tables
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

# --- CAPTCHA ENDPOINT ---

@app.get("/api/captcha")
async def get_captcha():
    """Generate a new CAPTCHA image"""
    return captcha.create_captcha()


# --- AUTH ENDPOINTS ---

@app.post("/api/auth/login")
async def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # 1. CAPTCHA CHECK
    if data.captcha_id and data.captcha_text:
        if not captcha.verify_captcha(data.captcha_id, data.captcha_text):
            return {"success": False, "message": "Invalid CAPTCHA"}
    elif data.captcha_id or data.captcha_text:
        return {"success": False, "message": "CAPTCHA verification required"}

    # 2. FIND USER (via adapter)
    user = data_service.get_user(db, data.employee_id)
    
    # 3. VERIFY CREDENTIALS
    if data.password:
        if not user:
            return {"success": False, "message": "Invalid Employee ID or Password"}
        if not data_service.verify_password(db, data.employee_id, data.password):
            return {"success": False, "message": "Invalid Employee ID or Password"}
    elif not user:
        return {"success": False, "message": "User not found"}

    # 4. GENERATE & SEND OTP (via adapter)
    otp = otp_service.generate_otp()
    data_service.save_otp(db, data.employee_id, otp)
    
    # Send OTP via email
    email_result = await otp_service.send_otp_email(user.get("email", ""), otp, data.employee_id)
    
    response = {
        "success": True,
        "message": "OTP Sent",
        "requires_otp": True,
    }
    
    if email_result.get("fallback"):
        response["dev_hint_otp"] = otp
    
    return response


@app.post("/api/auth/verify-otp")
async def verify_otp(data: schemas.OTPVerify, db: Session = Depends(get_db)):
    # All OTP logic is now in data_service (via adapter)
    result = data_service.verify_and_clear_otp(db, data.employee_id, data.otp_code)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "message": "Login Successful",
        "token": f"session_{result['employee_id']}",
        "employee_id": result["employee_id"]
    }


# --- EMPLOYEE DATA ENDPOINTS ---

@app.get("/api/employee/{employee_id}", response_model=schemas.UserProfile)
async def get_employee_profile(employee_id: str, db: Session = Depends(get_db)):
    # Get profile (via adapter)
    profile = data_service.get_employee_profile(db, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")
    return schemas.UserProfile(**profile)


# --- PAYSLIP DATA ENDPOINTS ---

@app.get("/api/payslips")
async def get_payslip(
    employee_id: str,
    month: str,
    year: int,
    db: Session = Depends(get_db)
):
    # Get payslip (via adapter)
    data = data_service.get_payslip(db, employee_id, month, year)
    if not data:
        return {"success": False, "message": "No payslip found for this period"}
    return {"success": True, "data": data}


# --- PDF DOWNLOAD ENDPOINT ---

@app.get("/api/payslips/download")
async def download_payslip(
    employee_id: str,
    month: str,
    year: int,
    format: str = "pdf",
    db: Session = Depends(get_db)
):
    from fpdf import FPDF
    from fastapi.responses import StreamingResponse
    import io
    
    # Get data (via adapter)
    user = data_service.get_user(db, employee_id)
    if not user:
        return {"success": False, "message": "Employee not found"}
    
    raw_data = data_service.get_payslip_raw(db, employee_id, month, year)
    if not raw_data:
        return {"success": False, "message": f"No payslip found for {month} {year}"}
    
    # --- Build the PDF ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "GOVERNMENT OF SIKKIM", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"PAY SLIP FOR THE MONTH OF {month} {year}", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 8)
    ref_no = f"PS/{year}-{employee_id}/{month[:3]}/{year}"
    pdf.cell(0, 6, ref_no, ln=True, align="L")
    pdf.ln(5)
    
    # Employee Details
    pdf.set_font("Helvetica", "", 10)
    y_start = pdf.get_y()
    pdf.cell(95, 6, f"Name:  {user.get('employee_id', '')}", ln=True)
    pdf.cell(95, 6, f"Section:  General Administration", ln=True)
    pdf.cell(95, 6, f"Date Of Birth:  --", ln=True)
    
    pdf.set_xy(110, y_start)
    pdf.cell(90, 6, f"Designation:  Officer", ln=True)
    pdf.set_x(110)
    pdf.cell(90, 6, f"CPF No.  {employee_id}", ln=True)
    pdf.ln(8)
    
    # Earnings & Deductions table
    earnings = raw_data.get("earnings", {})
    deductions = raw_data.get("deductions", {})
    summary = raw_data.get("summary", {})
    
    col_w = 47.5
    row_h = 8
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w, row_h, "EARNINGS", border=1, align="C")
    pdf.cell(col_w, row_h, "Amount (Rs.)", border=1, align="C")
    pdf.cell(col_w, row_h, "DEDUCTIONS", border=1, align="C")
    pdf.cell(col_w, row_h, "Amount (Rs.)", border=1, align="C")
    pdf.ln()
    
    earning_items = [
        ("Basic Pay", earnings.get("Basic Pay", 0)),
        ("DA", earnings.get("DA", 0)),
        ("HRAWS", earnings.get("HRAWS", 0)),
        ("NPA", earnings.get("NPA", 0)),
        ("SBCA", earnings.get("SBCA", 0)),
        ("TA", earnings.get("TA", 0)),
    ]
    
    deduction_items = [
        ("CPF State", deductions.get("CPF State", 0)),
        ("GIS State", deductions.get("GIS State", 0)),
        ("Professional Tax", deductions.get("Professional Tax", 0)),
        ("Stamp Duty", deductions.get("Stamp Duty", 0)),
        ("", ""),
        ("", ""),
    ]
    
    pdf.set_font("Helvetica", "", 10)
    for i in range(len(earning_items)):
        e_name, e_val = earning_items[i]
        d_name, d_val = deduction_items[i]
        
        pdf.cell(col_w, row_h, f"  {e_name}", border=1)
        pdf.cell(col_w, row_h, f"  {e_val:,.2f}" if e_val else "", border=1, align="R")
        pdf.cell(col_w, row_h, f"  {d_name}", border=1)
        pdf.cell(col_w, row_h, f"  {d_val:,.2f}" if d_val else "", border=1, align="R")
        pdf.ln()
    
    pdf.ln(5)
    
    # Summary
    pdf.set_font("Helvetica", "B", 11)
    gross = summary.get("Gross Salary", 0)
    total_ded = summary.get("Total Deductions", 0)
    net = summary.get("Net Salary", 0)
    
    summary_x = 60
    pdf.set_x(summary_x)
    pdf.cell(65, row_h, "Gross Pay", border=1, align="C")
    pdf.cell(65, row_h, f"Rs. {gross:,.2f}", border=1, align="R")
    pdf.ln()
    pdf.set_x(summary_x)
    pdf.cell(65, row_h, "Total Deduction", border=1, align="C")
    pdf.cell(65, row_h, f"Rs. {total_ded:,.2f}", border=1, align="R")
    pdf.ln()
    pdf.set_x(summary_x)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(65, row_h, "Net Pay", border=1, align="C")
    pdf.cell(65, row_h, f"Rs. {net:,.2f}", border=1, align="R")
    pdf.ln()
    
    # Footer
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "Seal and Signature of D&DO", align="R")
    
    pdf_bytes = pdf.output()
    pdf_buffer = io.BytesIO(pdf_bytes)
    filename = f"payslip_{employee_id}_{month}_{year}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
