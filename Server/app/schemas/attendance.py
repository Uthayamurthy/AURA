from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# --- Records ---
class AttendanceRecordBase(BaseModel):
    status: str # PRESENT, ABSENT, LATE
    timestamp: Optional[datetime] = None
    rssi_strength: Optional[float] = None

class AttendanceRecordCreate(AttendanceRecordBase):
    student_id: int
    code: str
    device_uuid: Optional[str] = None

class AttendanceRecord(AttendanceRecordBase):
    id: int
    student_id: int
    # We can optionally include student details here if needed
    
    class Config:
        from_attributes = True

# --- Sessions ---
class AttendanceSessionBase(BaseModel):
    is_active: bool = True

class AttendanceSessionCreate(BaseModel):
    # Input still uses Course/Class because that's what the UI selects
    course_id: int
    class_group_id: int
    duration_minutes: Optional[int] = 5

class AttendanceSession(AttendanceSessionBase):
    id: int
    assignment_id: int  # <--- Changed from course_id/class_group_id
    start_time: datetime
    end_time: Optional[datetime] = None
    current_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class AttendanceSessionDetails(AttendanceSession):
    # For detailed view, include the list of attendees
    records: List[AttendanceRecord] = []
    student_count: Optional[int] = 0
    attendees: Optional[List[Any]] = [] # For flexibility in the response
    
    class Config:
        from_attributes = True