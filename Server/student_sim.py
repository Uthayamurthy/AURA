import requests
import uuid
import json

# --- CONFIG ---
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "john@student.com"  # From your seed data
PASSWORD = "student123"

# Simulate a persistent device ID for this "phone"
# In a real app, you generate this once and save it to storage.
PHONE_DEVICE_ID = "android-device-pixel-7-" + str(uuid.getnode())

def login():
    """Authenticates and gets a JWT token."""
    print(f"🔑 Logging in as {USERNAME}...")
    try:
        response = requests.post(
            f"{BASE_URL}/login/access-token",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Login Successful!")
            return token
        else:
            print(f"❌ Login Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def submit_attendance(token, code):
    """Submits the code to the backend."""
    print(f"\n📡 Submitting Code: {code}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "code": code,
        "device_uuid": PHONE_DEVICE_ID,
        "rssi": -55  # Simulating a strong signal
    }

    try:
        response = requests.post(
            f"{BASE_URL}/student/attendance/submit",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n🎉 SUCCESS! Attendance Marked.")
            print(f"   Status: {data.get('status')}")
            print(f"   Time: {data.get('timestamp')}")
        elif response.status_code == 403:
            print("\n🚫 DENIED: You don't belong to this class.")
        elif response.status_code == 404:
            print("\n❌ FAILED: Invalid or Expired Code.")
        elif response.status_code == 401:
            print("\n🔒 SECURITY ALERT: Device Mismatch (Did you switch phones?)")
        else:
            print(f"\n⚠️ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Error submitting: {e}")

if __name__ == "__main__":
    print("--- 🎓 AURA Student App Simulator ---")
    
    # 1. Login
    token = login()
    
    if token:
        # 2. Simulate Scanning (User Input)
        # In the real app, this comes from Bluetooth
        code_input = input("\n👀 Enter the Broadcast Code (from Prof Dashboard): ").strip()
        
        if code_input:
            # 3. Submit
            submit_attendance(token, code_input)