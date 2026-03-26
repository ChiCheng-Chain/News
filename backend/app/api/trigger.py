from fastapi import APIRouter, HTTPException
from datetime import date, datetime
from app.models import PipelineRun
from app.database import SessionLocal
from app.pipeline.graph import run_pipeline
import threading

router = APIRouter()

def _run_in_background(run_id: int, run_date: str):
    try:
        run_pipeline(run_date=run_date, triggered_by="manual")
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            if run:
                run.status = "done"
                run.current_step = "done"
                run.finished_at = datetime.now()
                db.commit()
    except Exception as e:
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            if run:
                run.status = "failed"
                run.error_msg = str(e)
                run.finished_at = datetime.now()
                db.commit()

@router.post("/api/trigger")
def trigger_pipeline():
    today = date.today()
    with SessionLocal() as db:
        existing = db.query(PipelineRun).filter(
            PipelineRun.date == today,
            PipelineRun.status.in_(["running", "done"])
        ).first()
        if existing:
            if existing.status == "running":
                raise HTTPException(status_code=409, detail="今日Pipeline正在运行中")
            raise HTTPException(status_code=409, detail="今日Pipeline已完成，如需重跑请直接重置")

        run = PipelineRun(date=today, status="running", current_step="collect")
        db.add(run)
        db.commit()
        run_id = run.id

    thread = threading.Thread(target=_run_in_background, args=(run_id, today.isoformat()), daemon=True)
    thread.start()
    return {"message": "Pipeline已启动", "run_id": run_id}

@router.get("/api/pipeline/status")
def get_pipeline_status():
    today = date.today()
    with SessionLocal() as db:
        run = db.query(PipelineRun).filter(PipelineRun.date == today).order_by(
            PipelineRun.started_at.desc()
        ).first()
        if not run:
            return {"status": "idle", "current_step": None, "started_at": None, "finished_at": None, "error_msg": None}
        return {
            "status": run.status,
            "current_step": run.current_step,
            "started_at": str(run.started_at) if run.started_at else None,
            "finished_at": str(run.finished_at) if run.finished_at else None,
            "error_msg": run.error_msg,
        }
