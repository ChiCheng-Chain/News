from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100))
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(1000))
    published_at = Column(DateTime)
    language = Column(String(10))
    sentiment = Column(Enum("positive", "negative", "neutral"))
    is_duplicate = Column(Boolean, default=False)
    date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
