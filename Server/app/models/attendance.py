from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, func, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Link to the specific teaching assignment (Course + Prof + Class)
    assignment_id = Column(Integer, ForeignKey("teaching_assignments.id"))
    assignment = relationship("TeachingAssignment", back_populates="attendance_sessions")
    
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
    
    student_id = Column(BigInteger, ForeignKey("students.id")) 
    student = relationship("Student", back_populates="attendance_records")
    
    status = Column(String) # PRESENT, ABSENT, LATE
    timestamp = Column(DateTime, default=func.now())
    rssi_strength = Column(Float, nullable=True)