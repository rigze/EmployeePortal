"""
Employee Code Classification
==============================
Ported from C# FRED.Pranali.Payroll.Domain.Utilities.EmployeeCodeRegex

Three employee types based on their code format:
  - GPF: digits/letters         (e.g., 1234/ABC, 567/XYZ)
  - CPF: XXXX-XX-XXXXX          (e.g., 1234-56-78901)
  - Gosped: XXXXXX-XX-XX-XXXX   (e.g., 123456-12-34-5678)
"""
import re


def is_gpf_number(code: str) -> bool:
    """GPF Number: digit(s) followed by / and letter(s)"""
    if not code:
        return False
    return bool(re.match(r'\d+/[a-zA-Z]+', code.strip()))


def is_cpf_number(code: str) -> bool:
    """CPF Number: 4 digits - 2 digits - 5 digits"""
    if not code:
        return False
    return bool(re.match(r'\d{4}-\d{2}-\d{5}$', code.strip()))


def is_gosped_code(code: str) -> bool:
    """Gosped Code: 6 digits - 2 digits - 2 digits - 4 digits"""
    if not code:
        return False
    return bool(re.match(r'\d{6}-\d{2}-\d{2}-\d{4}$', code.strip()))


def classify_employee(code: str) -> str:
    """
    Classify an employee code into its type.
    Returns: "GPF", "CPF", "GOSPED", or "UNKNOWN"
    """
    if not code:
        return "UNKNOWN"
    
    code = code.strip()
    
    if is_gpf_number(code):
        return "GPF"
    elif is_cpf_number(code):
        return "CPF"
    elif is_gosped_code(code):
        return "GOSPED"
    else:
        return "UNKNOWN"
