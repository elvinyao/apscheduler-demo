from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
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
    RETRY = 'RETRY'  # New status for retry mechanism
    TIMEOUT = 'TIMEOUT'  # New status for timeout

class TaskPriority(str, Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    
class RetryPolicy(BaseModel):
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    current_retries: int = 0
    
class Task(BaseModel):
    id: int
    name: str
    task_type: TaskType
    cron_expr: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # New fields
    dependencies: List[int] = Field(default_factory=list)  # List of task IDs this task depends on
    timeout_seconds: Optional[int] = None  # Timeout in seconds, None means no timeout
    retry_policy: Optional[RetryPolicy] = None  # Retry configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Task-specific parameters
    
    def update_status(self, new_status: TaskStatus):
        self.status = new_status
        self.updated_at = datetime.now()
        
    def should_retry(self) -> bool:
        """Check if the task should be retried based on retry policy."""
        if not self.retry_policy:
            return False
            
        return self.retry_policy.current_retries < self.retry_policy.max_retries

    def increment_retry_counter(self):
        """Increment the retry counter."""
        if self.retry_policy:
            self.retry_policy.current_retries += 1
            
    def get_next_retry_time(self) -> datetime:
        """Calculate the next retry time based on retry policy."""
        if not self.retry_policy:
            return datetime.now()
            
        return datetime.now() + timedelta(seconds=self.retry_policy.retry_delay)