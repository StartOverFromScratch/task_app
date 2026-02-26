from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class CaptureItem(Base):
    __tablename__ = "capture_items"

    id = Column(Integer, primary_key=True)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
