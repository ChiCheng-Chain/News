from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
from app.database import get_db
from app.models import Digest

router = APIRouter()

@router.get("/api/digest")
def get_digest(date: Optional[date_type] = None, db: Session = Depends(get_db)):
    query_date = date or date_type.today()
    digest = db.query(Digest).filter(Digest.date == query_date).first()
    if not digest:
        raise HTTPException(status_code=404, detail="该日期暂无简报")
    return {
        "id": digest.id,
        "date": str(digest.date),
        "content": digest.content,
        "triggered_by": digest.triggered_by,
        "created_at": str(digest.created_at),
    }
