from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Source

router = APIRouter()

class SourceUpdate(BaseModel):
    enabled: bool

@router.get("/api/sources")
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return [{"id": s.id, "name": s.name, "type": s.type,
             "url": s.url, "language": s.language, "enabled": s.enabled} for s in sources]

@router.put("/api/sources/{source_id}")
def update_source(source_id: int, body: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    source.enabled = body.enabled
    db.commit()
    return {"id": source.id, "name": source.name, "enabled": source.enabled}
