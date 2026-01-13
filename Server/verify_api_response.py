
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app import models

def verify_response():
    client = TestClient(app)
    
    # Get Admin Token First?
    # Assuming endpoint has Dependencies but TestClient with override or mock might be needed if auth is strict.
    # But let's try to just get the token or bypass auth?
    # The routers use `deps.get_current_active_admin`. 
    # I can override the dependency.
    
    from app.api import deps
    def mock_get_admin():
        db = SessionLocal()
        return db.query(models.Admin).first() # Return the seeded admin
        
    app.dependency_overrides[deps.get_current_active_admin] = mock_get_admin
    
    # Get Class ID for "CSE A"
    db = SessionLocal()
    cse_a = db.query(models.ClassGroup).filter(models.ClassGroup.name == "CSE A").first()
    if not cse_a:
        print("CSE A not found")
        return

    print(f"Requesting timetable for Class ID: {cse_a.id}")
    response = client.get(f"/api/v1/admin/timetable/{cse_a.id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response Items: {len(data)}")
        if len(data) > 0:
            print("first item sample:", data[0])
            # Check deep nesting
            has_prof = data[0].get("assignment", {}).get("professor")
            print("Has Professor:", has_prof)
            
            has_course = data[0].get("assignment", {}).get("course")
            print("Has Course:", has_course)
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    verify_response()
