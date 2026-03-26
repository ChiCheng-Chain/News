from sqlalchemy import Column, Integer, Date, Enum, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    status = Column(Enum("running", "done", "failed"))
    current_step = Column(String(50))
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
    error_msg = Column(Text)
