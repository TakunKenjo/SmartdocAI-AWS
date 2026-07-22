#!/usr/bin/env python
# Quick test for validation functions

from modules.auth_service import validate_phone_format, validate_dob, validate_fullname

print("=== PHONE VALIDATION ===")
print(f"0901234567: {validate_phone_format('0901234567')} (expect True)")
print(f"+84901234567: {validate_phone_format('+84901234567')} (expect True)")
print(f"090 1234 567: {validate_phone_format('090 1234 567')} (expect False)")
print(f"090-1234-567: {validate_phone_format('090-1234-567')} (expect False)")

print("\n=== DOB VALIDATION ===")
print(f"1900-01-01: {validate_dob('1900-01-01')} (expect True)")
print(f"1990-12-31: {validate_dob('1990-12-31')} (expect True)")
print(f"2020-02-29: {validate_dob('2020-02-29')} (expect True - leap year)")
print(f"2099-12-31: {validate_dob('2099-12-31')} (expect False - out of range)")
print(f"1899-12-31: {validate_dob('1899-12-31')} (expect False - before 1900)")

print("\n=== FULLNAME VALIDATION ===")
print(f"Nguyễn Văn A: {validate_fullname('Nguyễn Văn A')} (expect True)")
print(f"Test@User#123: {validate_fullname('Test@User#123')} (expect True)")

obrien_result = validate_fullname("O'Brien")
print(f"O'Brien: {obrien_result} (expect True)")

script_result = validate_fullname('<script>alert(1)</script>')
print(f"<script>alert: {script_result} (expect False)")

onclick_result = validate_fullname('onclick=alert(1)')
print(f"onclick=alert: {onclick_result} (expect False)")

