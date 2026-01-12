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
    # Link to assignments that belong to this class
    assignments = relationship("TeachingAssignment", back_populates="class_group")

class Course(Base):
    """
    Defines a generic course, e.g. "UCS1234: Data Structures"
    """
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True) # e.g. UCS1234
    name = Column(String) # e.g. Data Structures
    department = Column(String) # e.g. CSE

    assignments = relationship("TeachingAssignment", back_populates="course")

class TeachingAssignment(Base):
    """
    Links a Course, a Professor, and a ClassGroup.
    Example: "Dr. Smith teaches UCS1234 to CSE-A"
    """
    __tablename__ = "teaching_assignments"

    id = Column(Integer, primary_key=True, index=True)
    
    course_id = Column(Integer, ForeignKey("courses.id"))
    professor_id = Column(Integer, ForeignKey("professors.id"))
    class_group_id = Column(Integer, ForeignKey("class_groups.id"))

    default_classroom = Column(String, nullable=True)

    course = relationship("Course", back_populates="assignments")
    professor = relationship("Professor", back_populates="assignments")
    class_group = relationship("ClassGroup", back_populates="assignments")
    
    timetables = relationship("TimeTable", back_populates="assignment")
    attendance_sessions = relationship("AttendanceSession", back_populates="assignment")

class TimeTable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    
    assignment_id = Column(Integer, ForeignKey("teaching_assignments.id"))
    assignment = relationship("TeachingAssignment", back_populates="timetables")
    
    day_of_week = Column(Integer) # 0=Monday, 5=Saturday
    hour_slot = Column(Integer) # 1-8