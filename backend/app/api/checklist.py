from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.checklist_item import (
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    ExtractRequest,
)
from app.schemas.task import TaskResponse
from app.services import task_service

router = APIRouter()


@router.get("/{task_id}/checklist", response_model=list[ChecklistItemResponse])
def get_checklist(task_id: int, db: Session = Depends(get_db)):
    return task_service.get_checklist(db, task_id)


@router.post(
    "/{task_id}/checklist",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_checklist_item(task_id: int, data: ChecklistItemCreate, db: Session = Depends(get_db)):
    return task_service.create_checklist_item(db, task_id, data)


@router.patch("/{task_id}/checklist/{item_id}", response_model=ChecklistItemResponse)
def update_checklist_item(
    task_id: int, item_id: int, data: ChecklistItemUpdate, db: Session = Depends(get_db)
):
    return task_service.update_checklist_item(db, task_id, item_id, data)


@router.post(
    "/{task_id}/checklist/{item_id}/extract",
    status_code=status.HTTP_201_CREATED,
)
def extract_checklist_item(
    task_id: int, item_id: int, data: ExtractRequest, db: Session = Depends(get_db)
):
    result = task_service.extract_checklist_item(db, task_id, item_id, data)
    return {
        "extracted_task": TaskResponse.model_validate(result["extracted_task"]).model_dump(),
        "checklist_item": ChecklistItemResponse.model_validate(result["checklist_item"]).model_dump(),
    }
