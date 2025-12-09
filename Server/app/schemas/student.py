from pydantic import BaseModel
from typing import Optional

class AttendanceSubmit(BaseModel):
    code: str
    device_uuid: str
    rssi: float

class AttendanceResponse(BaseModel):
    status: str
    message: str
