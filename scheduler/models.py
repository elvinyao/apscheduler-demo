from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4

class Task(BaseModel):
    id: int
    name: str
    task_type: str  # e.g., 'scheduled' or 'immediate'
    cron_expr: Optional[str] = None   # e.g., "*/5 * * * *" for scheduled tasks
    status: str = 'PENDING'  # e.g., 'PENDING', 'RUNNING', 'DONE', 'FAILED'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_status(self, new_status: str):
        self.status = new_status
        self.updated_at = datetime.now()

class TaskOut(Task):
    pass