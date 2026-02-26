from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.enums import CarryoverAction, TaskStatus
from app.services.task_service import _now, _task_or_404


def get_carryover_candidates(db: Session) -> list[dict]:
    today = date.today()
    active = [TaskStatus.todo, TaskStatus.doing]
    tasks = (
        db.query(Task)
        .filter(Task.status.in_(active), Task.due_date < today)
        .all()
    )
    result = []
    for task in tasks:
        row = {c.key: getattr(task, c.key) for c in task.__mapper__.column_attrs}
        row["overdue_days"] = (today - task.due_date).days
        result.append(row)
    return result


def do_carryover(db: Session, task_id: int, action: CarryoverAction) -> Task:
    task = _task_or_404(db, task_id)
    today = date.today()

    if action == CarryoverAction.today:
        task.due_date = today
        task.status = TaskStatus.todo
    elif action == CarryoverAction.plus_2d:
        base = task.due_date or today
        task.due_date = base + timedelta(days=2)
        task.status = TaskStatus.todo
    elif action == CarryoverAction.plus_7d:
        base = task.due_date or today
        task.due_date = base + timedelta(days=7)
        task.status = TaskStatus.todo
    elif action == CarryoverAction.needs_redefine:
        task.status = TaskStatus.needs_redefine

    task.last_updated_at = _now()
    db.commit()
    db.refresh(task)
    return task
