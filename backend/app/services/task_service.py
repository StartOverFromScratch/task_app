from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.capture_item import CaptureItem
from app.models.checklist_item import TaskChecklistItem
from app.models.completion_log import CompletionLog
from app.models.task import Task
from app.schemas.checklist_item import ChecklistItemCreate, ChecklistItemUpdate, ExtractRequest
from app.schemas.completion_log import CompleteRequest
from app.schemas.enums import Priority, TaskStatus, TaskType
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest

STALE_THRESHOLD = {Priority.must: 7, Priority.should: 21}


def _now() -> datetime:
    return datetime.utcnow()


def _task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return task


def _item_or_404(db: Session, task_id: int, item_id: int) -> TaskChecklistItem:
    item = db.get(TaskChecklistItem, item_id)
    if not item or item.task_id != task_id:
        raise HTTPException(status_code=404, detail="チェックリストアイテムが見つかりません")
    return item


# ── Task CRUD ──────────────────────────────────────────────────────────────


def get_tasks(
    db: Session,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> list[Task]:
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if task_type:
        q = q.filter(Task.task_type == task_type)
    if priority:
        q = q.filter(Task.priority == priority)
    if parent_id is not None:
        q = q.filter(Task.parent_id == parent_id)
    return q.order_by(Task.created_at.desc()).all()


def get_task_detail(db: Session, task_id: int) -> dict:
    task = _task_or_404(db, task_id)
    origin = None
    if task.origin_checklist_item_id:
        item = db.get(TaskChecklistItem, task.origin_checklist_item_id)
        if item:
            parent = db.get(Task, item.task_id)
            if parent:
                origin = {
                    "parent_task_id": parent.id,
                    "parent_task_title": parent.title,
                    "checklist_item_text": item.text,
                }
    return {"task": task, "origin": origin}


def create_task(db: Session, data: TaskCreateRequest) -> Task:
    if data.parent_id:
        _task_or_404(db, data.parent_id)
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdateRequest) -> Task:
    task = _task_or_404(db, task_id)
    updates = data.model_dump(exclude_unset=True)

    if updates.get("status") == TaskStatus.done:
        raise HTTPException(
            status_code=400,
            detail="完了処理は POST /tasks/{id}/complete から実行してください",
        )

    for key, value in updates.items():
        setattr(task, key, value)
    task.last_updated_at = _now()
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> None:
    task = _task_or_404(db, task_id)

    # 子タスクの parent_id を NULL に
    db.query(Task).filter(Task.parent_id == task_id).update(
        {"parent_id": None}, synchronize_session=False
    )
    # このタスクのチェックリストを origin とする他タスクの参照を NULL に
    item_ids = [i.id for i in db.query(TaskChecklistItem.id).filter(TaskChecklistItem.task_id == task_id)]
    if item_ids:
        db.query(Task).filter(Task.origin_checklist_item_id.in_(item_ids)).update(
            {"origin_checklist_item_id": None}, synchronize_session=False
        )
    # キャプチャの参照を NULL に
    db.query(CaptureItem).filter(CaptureItem.related_task_id == task_id).update(
        {"related_task_id": None}, synchronize_session=False
    )
    db.query(TaskChecklistItem).filter(TaskChecklistItem.task_id == task_id).delete(
        synchronize_session=False
    )
    db.query(CompletionLog).filter(CompletionLog.task_id == task_id).delete(
        synchronize_session=False
    )
    db.delete(task)
    db.commit()


# ── Children ───────────────────────────────────────────────────────────────


def get_children(db: Session, task_id: int) -> list[Task]:
    _task_or_404(db, task_id)
    return db.query(Task).filter(Task.parent_id == task_id).all()


def create_child(db: Session, task_id: int, data: TaskCreateRequest) -> Task:
    _task_or_404(db, task_id)
    d = data.model_dump()
    d["parent_id"] = task_id
    task = Task(**d)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ── Complete ───────────────────────────────────────────────────────────────


