import logging
from typing import List, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.api import deps
from app.core import mqtt
from app.core.ws_manager import manager as ws_manager
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        room_number=session_in.room_number,
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
    
    # Stop Beacon — use the same composite classroom_id format as start
    class_group = session.assignment.class_group
    if class_group:
        # Use composite ID consistent with start_session
        composite_classroom_id = f"{class_group.name}_{session.room_number}"
        mqtt.send_beacon_command(
            command="stop_session",
            classroom_id=composite_classroom_id
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
        joinedload(models.AttendanceSession.records).joinedload(models.AttendanceRecord.student),
        joinedload(models.AttendanceSession.assignment).joinedload(models.TeachingAssignment.course),
        joinedload(models.AttendanceSession.assignment).joinedload(models.TeachingAssignment.class_group)
    ).filter(models.AttendanceSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.assignment.professor_id != current_prof.id:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    session.student_count = len(session.records)
    return session

@router.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: int, token: str = Query(...)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if not subject or not subject.startswith("professor:"):
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)

@router.post("/attendance/verify/{session_id}", response_model=schemas.attendance.HeadcountVerifyResponse)
def verify_headcount(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    session = db.query(models.AttendanceSession).options(
        joinedload(models.AttendanceSession.records).joinedload(models.AttendanceRecord.student)
    ).filter(models.AttendanceSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.assignment.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    attendance_count = len(session.records)
    headcount = session.headcount
    headcount_students = (headcount - 1) if headcount is not None else None
    
    is_match = headcount_students == attendance_count if headcount_students is not None else False
    difference = (headcount_students - attendance_count) if headcount_students is not None else 0
    
    if is_match:
        session.is_verified = True
        session.verification_status = "MATCHED"
        db.commit()
    
    return schemas.attendance.HeadcountVerifyResponse(
        session_id=session.id,
        headcount=headcount,
        headcount_students=headcount_students,
        attendance_count=attendance_count,
        is_match=is_match,
        difference=difference,
        records=session.records
    )

@router.post("/attendance/retake/{session_id}", response_model=schemas.attendance.AttendanceSession)
def retake_attendance(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    old_session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id
    ).first()
    if not old_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if old_session.assignment.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_session.is_active = False
    old_session.end_time = datetime.now(timezone.utc)
    old_session.verification_status = "RETAKEN"
    
    class_group = old_session.assignment.class_group
    if class_group:
        composite_classroom_id = f"{class_group.name}_{old_session.room_number}"
        mqtt.send_beacon_command(command="stop_session", classroom_id=composite_classroom_id)
    
    duration_min = 5
    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_min)
    
    new_session = models.AttendanceSession(
        assignment_id=old_session.assignment_id,
        room_number=old_session.room_number,
        start_time=datetime.now(timezone.utc),
        end_time=end_time,
        is_active=True
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    if class_group:
        composite_classroom_id = f"{class_group.name}_{old_session.room_number}"
        try:
            mqtt.send_beacon_command(
                command="start_session",
                classroom_id=composite_classroom_id,
                duration_minutes=duration_min,
                session_id=new_session.id
            )
        except Exception as e:
            db.delete(new_session)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to start beacon: {str(e)}")
    
    return new_session

@router.delete("/attendance/record/{record_id}")
def remove_attendance_record(
    record_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    record = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.id == record_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    session = record.session
    if session.assignment.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    session_id = session.id
    db.delete(record)
    db.commit()
    
    updated_count = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session_id
    ).count()
    
    ws_manager.broadcast_from_thread(session_id, {
        "type": "attendance_update",
        "session_id": session_id,
        "headcount": session.headcount,
        "attendance_count": updated_count
    })
    
    return {"message": "Record removed", "attendance_count": updated_count}

@router.post("/attendance/verify/{session_id}/save")
def save_despite_mismatch(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_prof: models.Professor = Depends(deps.get_current_active_professor),
):
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.assignment.professor_id != current_prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    session.is_verified = True
    session.verification_status = "MISMATCH_SAVED"
    db.commit()
    
    return {"message": "Session saved despite mismatch", "verification_status": "MISMATCH_SAVED"}