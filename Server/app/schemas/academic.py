from pydantic import BaseModel
from typing import Optional, List
from datetime import time

# ClassGroup
class ClassGroupBase(BaseModel):
    name: str # e.g. "CSE C"
    department: Optional[str] = None
    year: Optional[int] = None

class ClassGroupCreate(ClassGroupBase):
    pass

class ClassGroup(ClassGroupBase):
    id: int
    class Config:
        from_attributes = True

# Course (Definition)
class CourseBase(BaseModel):
    code: str
    name: str
    department: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None

class Course(CourseBase):
    id: int
    class Config:
        from_attributes = True

# Teaching Assignment
class TeachingAssignmentBase(BaseModel):
    course_id: int
    professor_id: int
    class_group_id: int

class TeachingAssignmentCreate(TeachingAssignmentBase):
    pass

class TeachingAssignment(TeachingAssignmentBase):
    id: int
    course: Optional[Course] = None
    class_group: Optional[ClassGroup] = None
    
    class Config:
        from_attributes = True

# TimeTable
class TimeTableBase(BaseModel):
    assignment_id: int
    day_of_week: int # 0-5 (Mon-Sat)
    hour_slot: int # 1-8

class TimeTableCreate(TimeTableBase):
    pass

class TimeTable(TimeTableBase):
    id: int
    assignment: Optional[TeachingAssignment] = None
    class Config:
        from_attributes = True

# Bell Schedule
class BellScheduleBase(BaseModel):
    slot_number: int
    start_time: time
    end_time: time

class BellScheduleCreate(BellScheduleBase):
    pass

class BellSchedule(BellScheduleBase):
    id: int
    class Config:
        from_attributes = True