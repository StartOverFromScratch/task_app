from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.capture_item import CaptureCreateRequest, CaptureItemResponse, CaptureUpdateRequest
from app.services import capture_service

router = APIRouter()


@router.get("", response_model=list[CaptureItemResponse])
def list_captures(is_resolved: Optional[bool] = None, db: Session = Depends(get_db)):
    return capture_service.get_captures(db, is_resolved=is_resolved)


@router.post("", response_model=CaptureItemResponse, status_code=status.HTTP_201_CREATED)
def create_capture(data: CaptureCreateRequest, db: Session = Depends(get_db)):
    return capture_service.create_capture(db, data)


@router.patch("/{capture_id}", response_model=CaptureItemResponse)
def update_capture(capture_id: int, data: CaptureUpdateRequest, db: Session = Depends(get_db)):
    return capture_service.update_capture(db, capture_id, data)


@router.delete("/{capture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_capture(capture_id: int, db: Session = Depends(get_db)):
    capture_service.delete_capture(db, capture_id)
