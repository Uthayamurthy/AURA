from app.core.database import SessionLocal, init_db
from app import models
from app.core.security import get_password_hash

def seed_data():
    init_db()
    db = SessionLocal()
    
    # 0. Create Admin (Default Credentials)
    admin = db.query(models.Admin).filter_by(username="admin").first()
    if not admin:
        admin = models.Admin(
            username="admin",
            password_hash=get_password_hash("admin123")
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Created Admin: admin (username: admin / password: admin123)")
    else:
        print("Admin 'admin' exists")

    # 1. Create ClassGroup
    cg = db.query(models.ClassGroup).filter_by(name="CSC2").first()
    if not cg:
        cg = models.ClassGroup(name="CSC2", department="CSE", year=2)
        db.add(cg)
        db.commit()
        db.refresh(cg)
        print("Created ClassGroup: CSC2")
    else:
        print("ClassGroup CSC2 exists")

    # 2. Create Professor
    prof = db.query(models.Professor).filter_by(email="prof@aura.com").first()
    if not prof:
        prof = models.Professor(
            id=100001,
            name="Dr. Smith",
            email="prof@aura.com",
            department="CSE",
            password_hash=get_password_hash("pass")
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)
        print("Created Professor: Dr. Smith (prof@aura.com / pass)")
    else:
         print("Professor Dr. Smith exists")

    # 3. Create Course
    course = db.query(models.Course).filter_by(name="Algorithms").first()
    if not course:
        course = models.Course(name="Algorithms", professor_id=prof.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        print("Created Course: Algorithms")

    # 4. Create TimeTable (Optional for now since we manual start)
    tt = db.query(models.TimeTable).first()
    if not tt:
        tt = models.TimeTable(class_group_id=cg.id, course_id=course.id, day_of_week=0, hour_slot=1)
        db.add(tt)
        db.commit()

    # 5. Create Student
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
            class_group_id=cg.id,
            device_id="device-uuid-123" 
        )
        db.add(student)
        db.commit()
        print("Created Student: John Doe (john@student.com / student123)")
    else:
        print("Student John Doe exists")

    db.close()

if __name__ == "__main__":
    seed_data()
