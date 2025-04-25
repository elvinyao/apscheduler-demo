# scheduler/managers/task_queue_manager.py

import logging
from queue import PriorityQueue
from threading import Lock
from typing import Optional, Tuple, Set, Dict, Any
from uuid import UUID

from domain.entities.models import TaskPriority, TaskStatus

class TaskQueueManager:
    """
    Manages a priority queue for tasks, providing thread-safe operations
    for adding, retrieving, and manipulating tasks in the queue.
    """
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.queue_lock = Lock()
        self.running_tasks = set()
        self.futures: Dict[UUID, Any] = {}  # Store futures for running tasks
    
    def add_task(self, task_id, priority):
        """Add a task to the priority queue with the given priority."""
        with self.queue_lock:
            priority_value = self.get_priority_value(priority)
            self.task_queue.put((priority_value, task_id))
            logging.info(f"Added task {task_id} to queue with priority {priority}")
    
    def get_next_tasks(self, max_tasks):
        """Get up to max_tasks from the queue if slots are available."""
        tasks_to_execute = []
        
        with self.queue_lock:
            # Check available slots
            available_slots = max_tasks - len(self.running_tasks)
            
            # If no slots or empty queue, return empty list
            if available_slots <= 0 or self.task_queue.empty():
                return tasks_to_execute
                
            # Get up to available_slots tasks
            for _ in range(available_slots):
                if self.task_queue.empty():
                    break
                    
                priority, task_id = self.task_queue.get()
                self.running_tasks.add(task_id)
                tasks_to_execute.append((priority, task_id))
                
        return tasks_to_execute
    
    def mark_task_completed(self, task_id):
        """Mark a task as completed and remove it from running tasks."""
        with self.queue_lock:
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
            if task_id in self.futures:
                del self.futures[task_id]
    
    def is_queue_empty(self):
        """Check if the task queue is empty."""
        with self.queue_lock:
            return self.task_queue.empty()
    
    def get_priority_value(self, priority):
        """Convert task priority to numeric value, lower is higher priority."""
        if priority == TaskPriority.HIGH:
            return 0
        elif priority == TaskPriority.MEDIUM:
            return 50
        elif priority == TaskPriority.LOW:
            return 100
        else:
            return 50  # Default medium priority