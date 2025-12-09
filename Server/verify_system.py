# A test script to simulate the end-to-end flow of starting an attendance session,
# broadcasting a beacon code, and submitting attendance as a student.

import requests
import time
import json
import paho.mqtt.publish as publish

BASE_URL = "http://localhost:8000/api/v1"
MQTT_HOST = "localhost"

def test_flow():
    # ---------------------------------------------------------
    # 1. Login as Professor
    # ---------------------------------------------------------
    print("\n[1] Logging in as Professor...")
    resp = requests.post(f"{BASE_URL}/login/access-token", data={"username": "prof@aura.com", "password": "pass"})
    if resp.status_code != 200:
        print(f"Prof Login Failed: {resp.text}")
        return
    prof_token = resp.json()["access_token"]
    prof_headers = {"Authorization": f"Bearer {prof_token}"}
    print("Professor Logged in.")

    # ---------------------------------------------------------
    # 2. Get Courses
    # ---------------------------------------------------------
    print("\n[2] Getting Courses...")
    resp = requests.get(f"{BASE_URL}/professor/my-courses", headers=prof_headers)
    courses = resp.json()
    if not courses:
        print("No courses found.")
        return
    course_id = courses[0]["id"]
    print(f"Found Course: {courses[0]['name']} (ID: {course_id})")

    # ---------------------------------------------------------
    # 3. Start Attendance
    # ---------------------------------------------------------
    print("\n[3] Starting Attendance...")
    # Using Class Group ID 1 (CSC2 from seed)
    start_payload = {
        "course_id": course_id,
        "class_group_id": 1,
        "duration_minutes": 5
    }
    resp = requests.post(f"{BASE_URL}/professor/attendance/start", json=start_payload, headers=prof_headers)
    if resp.status_code != 200:
        print(f"Start Failed: {resp.text}")
        return
    print(f"Session Started. Check Server logs for MQTT broadcast.")

    # ---------------------------------------------------------
    # 4. Simulate Beacon (The Hardware)
    # ---------------------------------------------------------
    print("\n[4] Simulating Beacon Broadcasting Code 'XYZ123'...")
    # The real beacon would receive the command and then publish this:
    publish.single("aura/classrooms/CSC2/active_code", payload="XYZ123", hostname=MQTT_HOST)
    
    print("   ... Waiting 2 seconds for Server MQTT Listener to update DB ...")
    time.sleep(2) 

    # ---------------------------------------------------------
    # 5. Student Login
    # ---------------------------------------------------------
    print("\n[5] Logging in as Student...")
    # Login with the credentials from seed_test_data.py
    resp = requests.post(f"{BASE_URL}/login/access-token", data={"username": "john@student.com", "password": "student123"})
    if resp.status_code != 200:
        print(f"Student Login Failed: {resp.text}")
        return
    student_token = resp.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("Student Logged in.")

    # ---------------------------------------------------------
    # 6. Student Submits Attendance
    # ---------------------------------------------------------
    print("\n[6] Submitting Attendance...")
    submit_payload = {
        "code": "XYZ123",
        "device_uuid": "device-uuid-123",
        "rssi": -50.5
    }
    
    resp = requests.post(
        f"{BASE_URL}/student/attendance/submit", 
        json=submit_payload,
        headers=student_headers
    )
    
    print(f"Submission Response: {resp.json()}")
    
    if resp.status_code == 200:
        print("SUCCESS: Attendance Marked!")
    else:
        print(f"FAILURE: {resp.status_code}")

if __name__ == "__main__":
    test_flow()