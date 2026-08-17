from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
# Import the assignment schema to nest it
from .academic import TeachingAssignment 

from .user import Student

# --- Records ---
class AttendanceRecordBase(BaseModel):
    status: str 
    timestamp: Optional[datetime] = None
    rssi_strength: Optional[float] = None

class AttendanceRecordCreate(BaseModel):
    code: str
    device_uuid: str
    rssi: Optional[float] = None 
    
class AttendanceRecord(AttendanceRecordBase):
    id: int
    student_id: int
    student: Optional[Student] = None  # Added student field
    
    class Config:
        from_attributes = True

# --- Sessions ---
class AttendanceSessionBase(BaseModel):
    is_active: bool = True

class AttendanceSessionCreate(BaseModel):
    course_id: int
    class_group_id: int
    duration_minutes: Optional[int] = 5
    room_number: str

class AttendanceSession(AttendanceSessionBase):
    id: int
    assignment_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    current_code: Optional[str] = None
    student_count: Optional[int] = 0  # Added for history view
    room_number: Optional[str] = None
    headcount: Optional[int] = None
    is_verified: bool = False
    verification_status: Optional[str] = None
    
    # NESTED OBJECT: This fixes the empty () in the UI
    assignment: Optional[TeachingAssignment] = None 
    
    class Config:
        from_attributes = True

class AttendanceSessionDetails(AttendanceSession):
    records: List[AttendanceRecord] = []
    student_count: Optional[int] = 0
    room_number: Optional[str] = None
    headcount: Optional[int] = None
    is_verified: bool = False
    verification_status: Optional[str] = None
    
    class Config:
        from_attributes = True

class HeadcountVerifyResponse(BaseModel):
    session_id: int
    headcount: Optional[int] = None
    headcount_students: Optional[int] = None  # headcount - 1
    attendance_count: int
    is_match: bool
    difference: int
    records: List[AttendanceRecord] = []