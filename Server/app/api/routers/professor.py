from typing import List, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import mqtt

router = APIRouter()

@router.get("/my-courses", response_model=List[schemas.academic.Course])
def read_my_courses(
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    return current_prof.courses

@router.get("/my-timetable", response_model=List[schemas.academic.TimeTable])
def read_my_timetable(
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # Get all timetables for this prof's courses
    timetables = db.query(models.TimeTable).join(models.Course).filter(models.Course.professor_id == current_prof.id).all()
    return timetables

@router.post("/attendance/start", response_model=schemas.attendance.AttendanceSession)
def start_attendance(
    *,
    db: Session = Depends(deps.get_db),
    session_in: schemas.attendance.AttendanceSessionCreate,
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    # 1. Verify Course ownership
    course = db.query(models.Course).filter(models.Course.id == session_in.course_id).first()
    if not course or course.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="You do not teach this course")
        
    # 2. Get ClassGroup to determine Classroom ID for Beacon
    class_group = db.query(models.ClassGroup).filter(models.ClassGroup.id == session_in.class_group_id).first()
    if not class_group:
         raise HTTPException(status_code=404, detail="Class Group not found")

    # 3. Create Session in DB
    duration_min = session_in.duration_minutes or 5
    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_min)
    
    db_session = models.AttendanceSession(
        course_id=session_in.course_id,
        class_group_id=session_in.class_group_id,
        start_time=datetime.now(timezone.utc),
        end_time=end_time,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # 4. Trigger Beacon via MQTT
    # Assuming ClassGroup.name (e.g. "CSC2") is the identifier used in Beacon Controller config
    try:
        mqtt.send_beacon_command(
            command="start_session",
            classroom_id=class_group.name,
            duration_minutes=duration_min,
            session_id=db_session.id
        )
    except Exception as e:
        # MQTT Failed! Undo the DB change so we don't have a "fake" active session
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
        
    # Verify ownership via course
    course = db.query(models.Course).filter(models.Course.id == session.course_id).first()
    if course.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.is_active = False
    session.end_time = datetime.now(timezone.utc) # Update end time to now
    db.commit()
    
    class_group = db.query(models.ClassGroup).filter(models.ClassGroup.id == session.class_group_id).first()
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
    # Return sessions for courses taught by this prof
    sessions = db.query(models.AttendanceSession).join(models.Course).filter(models.Course.professor_id == current_prof.id).order_by(models.AttendanceSession.start_time.desc()).all()
    return sessions
