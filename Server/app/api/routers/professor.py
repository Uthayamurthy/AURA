from typing import List, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.api import deps
from app.core import mqtt

router = APIRouter()

@router.get("/my-courses", response_model=List[schemas.academic.TeachingAssignment])
def read_my_courses(
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    return current_prof.assignments

@router.get("/my-timetable", response_model=List[schemas.academic.TimeTable])
def read_my_timetable(
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # Get all timetables where the assignment -> professor is me
    timetables = db.query(models.TimeTable).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.professor_id == current_prof.id
    ).all()
    return timetables

@router.post("/attendance/start", response_model=schemas.attendance.AttendanceSession)
def start_attendance(
    *,
    db: Session = Depends(deps.get_db),
    session_in: schemas.attendance.AttendanceSessionCreate, # expects course_id, class_group_id
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # 1. Verify Teaching Assignment exists for this Prof + Course + Class
    assignment = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.professor_id == current_prof.id,
        models.TeachingAssignment.course_id == session_in.course_id,
        models.TeachingAssignment.class_group_id == session_in.class_group_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to teach this course to this class.")
        
    # 2. Get ClassGroup to determine Classroom ID for Beacon (needed for MQTT)
    class_group = assignment.class_group # loaded via relationship
    if not class_group:
         raise HTTPException(status_code=404, detail="Class Group not found")

    # 3. Create Session in DB
    duration_min = session_in.duration_minutes or 5
    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_min)
    
    db_session = models.AttendanceSession(
        assignment_id=assignment.id, # Link to Assignment now!
        start_time=datetime.now(timezone.utc),
        end_time=end_time,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # 4. Trigger Beacon via MQTT
    composite_classroom_id = f"{class_group.name}_{session_in.room_number}"

    try:
        mqtt.send_beacon_command(
            command="start_session",
            classroom_id=composite_classroom_id,
            duration_minutes=duration_min,
            session_id=db_session.id
        )
    except Exception as e:
        db.delete(db_session)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start beacon: {str(e)}")
    
    return db_session

@router.post("/attendance/stop/{session_id}")
def stop_attendance(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    session = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Verify ownership via assignment -> professor
    if session.assignment.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.is_active = False
    session.end_time = datetime.now(timezone.utc)
    db.commit()
    
    # Stop Beacon
    class_group = session.assignment.class_group
    if class_group:
         mqtt.send_beacon_command(
            command="stop_session",
            classroom_id=class_group.name
        )
    
    return {"message": "Attendance stopped"}

@router.get("/attendance/history", response_model=List[schemas.attendance.AttendanceSession])
def read_attendance_history(
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # Eagerly load assignment, course, and class_group for proper serialization
    sessions = db.query(models.AttendanceSession).options(
        joinedload(models.AttendanceSession.assignment)
            .joinedload(models.TeachingAssignment.course),
        joinedload(models.AttendanceSession.assignment)
            .joinedload(models.TeachingAssignment.class_group),
        joinedload(models.AttendanceSession.records)  # For student_count
    ).join(models.TeachingAssignment).filter(
        models.TeachingAssignment.professor_id == current_prof.id
    ).order_by(models.AttendanceSession.start_time.desc()).all()
    
    for session in sessions:
        session.student_count = len(session.records)
        
    return sessions

@router.get("/attendance/session/{session_id}", response_model=schemas.attendance.AttendanceSessionDetails)
def read_session_details(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # Eagerly load records and the nested student for each record
    session = db.query(models.AttendanceSession).options(
        joinedload(models.AttendanceSession.records).joinedload(models.AttendanceRecord.student)
    ).filter(models.AttendanceSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.assignment.professor_id != current_prof.id:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    session.student_count = len(session.records)
    # session.attendees = session.records # Removed to fix serialization error
    return session