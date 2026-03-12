"""
Seed Mock Data — GPF, CPF, and Gosped Employees
=================================================
Run: venv\Scripts\python.exe seed_mock_data.py

Creates employees of each type with realistic Sikkim Govt payslip data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from app.auth import get_password_hash
from sqlalchemy import text
import json


def seed():
    conn = engine.connect()
    
    # =============================================
    # EMPLOYEES — One of each type
    # =============================================
    employees = [
        # GPF Employee (digits/letters format)
        {
            "employee_id": "4521/SKM",
            "password": get_password_hash("pass123"),
            "phone_number": "9800000001",
            "email": "gpf.user@example.com",
            "type": "GPF"
        },
        # CPF Employee (XXXX-XX-XXXXX format)
        {
            "employee_id": "2019-01-00342",
            "password": get_password_hash("pass123"),
            "phone_number": "9800000002",
            "email": "cpf.user@example.com",
            "type": "CPF"
        },
        # Gosped Employee (XXXXXX-XX-XX-XXXX format)
        {
            "employee_id": "202101-03-15-0078",
            "password": get_password_hash("pass123"),
            "phone_number": "9800000003",
            "email": "gosped.user@example.com",
            "type": "GOSPED"
        },
    ]
    
    # =============================================
    # PAYSLIP DATA — Realistic Sikkim Govt format
    # =============================================
    payslips = [
        # --- GPF Employee: 4521/SKM ---
        {
            "employee_id": "4521/SKM",
            "month": "January", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 16200.00,
                    "DA": 8910.00,
                    "HRAWS": 3500.00,
                    "NPA": 0.00,
                    "SBCA": 1296.00,
                    "TA": 500.00
                },
                "deductions": {
                    "CPF State": 2511.00,
                    "GIS State": 30.00,
                    "Professional Tax": 150.00,
                    "Stamp Duty": 5.00
                },
                "summary": {
                    "Gross Salary": 30406.00,
                    "Total Deductions": 2696.00,
                    "Net Salary": 27710.00
                }
            })
        },
        {
            "employee_id": "4521/SKM",
            "month": "February", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 16200.00,
                    "DA": 8910.00,
                    "HRAWS": 3500.00,
                    "NPA": 0.00,
                    "SBCA": 1296.00,
                    "TA": 500.00
                },
                "deductions": {
                    "CPF State": 2511.00,
                    "GIS State": 30.00,
                    "Professional Tax": 150.00,
                    "Stamp Duty": 5.00
                },
                "summary": {
                    "Gross Salary": 30406.00,
                    "Total Deductions": 2696.00,
                    "Net Salary": 27710.00
                }
            })
        },
        {
            "employee_id": "4521/SKM",
            "month": "March", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 16700.00,
                    "DA": 9185.00,
                    "HRAWS": 3600.00,
                    "NPA": 0.00,
                    "SBCA": 1336.00,
                    "TA": 500.00
                },
                "deductions": {
                    "CPF State": 2588.50,
                    "GIS State": 30.00,
                    "Professional Tax": 150.00,
                    "Stamp Duty": 5.00
                },
                "summary": {
                    "Gross Salary": 31321.00,
                    "Total Deductions": 2773.50,
                    "Net Salary": 28547.50
                }
            })
        },
        
        # --- CPF Employee: 2019-01-00342 ---
        {
            "employee_id": "2019-01-00342",
            "month": "January", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 25600.00,
                    "DA": 14080.00,
                    "HRAWS": 5120.00,
                    "NPA": 2560.00,
                    "SBCA": 2048.00,
                    "TA": 800.00
                },
                "deductions": {
                    "CPF State": 3968.00,
                    "GIS State": 60.00,
                    "Professional Tax": 200.00,
                    "Stamp Duty": 10.00
                },
                "summary": {
                    "Gross Salary": 50208.00,
                    "Total Deductions": 4238.00,
                    "Net Salary": 45970.00
                }
            })
        },
        {
            "employee_id": "2019-01-00342",
            "month": "February", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 25600.00,
                    "DA": 14080.00,
                    "HRAWS": 5120.00,
                    "NPA": 2560.00,
                    "SBCA": 2048.00,
                    "TA": 800.00
                },
                "deductions": {
                    "CPF State": 3968.00,
                    "GIS State": 60.00,
                    "Professional Tax": 200.00,
                    "Stamp Duty": 10.00
                },
                "summary": {
                    "Gross Salary": 50208.00,
                    "Total Deductions": 4238.00,
                    "Net Salary": 45970.00
                }
            })
        },
        
        # --- Gosped Employee: 202101-03-15-0078 ---
        {
            "employee_id": "202101-03-15-0078",
            "month": "January", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 35400.00,
                    "DA": 19470.00,
                    "HRAWS": 7080.00,
                    "NPA": 3540.00,
                    "SBCA": 2832.00,
                    "TA": 1200.00
                },
                "deductions": {
                    "CPF State": 5487.00,
                    "GIS State": 100.00,
                    "Professional Tax": 200.00,
                    "Stamp Duty": 20.00
                },
                "summary": {
                    "Gross Salary": 69522.00,
                    "Total Deductions": 5807.00,
                    "Net Salary": 63715.00
                }
            })
        },
        {
            "employee_id": "202101-03-15-0078",
            "month": "February", "year": 2026,
            "data_json": json.dumps({
                "earnings": {
                    "Basic Pay": 35400.00,
                    "DA": 19470.00,
                    "HRAWS": 7080.00,
                    "NPA": 3540.00,
                    "SBCA": 2832.00,
                    "TA": 1200.00
                },
                "deductions": {
                    "CPF State": 5487.00,
                    "GIS State": 100.00,
                    "Professional Tax": 200.00,
                    "Stamp Duty": 20.00
                },
                "summary": {
                    "Gross Salary": 69522.00,
                    "Total Deductions": 5807.00,
                    "Net Salary": 63715.00
                }
            })
        },
    ]

    # =============================================
    # INSERT DATA
    # =============================================
    
    print("\n=== Seeding Mock Employees ===\n")
    
    for emp in employees:
        try:
            conn.execute(text("""
                INSERT INTO users (employee_id, password, phone_number, email)
                VALUES (:eid, :pwd, :phone, :email)
            """), {
                "eid": emp["employee_id"],
                "pwd": emp["password"],
                "phone": emp["phone_number"],
                "email": emp["email"]
            })
            print(f"  ✓ {emp['type']:7} | {emp['employee_id']:25} | pass123")
        except Exception as e:
            if "Duplicate" in str(e):
                print(f"  ⊘ {emp['type']:7} | {emp['employee_id']:25} | Already exists")
            else:
                print(f"  ✗ {emp['type']:7} | {emp['employee_id']:25} | Error: {e}")
    
    print("\n=== Seeding Mock Payslips ===\n")
    
    for ps in payslips:
        try:
            conn.execute(text("""
                INSERT INTO payslips (employee_id, month, year, data_json)
                VALUES (:eid, :month, :year, :data)
            """), {
                "eid": ps["employee_id"],
                "month": ps["month"],
                "year": ps["year"],
                "data": ps["data_json"]
            })
            summary = json.loads(ps["data_json"])["summary"]
            print(f"  ✓ {ps['employee_id']:25} | {ps['month']:10} {ps['year']} | Net: ₹{summary['Net Salary']:,.2f}")
        except Exception as e:
            if "Duplicate" in str(e):
                print(f"  ⊘ {ps['employee_id']:25} | {ps['month']:10} {ps['year']} | Already exists")
            else:
                print(f"  ✗ {ps['employee_id']:25} | {ps['month']:10} {ps['year']} | Error: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n=== Done! ===")
    print("\nTest Login Credentials:")
    print("  GPF:    4521/SKM            | Password: pass123")
    print("  CPF:    2019-01-00342       | Password: pass123")
    print("  Gosped: 202101-03-15-0078   | Password: pass123")
    print()


if __name__ == "__main__":
    seed()
