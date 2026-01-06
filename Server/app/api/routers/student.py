from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas
from app.api import deps

router = APIRouter()

@router.get("/my-attendance", response_model=List[schemas.attendance.AttendanceRecord])
def read_my_attendance(
    db: Session = Depends(deps.get_db),
    current_student: models.Student = Depends(deps.get_current_active_student),
):
    return current_student.attendance_records

@router.post("/attendance/submit", response_model=schemas.attendance.AttendanceRecord)
def submit_attendance(
    *,
    db: Session = Depends(deps.get_db),
    submission: schemas.attendance.AttendanceRecordCreate,
    current_student: models.Student = Depends(deps.get_current_active_student),
):
    # 1. Device Security & First-Time Binding
    if not submission.device_uuid:
         raise HTTPException(status_code=400, detail="Device UUID is required")

    if current_student.device_id is None:
        # First time use: Bind this device to the student
        current_student.device_id = submission.device_uuid
        db.add(current_student)
        db.commit()
        db.refresh(current_student)
    elif current_student.device_id != submission.device_uuid:
        # Security Mismatch
        raise HTTPException(status_code=401, detail="Unauthorized device. Please use your registered phone.")

    # 2. Find the Active Session by Code
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.current_code == submission.code,
        models.AttendanceSession.is_active == True
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired beacon code.")

    # 3. Validate Class Membership
    if session.assignment.class_group_id != current_student.class_group_id:
         raise HTTPException(status_code=403, detail="You do not belong to this class group.")

    # 4. Check for Duplicate Submission
    existing = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session.id,
        models.AttendanceRecord.student_id == current_student.id
    ).first()
    
    if existing:
        return existing

    # 5. Create Attendance Record
    record = models.AttendanceRecord(
        session_id=session.id,
        student_id=current_student.id,
        status="PRESENT",
        rssi_strength=submission.rssi,
        timestamp=datetime.now()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record