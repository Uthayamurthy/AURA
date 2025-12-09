from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app import models, schemas
from app.api import deps

router = APIRouter()

@router.post("/attendance/submit", response_model=schemas.student.AttendanceResponse)
def submit_attendance(
    *,
    db: Session = Depends(deps.get_db),
    submission: schemas.student.AttendanceSubmit,
    current_student: models.Student = Depends(deps.get_current_active_student),
):
    # 1. Verify Student - Check if the device UUID matches and in future, check RSSI

    student = current_student

    if student.device_id != submission.device_uuid:
        raise HTTPException(status_code=401, detail="Unauthorized device. Please use your registered phone.")
    
    # TODO: Optionally verify RSSI strength to ensure proximity. Skipping for now. Will do some experiments and then add this.
    # MIN_RSSI_THRESHOLD = -80  # Example threshold value, adjust as needed
    # if submission.rssi < MIN_RSSI_THRESHOLD:
    #     raise HTTPException(status_code=400, detail="Signal too weak. Please move closer to the beacon.")
    
    # 2. Find Active Session for Student's Class Group
    # We join with ClassGroup to be sure, or just look up by class_group_id
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_group_id == student.class_group_id,
        models.AttendanceSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(status_code=400, detail="No active attendance session for your class")
        
    # 3. Verify Code
    # The session.current_code is updated by the MQTT Listener background service
    if not session.current_code:
        raise HTTPException(status_code=400, detail="Attendance not yet ready (Wait for code)")
        
    if session.current_code != submission.code:
         raise HTTPException(status_code=400, detail="Invalid Code")

    # 4. Check for duplicate
    existing_record = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session.id,
        models.AttendanceRecord.student_id == student.id
    ).first()
    
    if existing_record:
        return {"status": "success", "message": "Attendance already marked"}

    # 5. Mark Attendance
    record = models.AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        status="PRESENT",
        timestamp=datetime.now(timezone.utc),
        rssi_strength=submission.rssi
    )
    db.add(record)
    db.commit()
    
    return {"status": "success", "message": "Attendance marked successfully"}
