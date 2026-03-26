from sqlalchemy import Column, Integer, Date, Text, JSON, Enum, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Digest(Base):
    __tablename__ = "digests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True)
    content = Column(Text)
    topic_ids = Column(JSON)
    triggered_by = Column(Enum("scheduled", "manual"))
    created_at = Column(DateTime, server_default=func.now())
