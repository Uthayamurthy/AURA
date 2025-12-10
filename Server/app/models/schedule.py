from sqlalchemy import Column, Integer, Time
from app.core.database import Base

class BellSchedule(Base):
    __tablename__ = "bell_schedule"

    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(Integer, unique=True, index=True) # 1 to 8
    start_time = Column(Time)
    end_time = Column(Time)