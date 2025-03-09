# scheduler/managers/retry_manager.py

import logging
from typing import Callable, Dict
from uuid import UUID
from datetime import datetime

from domain.entities.models import Task, TaskStatus, RetryPolicy

class RetryManager:
    """Manages task retry policies and scheduling."""
    
    def __init__(self, task_repository):
        self.task_repository = task_repository
        self.retry_callbacks: Dict[UUID, Callable] = {}  # Callbacks for retry scheduling
    
    def register_retry_callback(self, task_id: UUID, callback: Callable) -> None:
        """Register a callback function for task retry."""
        self.retry_callbacks[task_id] = callback
    
    def should_retry(self, task: Task) -> bool:
        """Check if a task should be retried based on its retry policy."""
        if not task.retry_policy:
            return False
            
        return (task.retry_policy.current_retries < task.retry_policy.max_retries)
    
    def schedule_retry(self, task: Task) -> datetime:
        """
        Schedule a retry for the task.
        Returns the next retry time.
        """
        if not task.retry_policy:
            raise ValueError(f"Task {task.id} has no retry policy")
            
        task.increment_retry_counter()
        next_retry_time = task.get_next_retry_time()
        
        # Update task status to RETRY
        self.task_repository.update_task_status(task.id, TaskStatus.RETRY)
        
        # Call the registered callback if exists
        if task.id in self.retry_callbacks:
            self.retry_callbacks[task.id](task.id, next_retry_time)
        
        logging.info(f"Scheduled retry {task.retry_policy.current_retries}/{task.retry_policy.max_retries} "
                    f"for task {task.id} at {next_retry_time}")
        
        return next_retry_time
    
    def reset_retry_counter(self, task_id: UUID) -> None:
        """Reset retry counter for a task."""
        task = self.task_repository.get_by_id(task_id)
        if task and task.retry_policy:
            task.retry_policy.current_retries = 0
            self.task_repository.update(task)
    
    def cleanup_retry(self, task_id: UUID) -> None:
        """Clean up retry resources for a task."""
        if task_id in self.retry_callbacks:
            del self.retry_callbacks[task_id]