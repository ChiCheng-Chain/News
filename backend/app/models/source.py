from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.database import Base

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    type = Column(Enum("rss", "api"))
    url = Column(String(500))
    language = Column(String(10))
    enabled = Column(Boolean, default=True)
