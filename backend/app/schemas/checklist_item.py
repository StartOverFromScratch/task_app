from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import Priority, TaskType


class ChecklistItemCreate(BaseModel):
    text: str
    order_no: Optional[int] = None


class ChecklistItemResponse(BaseModel):
    id: int
    task_id: int
    text: str
    is_done: bool
    order_no: int
    extracted_task_id: Optional[int] = None

    model_config = {"from_attributes": True}


class ChecklistItemUpdate(BaseModel):
    is_done: Optional[bool] = None
    text: Optional[str] = None


class ExtractRequest(BaseModel):
    title: Optional[str] = None
    task_type: TaskType = TaskType.execution
    priority: Optional[Priority] = None
    due_date: Optional[date] = None
    done_criteria: Optional[str] = None
