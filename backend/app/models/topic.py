from sqlalchemy import Column, Integer, String, Text, Date, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500))
    summary = Column(Text)
    perspectives = Column(JSON)
    is_blind_spot = Column(Boolean, default=False)
    date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
