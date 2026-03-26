from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.pipeline.graph import run_pipeline
from app.models import PipelineRun
from app.database import SessionLocal

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

def _run_daily():
    today = date.today()
    with SessionLocal() as db:
        existing = db.query(PipelineRun).filter(
            PipelineRun.date == today,
            PipelineRun.status.in_(["running", "done"])
        ).first()
        if existing:
            return

        run = PipelineRun(date=today, status="running", current_step="collect")
        db.add(run)
        db.commit()
        run_id = run.id

    try:
        run_pipeline(run_date=today.isoformat(), triggered_by="scheduled")
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

def start_scheduler():
    scheduler.add_job(_run_daily, CronTrigger(hour=20, minute=0, timezone="Asia/Shanghai"))
    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
