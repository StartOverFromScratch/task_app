from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.checklist_item import ChecklistItemResponse
from app.schemas.enums import Priority, TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    title: str
    task_type: TaskType
    category: Optional[str] = None
    priority: Priority
    due_date: Optional[date] = None
    parent_id: Optional[int] = None
    done_criteria: str
    decision_criteria: Optional[str] = None
    reversible: Optional[bool] = None
    exploration_limit: Optional[int] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    task_type: Optional[TaskType] = None
    category: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None
    done_criteria: Optional[str] = None
    decision_criteria: Optional[str] = None
    reversible: Optional[bool] = None
    exploration_limit: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    task_type: TaskType
    category: Optional[str] = None
    priority: Priority
    status: TaskStatus
    due_date: Optional[date] = None
    parent_id: Optional[int] = None
    done_criteria: str
    decision_criteria: Optional[str] = None
    reversible: Optional[bool] = None
    exploration_limit: Optional[int] = None
    origin_checklist_item_id: Optional[int] = None
    last_updated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class OriginInfo(BaseModel):
    parent_task_id: int
    parent_task_title: str
    checklist_item_text: str


class TaskDetailResponse(TaskResponse):
    children: list[TaskResponse] = []
    checklist: list[ChecklistItemResponse] = []
    origin: Optional[OriginInfo] = None


class StaleTaskResponse(TaskResponse):
    stale_days: int
    threshold_days: int


class CarryoverCandidateResponse(TaskResponse):
    overdue_days: int


class ConvergenceChecklist(BaseModel):
    options_within_limit: bool
    structure_simplified: bool
    reversible_confirmed: bool


class ConvergenceResponse(BaseModel):
    task_id: int
    exploration_limit: Optional[int] = None
    exploration_used: int
    exploration_remaining: Optional[int] = None
    reversible: Optional[bool] = None
    decision_criteria: Optional[str] = None
    is_convergeable: bool
    convergence_checklist: ConvergenceChecklist
