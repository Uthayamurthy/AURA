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
    # 2. Get Assignments (My Courses)
    # ---------------------------------------------------------
    print("\n[2] Getting Teaching Assignments...")
    resp = requests.get(f"{BASE_URL}/professor/my-courses", headers=prof_headers)
    assignments = resp.json()
    if not assignments:
        print("No assignments found.")
        return
    
    # Grab the first assignment details dynamically
    target_assignment = assignments[0]
    course_id = target_assignment["course_id"]
    class_group_id = target_assignment["class_group_id"]
    
    # We need the Class Name for the MQTT Topic (e.g., "CSE A")
    # Assuming the API returns the nested class_group object
    class_group_name = target_assignment["class_group"]["name"] 
    
    print(f"Selected Assignment: {target_assignment['course']['name']} for {class_group_name}")

    # ---------------------------------------------------------
    # 3. Start Attendance
    # ---------------------------------------------------------
    print("\n[3] Starting Attendance...")
    start_payload = {
        "course_id": course_id,
        "class_group_id": class_group_id,
        "duration_minutes": 5
    }
    resp = requests.post(f"{BASE_URL}/professor/attendance/start", json=start_payload, headers=prof_headers)
    if resp.status_code != 200:
        print(f"Start Failed: {resp.text}")
        return
    
    session_data = resp.json()
    print(f"Session Started (ID: {session_data['id']}).")

    # ---------------------------------------------------------
    # 4. Simulate Beacon (The Hardware)
    # ---------------------------------------------------------
    print(f"\n[4] Simulating Beacon Broadcasting in '{class_group_name}'...")
    
    # The Beacon generates a code and tells the server
    beacon_code = "XYZ123"
    
    # TOPIC FORMAT: aura/classrooms/{CLASS_NAME}/active_code
    # This must match what the server listens to in mqtt_listener.py
    topic = f"aura/classrooms/{class_group_name}/active_code"
    
    print(f"   -> Publishing '{beacon_code}' to topic '{topic}'")
    publish.single(topic, payload=beacon_code, hostname=MQTT_HOST)
    
    print("   ... Waiting 2 seconds for Server to update DB ...")
    time.sleep(2) 

    # ---------------------------------------------------------
    # 5. Student Login
    # ---------------------------------------------------------
    print("\n[5] Logging in as Student...")
    # John Doe is in CSE A (from seed data)
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
        "code": beacon_code, # Must match what we sent to MQTT
        "device_uuid": "device-uuid-123", # matches seed data (or nullable)
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
        print(f"FAILURE: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    test_flow()