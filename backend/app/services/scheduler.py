import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.services.push_service import send_today_due_notification

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
JOB_ID_1 = "daily_push_1"
JOB_ID_2 = "daily_push_2"


def _run_daily_push():
    print("[scheduler] _run_daily_push fired", flush=True)
    db = SessionLocal()
    try:
        result = send_today_due_notification(db)
        print(f"[scheduler] send result: {result}", flush=True)
    except Exception as e:
        print(f"[scheduler] error in _run_daily_push: {e}", flush=True)
    finally:
        db.close()


def _add_job(job_id: str, notify_time: str):
    hour, minute = notify_time.split(":")
    scheduler.add_job(
        _run_daily_push,
        CronTrigger(hour=int(hour), minute=int(minute), timezone="Asia/Tokyo"),
        id=job_id,
        replace_existing=True,
    )
    print(f"[scheduler] job added: id={job_id} time={notify_time}", flush=True)


def update_schedule(notify_time_1: str | None, notify_time_2: str | None, enabled: bool):
    for job_id in (JOB_ID_1, JOB_ID_2):
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            print(f"[scheduler] job removed: id={job_id}", flush=True)

    if enabled:
        if notify_time_1:
            _add_job(JOB_ID_1, notify_time_1)
        if notify_time_2:
            _add_job(JOB_ID_2, notify_time_2)
    print(f"[scheduler] update_schedule done: enabled={enabled} jobs={[j.id for j in scheduler.get_jobs()]}", flush=True)


def start_scheduler():
    scheduler.start()
    print("[scheduler] started", flush=True)


def stop_scheduler():
    scheduler.shutdown(wait=False)
    print("[scheduler] stopped", flush=True)
