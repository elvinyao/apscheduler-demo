from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

# Task tags is been used to identify the task type
class TaskTags:
    JIRA_TASK_EXP = "JIRA_TASK_EXP"  # task export service type
    JIRA_TASK_IMPORT = "JIRA_TASK_IMPORT"  # task import service type
    BULK_JIRA_TASK = "BULK_JIRA_TASK"  # bulk jira task
class TaskScheduleType(str, Enum):
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
    retry_delay: int = 60  # Initial delay in seconds
    backoff_factor: float = 2.0  # Each retry increases the delay by this factor
    current_retries: int = 0
    
class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # Changed from int to UUID with auto-generation
    name: str
    task_type: TaskScheduleType
    cron_expr: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at_iso: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    owner: Optional[str] = None  # Username or ID of task creator
    version: int = 1  # Increment on each update
    
    # Update dependencies to use UUID instead of int
    dependencies: List[UUID] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_policy: Optional[RetryPolicy] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
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