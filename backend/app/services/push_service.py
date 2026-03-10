from datetime import date
import json

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.models.task import Task


def upsert_subscription(db: Session, endpoint: str, p256dh: str, auth: str) -> PushSubscription:
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if sub:
        sub.p256dh = p256dh
        sub.auth = auth
    else:
        sub = PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, endpoint: str) -> bool:
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if not sub:
        return False
    db.delete(sub)
    db.commit()
    return True


def send_push(subscription: PushSubscription, title: str, body: str) -> bool:
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_mailto},
        )
        print(f"[push] sent OK: endpoint={subscription.endpoint[:40]}...", flush=True)
        return True
    except Exception as e:
        print(f"[push] send FAILED: endpoint={subscription.endpoint[:40]}... error={e}", flush=True)
        return False


def get_today_due_tasks(db: Session) -> list[Task]:
    today = date.today()
    return (
        db.query(Task)
        .filter(Task.due_date == today, Task.status.notin_(["done", "snoozed"]))
        .order_by(Task.priority.desc())
        .all()
    )


def send_today_due_notification(db: Session) -> dict:
    tasks = get_today_due_tasks(db)
    subscriptions = db.query(PushSubscription).all()

    if not subscriptions:
        return {"sent": 0, "task_count": len(tasks), "skipped": "no_subscriptions"}

    if not tasks:
        title = "今日の期限タスク"
        body = "今日期限のタスクはありません"
    else:
        title = f"今日の期限タスク（{len(tasks)}件）"
        body = "・" + "\n・".join(t.title for t in tasks[:5])
        if len(tasks) > 5:
            body += f"\n他 {len(tasks) - 5} 件"

    sent = sum(1 for sub in subscriptions if send_push(sub, title, body))
    return {"sent": sent, "total_subscriptions": len(subscriptions), "task_count": len(tasks)}
