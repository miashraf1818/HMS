#!/usr/bin/env python
"""
HMS Backend API Tester
Tests all critical endpoints
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_api():
    session = requests.Session()
    timestamp = int(datetime.now().timestamp())
    doctor_username = f"doctor{timestamp}"
    doctor_password = "doctor123"
    
    print("\n" + "="*60)
    print("🏥 HMS BACKEND API TESTING")
    print("="*60 + "\n")
    
    # Test 1: Doctor Registration
    print_info("Test 1: Doctor Registration")
    try:
        response = session.post(f"{BASE_URL}/api/accounts/doctor/register/", json={
            "username": doctor_username,
            "email": f"doctor{timestamp}@hospital.com",
            "password": doctor_password,
            "password2": doctor_password,
            "first_name": "Test",
            "last_name": "Doctor",
            "phone": "9876543210",
            "specialty": "CARDIOLOGY",
            "license_number": f"DOC-TEST-{datetime.now().timestamp()}",
            "consultation_fee": "500",
            "bio": "Test doctor for API testing"
        })
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Doctor registered: {data['user']['email']}")
            print(f"   Role: {data['user']['role']}")
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 2: Logout
    print_info("Test 2: Logout Doctor")
    try:
        response = session.post(f"{BASE_URL}/api/accounts/logout/")
        if response.status_code == 200:
            print_success("Logged out successfully")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 3: Patient Registration
    print_info("Test 3: Patient Registration")
    try:
        response = session.post(f"{BASE_URL}/api/accounts/patient/register/", json={
            "username": f"patient{timestamp}",
            "email": f"patient{timestamp}@email.com",
            "password": "patient123",
            "password2": "patient123",
            "first_name": "Test",
            "last_name": "Patient",
            "phone": "9123456789",
            "date_of_birth": "1990-01-15",
            "blood_group": "O+",
            "emergency_contact": "9000000000"
        })
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Patient registered: {data['user']['email']}")
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 4: List Doctors
    print_info("Test 4: List Available Doctors")
    doctor_id = None
    try:
        response = session.get(f"{BASE_URL}/api/accounts/doctors/")
        if response.status_code == 200:
            doctors = response.json()
            print_success(f"Found {len(doctors)} doctor(s)")
            if doctors:
                # Use the last doctor (most recently created - should be ours)
                doctor = doctors[-1]
                doctor_id = doctor['id']
                print(f"   Using Doctor: {doctor['name']} - {doctor['specialty']}")
                print(f"   Doctor ID: {doctor_id}")
                print(f"   Consultation Fee: ₹{doctor['consultation_fee']}")
            else:
                print_warning("No doctors available")
                return
        else:
            print_error(f"Failed: {response.status_code}")
            return
    except Exception as e:
        print_error(f"Error: {e}")
        return
    
    print()
    
    # Test 5: Book Appointment
    print_info("Test 5: Book Appointment")
    try:
        appointment_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        # Use a different time to avoid conflicts
        appointment_time = f"{10 + (timestamp % 6)}:00:00"  # Varies between 10:00 and 15:00
        response = session.post(f"{BASE_URL}/api/appointments/book/", json={
            "doctor": doctor_id,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "reason": "Regular checkup and consultation"
        })
        
        if response.status_code == 201:
            data = response.json()
            appointment_id = data['appointment']['id']
            print_success("Appointment booked successfully")
            print(f"   ID: {appointment_id}")
            print(f"   Doctor: {data['appointment']['doctor_name']}")
            print(f"   Date: {data['appointment']['appointment_date']}")
            print(f"   Status: {data['appointment']['status']}")
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print_error(f"Error: {e}")
        return
    
    print()
    
    # Test 6: View Patient Appointments
    print_info("Test 6: View Patient's Appointments")
    try:
        response = session.get(f"{BASE_URL}/api/appointments/patient/")
        if response.status_code == 200:
            appointments = response.json()
            print_success(f"Patient has {len(appointments)} appointment(s)")
            for apt in appointments:
                print(f"   - {apt['doctor_name']} on {apt['appointment_date']} at {apt['appointment_time']}")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 7: Check Available Slots
    print_info("Test 7: Check Doctor Availability")
    try:
        response = session.get(f"{BASE_URL}/api/appointments/availability/{doctor_id}/?date={appointment_date}")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Available slots for {data['doctor']} on {data['date']}")
            print(f"   Total slots: {len(data['available_slots'])}")
            print(f"   Sample slots: {', '.join(data['available_slots'][:5])}")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 8: Login as Doctor
    print_info("Test 8: Switch to Doctor Account")
    try:
        # Logout patient
        session.post(f"{BASE_URL}/api/accounts/logout/")
        
        # Login as doctor
        response = session.post(f"{BASE_URL}/api/accounts/login/", json={
            "username": doctor_username,
            "password": doctor_password
        })
        
        if response.status_code == 200:
            print_success("Logged in as doctor")
        else:
            print_error(f"Failed: {response.status_code}")
            return
    except Exception as e:
        print_error(f"Error: {e}")
        return
    
    print()
    
    # Test 9: View Doctor Appointments
    print_info("Test 9: View Doctor's Appointments")
    try:
        response = session.get(f"{BASE_URL}/api/appointments/doctor/")
        if response.status_code == 200:
            appointments = response.json()
            print_success(f"Doctor has {len(appointments)} appointment(s)")
            for apt in appointments:
                print(f"   - {apt['patient_name']} on {apt['appointment_date']} - Status: {apt['status']}")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 10: Approve Appointment
    print_info("Test 10: Doctor Approves Appointment")
    try:
        response = session.patch(f"{BASE_URL}/api/appointments/{appointment_id}/status/", json={
            "status": "CONFIRMED"
        })
        
        if response.status_code == 200:
            data = response.json()
            print_success("Appointment status updated")
            print(f"   New Status: {data['appointment']['status']}")
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    
    # Test 11: Get Appointment Details
    print_info("Test 11: Get Appointment Details")
    try:
        response = session.get(f"{BASE_URL}/api/appointments/{appointment_id}/")
        if response.status_code == 200:
            apt = response.json()
            print_success("Appointment details retrieved")
            print(f"   Patient: {apt['patient_name']}")
            print(f"   Doctor: {apt['doctor_name']} ({apt['doctor_specialty']})")
            print(f"   Date & Time: {apt['appointment_date']} at {apt['appointment_time']}")
            print(f"   Status: {apt['status']}")
            print(f"   Reason: {apt['reason']}")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    print()
    print("="*60)
    print_success("ALL TESTS COMPLETED!")
    print("="*60)
    print()

if __name__ == "__main__":
    test_api()
