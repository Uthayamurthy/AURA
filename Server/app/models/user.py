from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True) # 6 Digit ID
    name = Column(String)
    email = Column(String, unique=True, index=True)
    department = Column(String)
    password_hash = Column(String)
    
    courses = relationship("Course", back_populates="professor")

class Student(Base):
    __tablename__ = "students"

    id = Column(BigInteger, primary_key=True, index=True) # 13 Digit ID
    digital_id = Column(Integer, index=True) # 7 Digit ID
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    device_id = Column(String, nullable=True) # UUID
    department = Column(String)
    year = Column(Integer)
    
    class_group_id = Column(Integer, ForeignKey("class_groups.id"))
    class_group = relationship("ClassGroup", back_populates="students")
    
    attendance_records = relationship("AttendanceRecord", back_populates="student")
