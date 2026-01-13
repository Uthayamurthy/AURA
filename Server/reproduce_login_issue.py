
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app import models
from app.core.security import verify_password, get_password_hash

def reproduce():
    client = TestClient(app)
    
    email = "alicesmith@ABC.com"
    password = "pass"
    
    print(f"--- Attempting Login for {email} ---")
    
    # 1. Check DB directly
    db = SessionLocal()
    student = db.query(models.Student).filter(models.Student.email == email).first()
    if not student:
        print("ERROR: Student not found in DB!")
    else:
        print(f"Student found: ID={student.id}")
        print(f"Stored Hash: {student.password_hash}")
        
        is_valid = verify_password(password, student.password_hash)
        print(f"Direct Password Verification: {is_valid}")
        
        if not is_valid:
             # Check if hash generation gives same result (it shouldn't due to salt, but helpful to know context)
             print(f"New Hash of 'pass': {get_password_hash('pass')}")

    # 2. Check API
    payload = {
        "username": email,
        "password": password
    }
    # 3. Test Case Sensitivity
    print("\n--- Test 3: Lowercase Email ---")  
    payload_lower = {
        "username": email.lower(),
        "password": password
    }
    response_lower = client.post("/api/v1/login/access-token", data=payload_lower)
    print(f"Lowercase Email Response: {response_lower.status_code}")

    # 4. Test JSON Payload (Simulate App Error)
    print("\n--- Test 4: JSON Payload ---")
    response_json = client.post("/api/v1/login/access-token", json=payload)
    print(f"JSON Payload Response: {response_json.status_code}")
    print(f"JSON Payload Body: {response_json.text}")

if __name__ == "__main__":
    reproduce()
