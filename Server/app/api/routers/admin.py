from typing import List, Any
from datetime import datetime, timedelta
import csv
import codecs
from sqlalchemy import func, case
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import security

router = APIRouter()

# --- Dashboard Stats ---
@router.get("/stats", response_model=schemas.admin_stats.DashboardStats)
def read_stats(
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    total_students = db.query(models.Student).count()
    total_profs = db.query(models.Professor).count()
    total_courses = db.query(models.Course).count()
    total_classes = db.query(models.ClassGroup).count()
    active_sessions = db.query(models.AttendanceSession).filter(models.AttendanceSession.is_active == True).count()

    today = datetime.now().date()
    todays_sessions_subquery = db.query(models.AttendanceSession.id).filter(func.date(models.AttendanceSession.start_time) == today).subquery()
    
    present_count = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id.in_(todays_sessions_subquery),
        models.AttendanceRecord.status == "PRESENT"
    ).count()
    
    total_records_today = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id.in_(todays_sessions_subquery)
    ).count()
    
    todays_rate = 0.0
    if total_records_today > 0:
        todays_rate = (present_count / total_records_today) * 100

    seven_days_ago = today - timedelta(days=6)
    daily_stats = db.query(
        func.date(models.AttendanceSession.start_time).label("date"),
        func.count(models.AttendanceRecord.id).label("total"),
        func.sum(case((models.AttendanceRecord.status == "PRESENT", 1), else_=0)).label("present")
    ).join(models.AttendanceSession)\
    .filter(func.date(models.AttendanceSession.start_time) >= seven_days_ago)\
    .group_by(func.date(models.AttendanceSession.start_time))\
    .order_by(func.date(models.AttendanceSession.start_time)).all()
    
    weekly_trend = []
    for day_stat in daily_stats:
        rate = 0.0
        if day_stat.total > 0:
            rate = (day_stat.present / day_stat.total) * 100
        weekly_trend.append({"date": day_stat.date, "attendance_rate": rate})

    return {
        "total_students": total_students,
        "total_professors": total_profs,
        "total_courses": total_courses,
        "total_classes": total_classes,
        "active_sessions": active_sessions,
        "todays_attendance_rate": todays_rate,
        "weekly_trend": weekly_trend
    }

# --- Professors Management ---

@router.get("/professors", response_model=List[schemas.user.Professor])
def read_professors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    return db.query(models.Professor).offset(skip).limit(limit).all()

