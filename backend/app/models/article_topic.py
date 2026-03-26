from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class ArticleTopic(Base):
    __tablename__ = "article_topics"
    article_id = Column(Integer, ForeignKey("articles.id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), primary_key=True)
    viewpoint_label = Column(String(100))