def complete_task(db: Session, task_id: int, data: CompleteRequest) -> CompletionLog:
    task = _task_or_404(db, task_id)

    # 未完了かつ切り出し済みでないアイテムがあれば 400
    blocking = [i for i in task.checklist if not i.is_done and i.extracted_task_id is None]
    if blocking:
        raise HTTPException(
            status_code=400,
            detail=f"未完了のチェックリストが {len(blocking)} 件あります",
        )

    task.status = TaskStatus.done
    task.last_updated_at = _now()

    log = CompletionLog(task_id=task_id, completed_at=_now(), note=data.note)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_completion_logs(db: Session, task_id: int) -> list[CompletionLog]:
    _task_or_404(db, task_id)
    return (
        db.query(CompletionLog)
        .filter(CompletionLog.task_id == task_id)
        .order_by(CompletionLog.completed_at.desc())
        .all()
    )


# ── Convergence ────────────────────────────────────────────────────────────


def get_convergence(db: Session, task_id: int) -> dict:
    task = _task_or_404(db, task_id)
    exploration_used = len(task.children)
    exploration_remaining = (
        task.exploration_limit - exploration_used
        if task.exploration_limit is not None
        else None
    )
    options_within_limit = (
        exploration_used <= task.exploration_limit
        if task.exploration_limit is not None
        else True
    )
    structure_simplified = exploration_used <= 3
    reversible_confirmed = task.reversible is True
    is_convergeable = options_within_limit and structure_simplified and reversible_confirmed

    return {
        "task_id": task_id,
        "exploration_limit": task.exploration_limit,
        "exploration_used": exploration_used,
        "exploration_remaining": exploration_remaining,
        "reversible": task.reversible,
        "decision_criteria": task.decision_criteria,
        "is_convergeable": is_convergeable,
        "convergence_checklist": {
            "options_within_limit": options_within_limit,
            "structure_simplified": structure_simplified,
            "reversible_confirmed": reversible_confirmed,
        },
    }


# ── Stale ──────────────────────────────────────────────────────────────────


def get_stale_tasks(db: Session, priority: Optional[str] = None) -> list[dict]:
    now = _now()
    active = [TaskStatus.todo, TaskStatus.doing, TaskStatus.needs_redefine]
    q = db.query(Task).filter(Task.status.in_(active))
    if priority:
        q = q.filter(Task.priority == priority)

    result = []
    for task in q.all():
        threshold = STALE_THRESHOLD.get(task.priority, 21)
        if task.last_updated_at:
            days = (now - task.last_updated_at).days
            if days >= threshold:
                row = {c.key: getattr(task, c.key) for c in task.__mapper__.column_attrs}
                row["stale_days"] = days
                row["threshold_days"] = threshold
                result.append(row)
    return result


# ── Checklist ──────────────────────────────────────────────────────────────


def get_checklist(db: Session, task_id: int) -> list[TaskChecklistItem]:
    _task_or_404(db, task_id)
    return (
        db.query(TaskChecklistItem)
        .filter(TaskChecklistItem.task_id == task_id)
        .order_by(TaskChecklistItem.order_no)
        .all()
    )


def create_checklist_item(db: Session, task_id: int, data: ChecklistItemCreate) -> TaskChecklistItem:
    _task_or_404(db, task_id)
    if data.order_no is None:
        max_order = (
            db.query(TaskChecklistItem)
            .filter(TaskChecklistItem.task_id == task_id)
            .count()
        )
        order_no = max_order + 1
    else:
        order_no = data.order_no

    item = TaskChecklistItem(task_id=task_id, text=data.text, order_no=order_no)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_checklist_item(
    db: Session, task_id: int, item_id: int, data: ChecklistItemUpdate
) -> TaskChecklistItem:
    item = _item_or_404(db, task_id, item_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def extract_checklist_item(
    db: Session, task_id: int, item_id: int, data: ExtractRequest
) -> dict:
    parent = _task_or_404(db, task_id)
    item = _item_or_404(db, task_id, item_id)

    if item.extracted_task_id:
        raise HTTPException(status_code=400, detail="このアイテムはすでに切り出し済みです")

    title = data.title or item.text
    done_criteria = data.done_criteria or title
    priority = data.priority or parent.priority

    new_task = Task(
        title=title,
        task_type=data.task_type,
        priority=priority,
        due_date=data.due_date,
        done_criteria=done_criteria,
        parent_id=task_id,
        status=TaskStatus.todo,
        origin_checklist_item_id=item_id,
    )
    db.add(new_task)
    db.flush()  # IDを確定

    item.extracted_task_id = new_task.id
    item.is_done = True

    db.commit()
    db.refresh(new_task)
    db.refresh(item)
    return {"extracted_task": new_task, "checklist_item": item}
