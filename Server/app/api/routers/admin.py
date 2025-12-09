from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import security

router = APIRouter()

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
        raise HTTPException(status_code=400, detail="The professor with this email already exists.")
    
    prof_id = db.query(models.Professor).filter(models.Professor.id == professor_in.id).first()
    if prof_id:
        raise HTTPException(status_code=400, detail="The professor with this ID already exists.")
        
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
    profs = db.query(models.Professor).offset(skip).limit(limit).all()
    return profs

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
        raise HTTPException(status_code=400, detail="Student with this ID already exists.")
        
    db_student = models.Student(
        id=student_in.id,
        digital_id=student_in.digital_id,
        name=student_in.name,
        email=student_in.email,
        department=student_in.department,
        year=student_in.year,
        class_group_id=student_in.class_group_id,
        # device_id is usually registered by app, but can be pre-seeded
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

# --- Courses ---
@router.post("/courses", response_model=schemas.academic.Course)
def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: schemas.academic.CourseCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
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

# --- Timetable ---
@router.post("/timetables", response_model=schemas.academic.TimeTable)
def create_timetable(
    *,
    db: Session = Depends(deps.get_db),
    timetable_in: schemas.academic.TimeTableCreate,
    current_admin: models.Admin = Depends(deps.get_current_active_admin),
):
    db_tt = models.TimeTable(**timetable_in.dict())
    db.add(db_tt)
    db.commit()
    db.refresh(db_tt)
    return db_tt
