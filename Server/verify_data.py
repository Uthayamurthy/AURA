
from app.core.database import SessionLocal, init_db
from app import models

def verify():
    db = SessionLocal()
    
    print("--- Verifying Class Groups ---")
    classes = db.query(models.ClassGroup).all()
    for c in classes:
        print(f"Class: {c.name}, ID: {c.id}")
        
    print("\n--- Verifying TimeTable for CSE A ---")
    cg = db.query(models.ClassGroup).filter(models.ClassGroup.name == "CSE A").first()
    if not cg:
        print("CSE A not found!")
        return

    assignments = db.query(models.TeachingAssignment).filter(models.TeachingAssignment.class_group_id == cg.id).all()
    print(f"Found {len(assignments)} assignments for CSE A")
    
    ids = [a.id for a in assignments]
    print(f"Assignment IDs: {ids}")
    
    timetables = db.query(models.TimeTable).filter(models.TimeTable.assignment_id.in_(ids)).all()
    print(f"Found {len(timetables)} timetable entries for CSE A")
    
    for t in timetables:
        print(f"Day: {t.day_of_week}, Slot: {t.hour_slot}, Assignment: {t.assignment_id}")

    print("\n--- Verifying API Query Logic ---")
    api_result = db.query(models.TimeTable).join(models.TeachingAssignment).filter(models.TeachingAssignment.class_group_id == cg.id).all()
    print(f"API Query Result Count: {len(api_result)}")

if __name__ == "__main__":
    verify()
