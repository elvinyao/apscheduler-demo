# scheduler/managers/task_queue_manager.py

import logging
from queue import PriorityQueue
from threading import Lock
from typing import Optional, Tuple, Set, Dict, Any
from uuid import UUID

from domain.entities.models import TaskPriority, TaskStatus

class TaskQueueManager:
    """Manages the priority-based task queue and running tasks tracking."""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.task_queue = PriorityQueue()
        self.running_tasks: Set[UUID] = set()
        self.queue_lock = Lock()
        self.futures: Dict[UUID, Any] = {}  # Store futures for running tasks
        
    def get_priority_value(self, priority: TaskPriority) -> int:
        """Convert task priority to numeric value, lower is higher priority."""
        if priority == TaskPriority.HIGH:
            return 0
        elif priority == TaskPriority.MEDIUM:
            return 50
        elif priority == TaskPriority.LOW:
            return 100
        else:
            return 50  # Default medium priority
    
    def add_task(self, task_id: UUID, priority: TaskPriority) -> None:
        """Add a task to the queue with the specified priority."""
        with self.queue_lock:
            priority_value = self.get_priority_value(priority)
            self.task_queue.put((priority_value, task_id))
            logging.info(f"Added task {task_id} to queue with priority {priority}")
    
    def get_next_task(self) -> Optional[Tuple[int, UUID]]:
        """Get the next task from the queue, or None if queue is empty."""
        with self.queue_lock:
            if self.task_queue.empty():
                return None
            return self.task_queue.get()
    
    def mark_task_running(self, task_id: UUID, future: Any) -> None:
        """Mark a task as running and store its future."""
        with self.queue_lock:
            self.running_tasks.add(task_id)
            self.futures[task_id] = future
    
    def mark_task_completed(self, task_id: UUID) -> None:
        """Mark a task as completed and remove from tracking."""
        with self.queue_lock:
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
            if task_id in self.futures:
                del self.futures[task_id]
    
    def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a running task. Returns True if task was cancelled."""
        with self.queue_lock:
            if task_id in self.futures and task_id in self.running_tasks:
                self.futures[task_id].cancel()
                self.mark_task_completed(task_id)
                return True
            return False
    
    def get_available_slots(self) -> int:
        """Return the number of available execution slots."""
        with self.queue_lock:
            return self.max_concurrent_jobs - len(self.running_tasks)
    
    def is_queue_empty(self) -> bool:
        """Check if the task queue is empty."""
        with self.queue_lock:
            return self.task_queue.empty()