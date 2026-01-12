from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class DailyAttendance(BaseModel):
    date: date
    attendance_rate: float

class DashboardStats(BaseModel):
    total_students: int
    total_professors: int
    total_courses: int
    total_classes: int
    active_sessions: int
    todays_attendance_rate: float
    weekly_trend: List[DailyAttendance]
