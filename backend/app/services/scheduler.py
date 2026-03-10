from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.services.push_service import send_today_due_notification

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
JOB_ID_1 = "daily_push_1"
JOB_ID_2 = "daily_push_2"


def _run_daily_push():
    db = SessionLocal()
    try:
        send_today_due_notification(db)
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


def update_schedule(notify_time_1: str | None, notify_time_2: str | None, enabled: bool):
    for job_id in (JOB_ID_1, JOB_ID_2):
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    if enabled:
        if notify_time_1:
            _add_job(JOB_ID_1, notify_time_1)
        if notify_time_2:
            _add_job(JOB_ID_2, notify_time_2)


def start_scheduler():
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
