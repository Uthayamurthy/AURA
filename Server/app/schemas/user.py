from pydantic import BaseModel, EmailStr
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True

class ProfessorBase(UserBase):
    name: Optional[str] = None
    department: Optional[str] = None

class ProfessorCreate(ProfessorBase):
    email: EmailStr
    password: str
    id: int # 6 Digit ID

class ProfessorUpdate(ProfessorBase):
    password: Optional[str] = None

class Professor(ProfessorBase):
    id: int
    class Config:
        from_attributes = True

# Admin Schema (Simpler)
class AdminBase(BaseModel):
    username: str

class AdminCreate(AdminBase):
    password: str

class Admin(AdminBase):
    id: int
    class Config:
        from_attributes = True

# Student Schema
class StudentBase(UserBase):
    name: str
    department: Optional[str] = None
    year: Optional[int] = None
    class_group_id: Optional[int] = None
    device_id: Optional[str] = None # UUID

class StudentCreate(StudentBase):
    id: int # 13 Digit ID
    digital_id: int # 7 Digit ID
    email: EmailStr

class StudentUpdate(StudentBase):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class Student(StudentBase):
    id: int
    digital_id: int
    email: EmailStr
    class Config:
        from_attributes = True
