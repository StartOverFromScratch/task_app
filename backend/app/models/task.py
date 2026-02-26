from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    task_type = Column(String, nullable=False)  # research | decision | execution
    category = Column(String, nullable=True)
    priority = Column(String, nullable=False)   # must | should
    status = Column(String, nullable=False, default="todo")
    due_date = Column(Date, nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    done_criteria = Column(String, nullable=False)
    decision_criteria = Column(String, nullable=True)
    reversible = Column(Boolean, nullable=True)
    exploration_limit = Column(Integer, nullable=True)
    origin_checklist_item_id = Column(
        Integer, ForeignKey("task_checklist_items.id", ondelete="SET NULL"), nullable=True
    )
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    children = relationship(
        "Task",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    parent = relationship(
        "Task",
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side=[id],
    )
    checklist = relationship(
        "TaskChecklistItem",
        back_populates="task",
        foreign_keys="TaskChecklistItem.task_id",
        order_by="TaskChecklistItem.order_no",
    )
    completion_logs = relationship("CompletionLog", back_populates="task")
