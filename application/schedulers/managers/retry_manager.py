# scheduler/managers/retry_manager.py

import logging
from typing import Callable, Dict
from uuid import UUID
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from domain.entities.models import Task, TaskStatus, RetryPolicy

class RetryManager:
    """
    Manages the retry mechanism for failed tasks, handling retry policy,
    scheduling retries, and tracking retry attempts.
    """
    
    def __init__(self, task_repository, scheduler: BackgroundScheduler):
        self.task_repository = task_repository
        self.scheduler = scheduler
        self.retry_callbacks: Dict[UUID, Callable] = {}  # Callbacks for retry scheduling
    
    def register_retry_callback(self, task_id: UUID, callback: Callable) -> None:
        """Register a callback function for task retry."""
        self.retry_callbacks[task_id] = callback
    
    def should_retry(self, task: Task) -> bool:
        """Check if a task should be retried based on its retry policy."""
        if not task.retry_policy:
            return False
            
        return (task.retry_policy.current_retries < task.retry_policy.max_retries)
    
    def schedule_retry(self, task: Task, on_retry_callback):
        """
        Schedule a retry for the failed task based on its retry policy.
        
        Args:
            task: The task to retry
            on_retry_callback: Callback function to execute when a retry is triggered
        """
        if not task.retry_policy:
            logging.info(f"Task {task.id} has no retry policy, not scheduling retry")
            return
            
        task.increment_retry_counter()
        next_retry_time = task.get_next_retry_time()
        
        # Update task status to RETRY
        self.task_repository.update_task_status(task.id, TaskStatus.RETRY)
        
        # Schedule the retry with a date trigger
        retry_job_id = f"retry_task_{task.id}_{task.retry_policy.current_retries}"
        
        self.scheduler.add_job(
            func=on_retry_callback,
            trigger=DateTrigger(run_date=next_retry_time),
            args=[task.id],
            id=retry_job_id
        )
        
        logging.info(f"Scheduled retry {task.retry_policy.current_retries}/{task.retry_policy.max_retries} "
                    f"for task {task.id} at {next_retry_time}")
    
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
    
    def process_retries(self):
        """
        Process tasks that are due for retry.
        This method can be used for additional retry management logic.
        """
        # This is a placeholder that could be expanded with more complex retry logic
        # such as checking for stuck retries or implementing escalation policies
        retry_tasks = self.task_repository.get_by_status(TaskStatus.RETRY)
        if retry_tasks:
            logging.info(f"Found {len(retry_tasks)} tasks in RETRY status")
            # Additional logic could be added here