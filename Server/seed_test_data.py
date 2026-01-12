from app.core.database import SessionLocal, init_db
from app import models
from app.core.security import get_password_hash
from datetime import time

def seed_data():
    init_db()
    db = SessionLocal()
    
    print("--- Seeding Data ---")

    # 0. Bell Schedule
    if db.query(models.BellSchedule).count() == 0:
        print("Seeding Bell Schedule...")
        # 8 Slots, starting 9:00 AM, 1 hour each
        for i in range(1, 9):
            start_h = 8 + i
            db.add(models.BellSchedule(
                slot_number=i, 
                start_time=time(start_h, 0), 
                end_time=time(start_h, 50)
            ))
        db.commit()

    # 1. Create Admin
    admin = db.query(models.Admin).filter_by(username="admin").first()
    if not admin:
        admin = models.Admin(
            username="admin",
            password_hash=get_password_hash("admin123")
        )
        db.add(admin)
        print("Created Admin: admin")

    # 2. Create ClassGroups
    cg_a = db.query(models.ClassGroup).filter_by(name="CSE A").first()
    if not cg_a:
        cg_a = models.ClassGroup(name="CSE A", department="CSE", year=2)
        db.add(cg_a)
        print("Created ClassGroup: CSE A")
    
    cg_b = db.query(models.ClassGroup).filter_by(name="CSE B").first()
    if not cg_b:
        cg_b = models.ClassGroup(name="CSE B", department="CSE", year=2)
        db.add(cg_b)
        print("Created ClassGroup: CSE B")
    
    db.commit() # Commit to get IDs

    # 3. Create Professors
    prof1 = db.query(models.Professor).filter_by(email="prof@aura.com").first()
    if not prof1:
        prof1 = models.Professor(
            id=100001,
            name="Dr. Smith",
            email="prof@aura.com",
            department="CSE",
            password_hash=get_password_hash("pass")
        )
        db.add(prof1)
        print("Created Professor: Dr. Smith")

    prof2 = db.query(models.Professor).filter_by(email="jones@aura.com").first()
    if not prof2:
        prof2 = models.Professor(
            id=100002,
            name="Dr. Jones",
            email="jones@aura.com",
            department="CSE",
            password_hash=get_password_hash("pass")
        )
        db.add(prof2)
        print("Created Professor: Dr. Jones")
    
    db.commit()

    # 4. Create Courses (Definitions)
    course_algo = db.query(models.Course).filter_by(code="UCS1234").first()
    if not course_algo:
        course_algo = models.Course(code="UCS1234", name="Data Structures", department="CSE")
        db.add(course_algo)
        print("Created Course: Data Structures (UCS1234)")
    
    db.commit()

    # 5. Teaching Assignments (The Logic)
    # Smith teaches Data Structures to CSE A
    assign1 = db.query(models.TeachingAssignment).filter_by(
        course_id=course_algo.id, professor_id=prof1.id, class_group_id=cg_a.id
    ).first()
    
    if not assign1:
        assign1 = models.TeachingAssignment(
            course_id=course_algo.id, professor_id=prof1.id, class_group_id=cg_a.id,
            default_classroom="49",
        )
        db.add(assign1)
        print("Assigned Smith -> DS -> CSE A")

    # Jones teaches Data Structures to CSE B (Same Course, Different Prof)
    assign2 = db.query(models.TeachingAssignment).filter_by(
        course_id=course_algo.id, professor_id=prof2.id, class_group_id=cg_b.id
    ).first()
    
    if not assign2:
        assign2 = models.TeachingAssignment(
            course_id=course_algo.id, professor_id=prof2.id, class_group_id=cg_b.id,
            default_classroom="50",
        )
        db.add(assign2)
        print("Assigned Jones -> DS -> CSE B")

    db.commit()

    # 6. TimeTable
    # Monday (0), Slot 1 for CSE A (Smith)
    tt1 = db.query(models.TimeTable).filter_by(assignment_id=assign1.id, day_of_week=0, hour_slot=1).first()
    if not tt1:
        tt1 = models.TimeTable(assignment_id=assign1.id, day_of_week=0, hour_slot=1)
        db.add(tt1)

    # Monday (0), Slot 1 for CSE B (Jones) - Parallel class!
    tt2 = db.query(models.TimeTable).filter_by(assignment_id=assign2.id, day_of_week=0, hour_slot=1).first()
    if not tt2:
        tt2 = models.TimeTable(assignment_id=assign2.id, day_of_week=0, hour_slot=1)
        db.add(tt2)

    db.commit()

    # 7. Student
    student = db.query(models.Student).filter_by(email="john@student.com").first()
    if not student:
        student = models.Student(
            id=1234567890123,
            digital_id=1234567,
            name="John Doe",
            email="john@student.com",
            password_hash=get_password_hash("student123"), 
            department="CSE",
            year=2,
            class_group_id=cg_a.id, # Belongs to CSE A
            device_id=None # Null initially
        )
        db.add(student)
        print("Created Student: John Doe (CSE A)")

    db.commit()
    db.close()
    print("--- Seeding Complete ---")

if __name__ == "__main__":
    seed_data()