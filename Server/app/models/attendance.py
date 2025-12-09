from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="attendance_sessions")
    
    class_group_id = Column(Integer, ForeignKey("class_groups.id"))
    # Assuming we want to track which class this session was for, 
    # even though TimeTable links them. This is good for history.
    
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    current_code = Column(String, nullable=True, index=True)

    records = relationship("AttendanceRecord", back_populates="session")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
    session = relationship("AttendanceSession", back_populates="records")
    
    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", back_populates="attendance_records")
    
    status = Column(String) # PRESENT, ABSENT, LATE
    timestamp = Column(DateTime, default=func.now())
    rssi_strength = Column(Float, nullable=True)
