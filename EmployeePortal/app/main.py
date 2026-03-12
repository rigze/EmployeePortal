from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from datetime import datetime, timedelta

# Import from our modules
from . import models, schemas, captcha, otp_service, data_service, employee_code
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
    # 0. VALIDATE EMPLOYEE ID FORMAT (before anything else)
    emp_type = employee_code.classify_employee(data.employee_id)
    if emp_type == "UNKNOWN":
        return {
            "success": False,
            "message": "Invalid Employee ID format. Please check your Employee ID and try again."
        }

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
        "employee_type": employee_code.classify_employee(data.employee_id),
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
        "employee_id": result["employee_id"],
        "employee_type": employee_code.classify_employee(result["employee_id"])
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


# --- QR CODE PAYSLIP VERIFICATION ---

@app.post("/api/payslips/generate-verification-token")
async def generate_verification_token(
    employee_id: str,
    month: str,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Generate a unique QR verification token for a payslip.
    The frontend encodes this URL into the QR code on the payslip.
    """
    import uuid
    
    # Get payslip data
    payslip_data = data_service.get_payslip(db, employee_id, month, year)
    if not payslip_data:
        return {"success": False, "message": "Payslip not found"}
    
    # Get the raw payslip record for the payslip_id
    payslip = (
        db.query(models.PayslipModel)
        .filter(
            models.PayslipModel.employee_id == employee_id,
            models.PayslipModel.month == month,
            models.PayslipModel.year == year
        )
        .first()
    )
    
    # Check if token already exists for this payslip
    existing = db.query(models.PayslipVerificationToken).filter(
        models.PayslipVerificationToken.payslip_id == payslip.id
    ).first()
    
    if existing:
        return {
            "success": True,
            "token": existing.token,
            "verification_url": f"/api/payslips/verify?token={existing.token}"
        }
    
    # Generate new token
    token = uuid.uuid4().hex
    
    verification = models.PayslipVerificationToken(
        token=token,
        employee_id=employee_id,
        payslip_id=payslip.id,
        employee_name=employee_id,  # Will be real name when connected to govt API
        month=month,
        year=year,
        net_salary=payslip_data.get("net_salary", 0),
        gross_salary=payslip_data.get("gross_salary", 0),
        expires_at=datetime.utcnow() + timedelta(days=180),  # 6 months
    )
    db.add(verification)
    db.commit()
    
    return {
        "success": True,
        "token": token,
        "verification_url": f"/api/payslips/verify?token={token}"
    }


def _invalid_page() -> str:
    """HTML page for invalid/tampered QR codes."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payslip Verification - INVALID</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #fef2f2; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
            .card { background: white; border-radius: 12px; padding: 40px; max-width: 450px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #dc2626; }
            .icon { font-size: 64px; margin-bottom: 16px; }
            h1 { color: #dc2626; font-size: 24px; margin-bottom: 12px; }
            p { color: #666; line-height: 1.6; }
            .warning { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-top: 20px; color: #991b1b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">❌</div>
            <h1>INVALID PAYSLIP</h1>
            <p>This payslip could not be verified. It may have been <strong>tampered with</strong> or the QR code is invalid.</p>
            <div class="warning">
                ⚠️ Do not accept this document as proof of income. Contact the issuing department for a genuine copy.
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/api/payslips/verify")
async def verify_payslip(token: str, db: Session = Depends(get_db)):
    """
    Public verification page — bank officers scan the QR code,
    this page shows whether the payslip is genuine.
    Returns an HTML page (not JSON) so it works directly in a phone browser.
    """
    from fastapi.responses import HTMLResponse
    
    # Look up the token
    verification = db.query(models.PayslipVerificationToken).filter(
        models.PayslipVerificationToken.token == token
    ).first()
    
    if not verification:
        # INVALID / TAMPERED
        return HTMLResponse(content=_invalid_page(), status_code=404)
    
    # Check expiry
    if verification.expires_at and datetime.utcnow() > verification.expires_at:
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payslip Verification - EXPIRED</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #fefce8; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
                .card {{ background: white; border-radius: 12px; padding: 40px; max-width: 450px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #ca8a04; }}
                .icon {{ font-size: 64px; margin-bottom: 16px; }}
                h1 {{ color: #ca8a04; font-size: 24px; margin-bottom: 12px; }}
                p {{ color: #666; line-height: 1.6; }}
                .info {{ background: #fefce8; border: 1px solid #fde68a; border-radius: 8px; padding: 16px; margin-top: 20px; color: #92400e; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">⏳</div>
                <h1>VERIFICATION EXPIRED</h1>
                <p>This payslip verification token has <strong>expired</strong>. The employee needs to generate a new QR code from the portal.</p>
                <div class="info">
                    Expired on: {verification.expires_at.strftime("%d-%m-%Y")}<br>
                    Employee ID: {verification.employee_id}
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=410)
    
    # VALID — show verified data
    created = verification.created_at.strftime("%d-%m-%Y") if verification.created_at else "N/A"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payslip Verification - VERIFIED</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0fdf4; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 40px; max-width: 500px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.1); border-top: 5px solid #16a34a; }}
            .header {{ text-align: center; margin-bottom: 24px; }}
            .icon {{ font-size: 64px; margin-bottom: 12px; }}
            h1 {{ color: #16a34a; font-size: 22px; }}
            h2 {{ color: #333; font-size: 16px; margin-bottom: 20px; text-align: center; }}
            .details {{ border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #f3f4f6; }}
            .row:last-child {{ border-bottom: none; }}
            .row:nth-child(even) {{ background: #fafafa; }}
            .label {{ color: #666; font-size: 14px; }}
            .value {{ color: #111; font-weight: 600; font-size: 14px; }}
            .net-row {{ background: #f0fdf4 !important; }}
            .net-row .value {{ color: #16a34a; font-size: 18px; }}
            .footer {{ text-align: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
            .footer p {{ color: #999; font-size: 12px; line-height: 1.6; }}
            .badge {{ display: inline-block; background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="icon">✅</div>
                <h1>VERIFIED PAYSLIP</h1>
                <span class="badge">Government of Sikkim</span>
            </div>
            
            <h2>This payslip is authentic and has not been tampered with.</h2>
            
            <div class="details">
                <div class="row">
                    <span class="label">Employee ID</span>
                    <span class="value">{verification.employee_id}</span>
                </div>
                <div class="row">
                    <span class="label">Employee Name</span>
                    <span class="value">{verification.employee_name}</span>
                </div>
                <div class="row">
                    <span class="label">Pay Period</span>
                    <span class="value">{verification.month} {verification.year}</span>
                </div>
                <div class="row">
                    <span class="label">Gross Salary</span>
                    <span class="value">₹{verification.gross_salary:,.2f}</span>
                </div>
                <div class="row net-row">
                    <span class="label">Net Salary</span>
                    <span class="value">₹{verification.net_salary:,.2f}</span>
                </div>
            </div>
            
            <div class="footer">
                <p>Verified on: {created}<br>
                Token: {verification.token[:8]}...{verification.token[-4:]}<br>
                Issued by Government of Sikkim Employee Portal</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
