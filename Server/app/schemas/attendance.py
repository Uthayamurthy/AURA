from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AttendanceSessionBase(BaseModel):
    course_id: int
    class_group_id: int
    duration_minutes: Optional[int] = 5

class AttendanceSessionCreate(AttendanceSessionBase):
    pass

class AttendanceSession(AttendanceSessionBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool
    student_count: Optional[int] = 0 # Added for Statistics

    class Config:
        from_attributes = True

class AttendanceSessionDetails(AttendanceSession):
    attendees: List['AttendanceRecord'] = []


class AttendanceRecord(BaseModel):
    id: int
    student_id: int
    status: str
    timestamp: datetime
    class Config:
        from_attributes = True
