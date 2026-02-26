from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.capture_item import CaptureItem
from app.schemas.capture_item import CaptureCreateRequest, CaptureUpdateRequest


def get_captures(db: Session, is_resolved: Optional[bool] = None) -> list[CaptureItem]:
    q = db.query(CaptureItem)
    if is_resolved is not None:
        q = q.filter(CaptureItem.is_resolved == is_resolved)
    return q.order_by(CaptureItem.created_at.desc()).all()


def create_capture(db: Session, data: CaptureCreateRequest) -> CaptureItem:
    item = CaptureItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_capture(db: Session, capture_id: int, data: CaptureUpdateRequest) -> CaptureItem:
    item = db.get(CaptureItem, capture_id)
    if not item:
        raise HTTPException(status_code=404, detail="キャプチャアイテムが見つかりません")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_capture(db: Session, capture_id: int) -> None:
    item = db.get(CaptureItem, capture_id)
    if not item:
        raise HTTPException(status_code=404, detail="キャプチャアイテムが見つかりません")
    db.delete(item)
    db.commit()