@router.post("/professors", response_model=schemas.user.Professor)
def create_professor(
    *,
    db: Session = Depends(deps.get_db),
    professor_in: schemas.user.ProfessorCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    prof = db.query(models.Professor).filter(models.Professor.email == professor_in.email).first()
    if prof:
        raise HTTPException(status_code=400, detail="Email already exists.")
    
    prof_id = db.query(models.Professor).filter(models.Professor.id == professor_in.id).first()
    if prof_id:
        raise HTTPException(status_code=400, detail="ID already exists.")
        
    db_prof = models.Professor(
        id=professor_in.id,
        name=professor_in.name,
        email=professor_in.email,
        department=professor_in.department,
        password_hash=security.get_password_hash(professor_in.password),
    )
    db.add(db_prof)
    db.commit()
    db.refresh(db_prof)
    return db_prof

@router.put("/professors/{prof_id}", response_model=schemas.user.Professor)
def update_professor(
    prof_id: int,
    professor_in: schemas.user.ProfessorUpdate,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    prof = db.query(models.Professor).filter(models.Professor.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Professor not found")
        
    if professor_in.email:
        prof.email = professor_in.email
    if professor_in.name:
        prof.name = professor_in.name
    if professor_in.department:
        prof.department = professor_in.department
    if professor_in.password:
        prof.password_hash = security.get_password_hash(professor_in.password)
        
    db.commit()
    db.refresh(prof)
    return prof

@router.delete("/professors/{prof_id}")
def delete_professor(
    prof_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    prof = db.query(models.Professor).filter(models.Professor.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Professor not found")
    db.delete(prof)
    db.commit()
    return {"status": "success"}

@router.post("/professors/bulk_upload")
def upload_professors(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    """
    Expects CSV with columns: id, name, email, department, password
    """
    csvReader = csv.reader(codecs.iterdecode(file.file, 'utf-8'))
    header = next(csvReader) # Skip header
    
    count = 0
    errors = []
    
    for row in csvReader:
        if len(row) < 5:
            continue
        try:
            p_id = int(row[0])
            name = row[1]
            email = row[2]
            dept = row[3]
            pwd = row[4]
            
            # Check exist
            if db.query(models.Professor).filter((models.Professor.id == p_id) | (models.Professor.email == email)).first():
                errors.append(f"Skipped {email}: Already exists")
                continue
                
            db_prof = models.Professor(
                id=p_id,
                name=name,
                email=email,
                department=dept,
                password_hash=security.get_password_hash(pwd)
            )
            db.add(db_prof)
            count += 1
        except Exception as e:
            errors.append(f"Error row {row}: {str(e)}")
            
    db.commit()
    return {"added": count, "errors": errors}


# --- Students Management ---

@router.get("/students", response_model=List[schemas.user.Student])
def read_students(
    skip: int = 0,
    limit: int = 100,
    class_group_id: int = None,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    query = db.query(models.Student)
    if class_group_id:
        query = query.filter(models.Student.class_group_id == class_group_id)
    return query.offset(skip).limit(limit).all()

@router.post("/students", response_model=schemas.user.Student)
def create_student(
    *,
    db: Session = Depends(deps.get_db),
    student_in: schemas.user.StudentCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    student = db.query(models.Student).filter(models.Student.id == student_in.id).first()
    if student:
        raise HTTPException(status_code=400, detail="Student ID already exists.")
        
    db_student = models.Student(
        id=student_in.id,
        digital_id=student_in.digital_id,
        name=student_in.name,
        email=student_in.email,
        department=student_in.department,
        year=student_in.year,
        class_group_id=student_in.class_group_id,
        password_hash=security.get_password_hash("student123") # Default password if manual creation doesn't specify? Or we can take it from schema if added.
    )
    # Note: Using default password for manual creation for now, or you can add password to StudentCreate schema
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.put("/students/{student_id}", response_model=schemas.user.Student)
def update_student(
    student_id: int,
    student_in: schemas.user.StudentUpdate,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if student_in.name: student.name = student_in.name
    if student_in.email: student.email = student_in.email
    if student_in.class_group_id: student.class_group_id = student_in.class_group_id
    if student_in.password:
        student.password_hash = security.get_password_hash(student_in.password)
    # Allow resetting device_id (useful if student changes phone)
    if student_in.device_id == "": # Empty string to clear
        student.device_id = None
        
    db.commit()
    db.refresh(student)
    return student

@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"status": "success"}

@router.post("/students/bulk_upload")
def upload_students(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    """
    Expects CSV: id (13 digit), digital_id (7 digit), name, email, year, department, class_group_name, password
    """
    csvReader = csv.reader(codecs.iterdecode(file.file, 'utf-8'))
    header = next(csvReader) 
    
    count = 0
    errors = []
    
    # Cache class groups to avoid repeated DB lookups
    class_map = {cg.name: cg.id for cg in db.query(models.ClassGroup).all()}
    
    for row in csvReader:
        if len(row) < 8:
            continue
        try:
            s_id = int(row[0])
            d_id = int(row[1])
            name = row[2]
            email = row[3]
            year = int(row[4])
            dept = row[5]
            cg_name = row[6]
            pwd = row[7]
            
            # Resolve Class Group
            cg_id = class_map.get(cg_name)
            if not cg_id:
                errors.append(f"Skipped {name}: Class '{cg_name}' not found")
                continue

            if db.query(models.Student).filter(models.Student.id == s_id).first():
                errors.append(f"Skipped {s_id}: Already exists")
                continue
                
            db_student = models.Student(
                id=s_id,
                digital_id=d_id,
                name=name,
                email=email,
                year=year,
                department=dept,
                class_group_id=cg_id,
                password_hash=security.get_password_hash(pwd),
                device_id=None
            )
            db.add(db_student)
            count += 1
        except Exception as e:
            errors.append(f"Error row {row}: {str(e)}")
            
    db.commit()
    return {"added": count, "errors": errors}

# --- Classes & Courses (Keep existing read/create endpoints) ---
@router.post("/classes", response_model=schemas.academic.ClassGroup)
def create_class_group(
    *,
    db: Session = Depends(deps.get_db),
    class_in: schemas.academic.ClassGroupCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    db_class = models.ClassGroup(**class_in.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.get("/classes", response_model=List[schemas.academic.ClassGroup])
def read_classes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    return db.query(models.ClassGroup).offset(skip).limit(limit).all()

@router.post("/courses", response_model=schemas.academic.Course)
def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: schemas.academic.CourseCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    existing = db.query(models.Course).filter(models.Course.code == course_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course code already exists")
    db_course = models.Course(**course_in.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/courses", response_model=List[schemas.academic.Course])
def read_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    return db.query(models.Course).offset(skip).limit(limit).all()

@router.post("/assignments", response_model=schemas.academic.TeachingAssignment)
def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assign_in: schemas.academic.TeachingAssignmentCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    exists = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.course_id == assign_in.course_id,
        models.TeachingAssignment.class_group_id == assign_in.class_group_id,
        models.TeachingAssignment.professor_id == assign_in.professor_id
    ).first()
    if exists: return exists

    db_assign = models.TeachingAssignment(**assign_in.dict())
    db.add(db_assign)
    db.commit()
    db.refresh(db_assign)
    return db_assign

@router.get("/assignments", response_model=List[schemas.academic.TeachingAssignment])
def read_assignments(
    class_group_id: int = None,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    query = db.query(models.TeachingAssignment)
    if class_group_id:
        query = query.filter(models.TeachingAssignment.class_group_id == class_group_id)
    return query.all()

@router.get("/bell-schedule", response_model=List[schemas.academic.BellSchedule])
def read_bell_schedule(
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    return db.query(models.BellSchedule).order_by(models.BellSchedule.slot_number).all()

@router.put("/bell-schedule", response_model=List[schemas.academic.BellSchedule])
def update_bell_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_in: List[schemas.academic.BellScheduleCreate],
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    ret = []
    for slot_data in schedule_in:
        db_slot = db.query(models.BellSchedule).filter(models.BellSchedule.slot_number == slot_data.slot_number).first()
        if db_slot:
            db_slot.start_time = slot_data.start_time
            db_slot.end_time = slot_data.end_time
        else:
            db_slot = models.BellSchedule(**slot_data.dict())
            db.add(db_slot)
        db.commit()
        db.refresh(db_slot)
        ret.append(db_slot)
    return ret

@router.get("/timetable/{class_group_id}", response_model=List[schemas.academic.TimeTable])
def read_timetable_grid(
    class_group_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    entries = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_group_id == class_group_id
    ).all()
    return entries

@router.post("/timetable/slot", response_model=schemas.academic.TimeTable)
def update_timetable_slot(
    *,
    db: Session = Depends(deps.get_db),
    slot_in: schemas.academic.TimeTableCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    assign = db.query(models.TeachingAssignment).filter(models.TeachingAssignment.id == slot_in.assignment_id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")

    existing_entry = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_group_id == assign.class_group_id,
        models.TimeTable.day_of_week == slot_in.day_of_week,
        models.TimeTable.hour_slot == slot_in.hour_slot
    ).first()

    if existing_entry:
        existing_entry.assignment_id = slot_in.assignment_id
        db.commit()
        db.refresh(existing_entry)
        return existing_entry
    else:
        new_entry = models.TimeTable(**slot_in.dict())
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry

@router.delete("/timetable/slot")
def delete_timetable_slot(
    class_group_id: int,
    day_of_week: int,
    hour_slot: int,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    entry = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_group_id == class_group_id,
        models.TimeTable.day_of_week == day_of_week,
        models.TimeTable.hour_slot == hour_slot
    ).first()
    
    if entry:
        db.delete(entry)
        db.commit()
        
    return {"status": "success"}