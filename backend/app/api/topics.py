from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
from app.database import get_db
from app.models import Topic

router = APIRouter()

@router.get("/api/topics")
def get_topics(date: Optional[date_type] = None, db: Session = Depends(get_db)):
    query_date = date or date_type.today()
    topics = db.query(Topic).filter(Topic.date == query_date).all()
    return [{"id": t.id, "title": t.title, "summary": t.summary,
             "perspectives": t.perspectives, "is_blind_spot": t.is_blind_spot,
             "date": str(t.date)} for t in topics]

@router.get("/api/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    return {"id": topic.id, "title": topic.title, "summary": topic.summary,
            "perspectives": topic.perspectives, "is_blind_spot": topic.is_blind_spot,
            "date": str(topic.date)}
