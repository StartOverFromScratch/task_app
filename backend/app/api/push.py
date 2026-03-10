from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.notification_setting import NotificationSetting
from app.models.push_subscription import PushSubscription
from app.schemas.notification_setting import NotificationSettingResponse, NotificationSettingUpdate
from app.schemas.push import PushSubscribeRequest, PushSendRequest
from app.services import push_service
from app.services.scheduler import update_schedule

router = APIRouter()


@router.get("/vapid-public-key")
def get_vapid_public_key():
    return {"public_key": settings.vapid_public_key}


@router.post("/subscribe", status_code=201)
def subscribe(req: PushSubscribeRequest, db: Session = Depends(get_db)):
    sub = push_service.upsert_subscription(db, req.endpoint, req.keys.p256dh, req.keys.auth)
    return {"id": sub.id}


@router.delete("/subscribe")
def unsubscribe(req: PushSubscribeRequest, db: Session = Depends(get_db)):
    ok = push_service.delete_subscription(db, req.endpoint)
    if not ok:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"ok": True}


@router.post("/send-test")
def send_test(req: PushSendRequest, db: Session = Depends(get_db)):
    subscriptions = db.query(PushSubscription).all()
    if not subscriptions:
        raise HTTPException(status_code=404, detail="No subscriptions found")
    sent = sum(1 for sub in subscriptions if push_service.send_push(sub, req.title, req.body))
    return {"sent": sent, "total": len(subscriptions)}


@router.post("/send-today-due")
def send_today_due(db: Session = Depends(get_db)):
    result = push_service.send_today_due_notification(db)
    return result


@router.get("/notification-setting", response_model=NotificationSettingResponse)
def get_notification_setting(db: Session = Depends(get_db)):
    setting = db.query(NotificationSetting).filter(NotificationSetting.id == 1).first()
    if not setting:
        return NotificationSettingResponse(notify_time=None, enabled=False)
    return NotificationSettingResponse(notify_time=setting.notify_time, enabled=setting.enabled)


@router.put("/notification-setting", response_model=NotificationSettingResponse)
def update_notification_setting(req: NotificationSettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(NotificationSetting).filter(NotificationSetting.id == 1).first()
    if setting:
        setting.notify_time = req.notify_time
        setting.enabled = req.enabled
    else:
        setting = NotificationSetting(id=1, notify_time=req.notify_time, enabled=req.enabled)
        db.add(setting)
    db.commit()
    db.refresh(setting)

    update_schedule(setting.notify_time, setting.enabled)
    return NotificationSettingResponse(notify_time=setting.notify_time, enabled=setting.enabled)
