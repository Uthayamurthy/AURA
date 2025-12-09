from pydantic import BaseModel
from typing import Optional, List

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

# Course
class CourseBase(BaseModel):
    name: str
    professor_id: Optional[int] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    class Config:
        from_attributes = True

# TimeTable
class TimeTableBase(BaseModel):
    class_group_id: int
    course_id: int
    day_of_week: int # 0-6
    hour_slot: int # 1-8

class TimeTableCreate(TimeTableBase):
    pass

class TimeTable(TimeTableBase):
    id: int
    class Config:
        from_attributes = True
