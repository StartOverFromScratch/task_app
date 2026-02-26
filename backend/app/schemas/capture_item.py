from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CaptureCreateRequest(BaseModel):
    text: str
    related_task_id: Optional[int] = None


class CaptureUpdateRequest(BaseModel):
    text: Optional[str] = None
    is_resolved: Optional[bool] = None
    related_task_id: Optional[int] = None


class CaptureItemResponse(BaseModel):
    id: int
    text: str
    related_task_id: Optional[int] = None
    created_at: datetime
    is_resolved: bool

    model_config = {"from_attributes": True}
