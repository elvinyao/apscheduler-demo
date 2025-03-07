from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class TaskType(str, Enum):
    SCHEDULED = 'SCHEDULED'
    IMMEDIATE = 'IMMEDIATE'

class TaskStatus(str, Enum):
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    DONE = 'DONE'
    FAILED = 'FAILED'
    SCHEDULED = 'SCHEDULED'
    QUEUED = 'QUEUED'

class TaskPriority(str, Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    
class Task(BaseModel):
    id: int
    name: str
    task_type: TaskType  # e.g., 'scheduled' or 'immediate'
    cron_expr: Optional[str] = None   # e.g., "*/5 * * * *" for scheduled tasks
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.MEDIUM  # NEW: Task priority

    def update_status(self, new_status: TaskStatus):
        self.status = new_status
        self.updated_at = datetime.now()

class TaskOut(Task):
    pass