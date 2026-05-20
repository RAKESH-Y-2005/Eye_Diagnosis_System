import requests
import os
from app import app, db

def run_tests():
    print("Starting automated test flow...")
    
    # 0. Rebuild Database structure
    print("Rebuilding Database Schema...")
    with app.app_context():
        db.create_all()
    print("Database recreated with new schema.")
    
    # 1. Register Usersgistration & Login
    s_patient = requests.Session()
    r = s_patient.post('http://localhost:5000/register', data={
        'full_name': 'Test Patient',
        'email': 'patient@test.com',
        'password': 'password',
        'role': 'patient'
    })
    print("Patient Register/Login status:", r.status_code)
    
    # 2. Doctor Registration
    s_doc = requests.Session()
    r = s_doc.post('http://localhost:5000/register', data={
        'full_name': 'Test Doctor',
        'email': 'doctor@test.com',
        'password': 'password',
        'role': 'doctor'
    })
    print("Doctor Register/Login status:", r.status_code)
    
    # Get doctor ID (hacky: we know it's probably ID=2)
    doctor_id = 2

    # 3. Admin Registration
    s_admin = requests.Session()
    r = s_admin.post('http://localhost:5000/register', data={
        'full_name': 'Admin',
        'email': 'admin@test.com',
        'password': 'password',
        'role': 'admin'
    })
    print("Admin Register/Login status:", r.status_code)

    # 4. Patient Uploads Image for AI Scan
    with open('dummy.jpg', 'wb') as f:
        f.write(os.urandom(1024))
    
    with open('dummy.jpg', 'rb') as f:
        r = s_patient.post('http://localhost:5000/api/predict', files={'file': f})
        print("AI Scan API response:", r.json())
    
    # 5. Patient Books Appointment
    r = s_patient.post('http://localhost:5000/api/book_appointment', data={
        'doctor_id': doctor_id,
        'appointment_date': '2026-10-15T10:00',
        'notes': 'Checking my retina'
    })
    print("Book Appointment status:", r.status_code)

    # 6. Patient Views Dashboard (Contains reports and appts)
    r = s_patient.get('http://localhost:5000/dashboard')
    print("Patient Dashboard accessible:", r.ok, "Text Contains Scan:", "Diabetic Retinopathy" in r.text or "Normal" in r.text)

    # 7. Doctor Views Dashboard
    r = s_doc.get('http://localhost:5000/doctor_dashboard')
    print("Doctor Dashboard accessible:", r.ok, "Text Contains Appt:", "Checking my retina" in r.text or "APT-1" in r.text)

    # 8. Doctor Updates Appointment Status
    r = s_doc.post('http://localhost:5000/api/update_appointment/1', data={'status': 'confirmed'})
    print("Doctor Update Appt status:", r.status_code)

    # 9. Admin Views Dashboard
    r = s_admin.get('http://localhost:5000/admin_dashboard')
    print("Admin Dashboard accessible:", r.ok, "Text Contains Total Scans:", "Total Scans: 1" in r.text)

    # 10. Patient Downloads PDF Report
    r = s_patient.get('http://localhost:5000/report/1/pdf')
    print("PDF Report Download status:", r.status_code, "Bytes:", len(r.content))

if __name__ == '__main__':
    run_tests()
