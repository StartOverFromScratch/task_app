from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CompleteRequest(BaseModel):
    note: Optional[str] = None


class CompletionLogResponse(BaseModel):
    id: int
    task_id: int
    completed_at: datetime
    note: Optional[str] = None

    model_config = {"from_attributes": True}
