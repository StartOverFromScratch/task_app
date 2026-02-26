from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CompletionLog(Base):
    __tablename__ = "completion_logs"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    completed_at = Column(DateTime, server_default=func.now(), nullable=False)
    note = Column(String, nullable=True)

    task = relationship("Task", back_populates="completion_logs")
