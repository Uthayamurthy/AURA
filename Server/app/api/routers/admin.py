from typing import List, Any
from datetime import datetime, timedelta
from sqlalchemy import func, case, and_
from fastapi import APIRouter, Depends, HTTPException
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
    # 1. Counts
    total_students = db.query(models.Student).count()
    total_profs = db.query(models.Professor).count()
    total_courses = db.query(models.Course).count() # Generic Courses
    total_classes = db.query(models.ClassGroup).count()

    # 2. Active Sessions
    active_sessions = db.query(models.AttendanceSession).filter(models.AttendanceSession.is_active == True).count()

    # 3. Today's Attendance
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

    # 4. Weekly Trend
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

# --- Professors ---
@router.post("/professors", response_model=schemas.user.Professor)
def create_professor(
    *,
    db: Session = Depends(deps.get_db),
    professor_in: schemas.user.ProfessorCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    prof = db.query(models.Professor).filter(models.Professor.email == professor_in.email).first()
    if prof:
        raise HTTPException(status_code=400, detail="Professor with this email already exists.")
    
    prof_id = db.query(models.Professor).filter(models.Professor.id == professor_in.id).first()
    if prof_id:
        raise HTTPException(status_code=400, detail="Professor ID already exists.")
        
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

@router.get("/professors", response_model=List[schemas.user.Professor])
def read_professors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    return db.query(models.Professor).offset(skip).limit(limit).all()

# --- Students ---
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
        # device_id is nullable now, defaults to None
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

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

# --- Classes ---
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

# --- Courses (Definitions) ---
@router.post("/courses", response_model=schemas.academic.Course)
def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: schemas.academic.CourseCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    # Check if code exists
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

# --- Teaching Assignments ---
@router.post("/assignments", response_model=schemas.academic.TeachingAssignment)
def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assign_in: schemas.academic.TeachingAssignmentCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    # Check if duplicate assignment exists
    exists = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.course_id == assign_in.course_id,
        models.TeachingAssignment.class_group_id == assign_in.class_group_id,
        models.TeachingAssignment.professor_id == assign_in.professor_id
    ).first()
    
    if exists:
        return exists # Return existing if essentially same

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

# --- Bell Schedule ---
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
    # Simplest approach: Delete all and re-insert, or update matching slots.
    # We'll update matching slots for safety.
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

# --- Timetable (Grid Logic) ---
@router.get("/timetable/{class_group_id}", response_model=List[schemas.academic.TimeTable])
def read_timetable_grid(
    class_group_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    # Return all timetable entries for this class
    # We join Assignment to filter by class_group_id
    entries = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_group_id == class_group_id
    ).all()
    return entries

@router.post("/timetable/slot", response_model=schemas.academic.TimeTable)
def update_timetable_slot(
    *,
    db: Session = Depends(deps.get_db),
    slot_in: schemas.academic.TimeTableCreate, # Contains assignment_id, day, slot
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    # 1. Verify Assignment exists
    assign = db.query(models.TeachingAssignment).filter(models.TeachingAssignment.id == slot_in.assignment_id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 2. Check if this class already has something at this slot
    # We need to find if there is an existing TimeTable entry for this ClassGroup + Day + Slot
    # BUT TimeTable table only has assignment_id. We need to check the ClassGroup of the *existing* assignment.
    
    existing_entry = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_group_id == assign.class_group_id,
        models.TimeTable.day_of_week == slot_in.day_of_week,
        models.TimeTable.hour_slot == slot_in.hour_slot
    ).first()

    if existing_entry:
        # Update existing
        existing_entry.assignment_id = slot_in.assignment_id
        db.commit()
        db.refresh(existing_entry)
        return existing_entry
    else:
        # Create new
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