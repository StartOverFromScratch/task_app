from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class TaskChecklistItem(Base):
    __tablename__ = "task_checklist_items"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    text = Column(String, nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)
    order_no = Column(Integer, nullable=False)
    extracted_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    task = relationship("Task", back_populates="checklist", foreign_keys=[task_id])
