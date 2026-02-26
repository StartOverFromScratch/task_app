from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.enums import CarryoverAction
from app.schemas.task import CarryoverCandidateResponse, TaskResponse
from app.services import carryover_service
from pydantic import BaseModel

router = APIRouter()


class CarryoverRequest(BaseModel):
    action: CarryoverAction


@router.get("/carryover-candidates", response_model=list[CarryoverCandidateResponse])
def list_carryover_candidates(db: Session = Depends(get_db)):
    rows = carryover_service.get_carryover_candidates(db)
    return [CarryoverCandidateResponse.model_validate(r) for r in rows]


@router.post("/{task_id}/carryover", response_model=TaskResponse)
def do_carryover(task_id: int, data: CarryoverRequest, db: Session = Depends(get_db)):
    return carryover_service.do_carryover(db, task_id, data.action)
