from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.completion_log import CompleteRequest, CompletionLogResponse
from app.schemas.enums import Priority, TaskStatus, TaskType
from app.schemas.task import (
    CarryoverCandidateResponse,
    ConvergenceResponse,
    StaleTaskResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services import task_service

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    priority: Optional[Priority] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return task_service.get_tasks(db, status=status, task_type=task_type, priority=priority, parent_id=parent_id)


# /stale は /{task_id} より先に定義する必要がある
@router.get("/stale", response_model=list[StaleTaskResponse])
def list_stale_tasks(
    priority: Optional[Priority] = None,
    db: Session = Depends(get_db),
):
    rows = task_service.get_stale_tasks(db, priority=priority)
    return [StaleTaskResponse.model_validate(r) for r in rows]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreateRequest, db: Session = Depends(get_db)):
    return task_service.create_task(db, data)


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    result = task_service.get_task_detail(db, task_id)
    task = result["task"]
    origin = result["origin"]
    return TaskDetailResponse(
        **TaskResponse.model_validate(task).model_dump(),
        children=task.children,
        checklist=task.checklist,
        origin=origin,
    )


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdateRequest, db: Session = Depends(get_db)):
    return task_service.update_task(db, task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task_service.delete_task(db, task_id)


@router.get("/{task_id}/children", response_model=list[TaskResponse])
def list_children(task_id: int, db: Session = Depends(get_db)):
    return task_service.get_children(db, task_id)


@router.post(
    "/{task_id}/children",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_child(task_id: int, data: TaskCreateRequest, db: Session = Depends(get_db)):
    return task_service.create_child(db, task_id, data)


@router.post(
    "/{task_id}/complete",
    response_model=CompletionLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def complete_task(task_id: int, data: CompleteRequest, db: Session = Depends(get_db)):
    return task_service.complete_task(db, task_id, data)


@router.get("/{task_id}/completion-log", response_model=list[CompletionLogResponse])
def get_completion_log(task_id: int, db: Session = Depends(get_db)):
    return task_service.get_completion_logs(db, task_id)


@router.get("/{task_id}/convergence", response_model=ConvergenceResponse)
def get_convergence(task_id: int, db: Session = Depends(get_db)):
    return task_service.get_convergence(db, task_id)
