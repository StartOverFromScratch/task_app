from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.services.push_service import send_today_due_notification

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
JOB_ID = "daily_push"


def _run_daily_push():
    db = SessionLocal()
    try:
        send_today_due_notification(db)
    finally:
        db.close()


def update_schedule(notify_time: str | None, enabled: bool):
    scheduler.remove_job(JOB_ID) if scheduler.get_job(JOB_ID) else None

    if enabled and notify_time:
        hour, minute = notify_time.split(":")
        scheduler.add_job(
            _run_daily_push,
            CronTrigger(hour=int(hour), minute=int(minute), timezone="Asia/Tokyo"),
            id=JOB_ID,
            replace_existing=True,
        )


def start_scheduler():
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
