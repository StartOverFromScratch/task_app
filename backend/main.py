from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import captures, carryover, checklist, push, tasks
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.notification_setting import NotificationSetting
from app.services.scheduler import start_scheduler, stop_scheduler, update_schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: DB から通知設定を読み込んでスケジューラを初期化
    start_scheduler()
    db = SessionLocal()
    try:
        setting = db.query(NotificationSetting).filter(NotificationSetting.id == 1).first()
        if setting and setting.enabled and setting.notify_time:
            update_schedule(setting.notify_time, setting.enabled)
    finally:
        db.close()
    yield
    stop_scheduler()


app = FastAPI(title="タスク管理システム", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 固定パス（/stale, /carryover-candidates）を /{task_id} より先に登録する
app.include_router(carryover.router, prefix="/tasks", tags=["carryover"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(checklist.router, prefix="/tasks", tags=["checklist"])
app.include_router(captures.router, prefix="/captures", tags=["captures"])
app.include_router(push.router, prefix="/push", tags=["push"])


@app.get("/health")
def health():
    return {"status": "ok"}
