from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g. "CSE C"
    department = Column(String)
    year = Column(Integer)

    students = relationship("Student", back_populates="class_group")
    timetables = relationship("TimeTable", back_populates="class_group")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # e.g. "Data Structures"
    
    professor_id = Column(Integer, ForeignKey("professors.id"))
    professor = relationship("Professor", back_populates="courses")
    
    timetables = relationship("TimeTable", back_populates="course")
    attendance_sessions = relationship("AttendanceSession", back_populates="course")

class TimeTable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    
    class_group_id = Column(Integer, ForeignKey("class_groups.id"))
    class_group = relationship("ClassGroup", back_populates="timetables")
    
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="timetables")
    
    day_of_week = Column(Integer) # 0=Monday, 6=Sunday
    hour_slot = Column(Integer) # 1-8
