"""
Repository implementation for Task entities.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from copy import deepcopy

from domain.exceptions import EntityNotFoundError
from domain.entities.repositories import BaseRepository
from domain.entities.models import Task, TaskStatus

class TaskRepository(BaseRepository[Task]):
    """
    Repository implementation for Task entities with persistence support.
    This is an in-memory implementation that saves snapshots to disk.
    """
    
    def __init__(self, persistence_manager=None):
        """
        Initialize the repository.
        
        Args:
            persistence_manager: Optional persistence manager to save state
        """
        self._tasks: List[Task] = []
        self._task_execute_history: List[Task] = []
        self.persistence_manager = persistence_manager
        
        # Try to recover tasks on initialization
        if self.persistence_manager:
            self._recover_tasks()
    
    def _recover_tasks(self):
        """Recover tasks from persistence storage on startup."""
        if not self.persistence_manager:
            return
            
        task_dicts = self.persistence_manager.load_tasks_snapshot()
        if not task_dicts:
            return
        
        for task_dict in task_dicts:
            # Skip tasks that are already DONE or FAILED
            if task_dict["status"] in (TaskStatus.DONE, TaskStatus.FAILED):
                history_task = Task(**task_dict)
                self._task_execute_history.append(history_task)
                continue
                
            # Tasks that were RUNNING when the app crashed should be reset to PENDING
            if task_dict["status"] == TaskStatus.RUNNING:
                task_dict["status"] = TaskStatus.PENDING
                
            # Add the task to the active task list
            task = Task(**task_dict)
            self._tasks.append(task)
    
    def persist_tasks(self):
        """Save current tasks to persistent storage."""
        if not self.persistence_manager:
            return
            
        # Combine active tasks and history for complete persistence
        all_tasks = self._tasks + self._task_execute_history
        self.persistence_manager.save_tasks_snapshot(all_tasks)

    def get_by_id(self, entity_id: UUID) -> Optional[Task]:
        """Get a task by its ID."""
        for task in self._tasks:
            if task.id == entity_id:
                return task
        raise EntityNotFoundError("Task", entity_id)

    def get_all(self) -> List[Task]:
        """Get all tasks."""
        return self._tasks.copy()

    def add(self, entity: Task) -> Task:
        """Add a new task."""
        self._tasks.append(entity)
        self.persist_tasks()
        return entity

    def update(self, entity: Task) -> Task:
        """Update an existing task."""
        for i, task in enumerate(self._tasks):
            if task.id == entity.id:
                entity.updated_at = datetime.now()
                entity.version += 1
                self._tasks[i] = entity
                
                # If status changes to DONE or FAILED, record to history
                if entity.status in (TaskStatus.DONE, TaskStatus.FAILED):
                    # Deep copy to history to prevent modification
                    self._task_execute_history.append(deepcopy(entity))
                
                self.persist_tasks()
                return entity
        
        raise EntityNotFoundError("Task", entity.id)

    def delete(self, entity_id: UUID) -> bool:
        """Delete a task by ID."""
        for i, task in enumerate(self._tasks):
            if task.id == entity_id:
                del self._tasks[i]
                self.persist_tasks()
                return True
        
        raise EntityNotFoundError("Task", entity_id)
    
    # Additional methods specific to TaskRepository
    
    def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with the specified status."""
        return [task for task in self._tasks if task.status == status]
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return self.get_by_status(TaskStatus.PENDING)
    
    def update_task_status(self, task_id: UUID, new_status: TaskStatus) -> Task:
        """Update the status of a task."""
        task = self.get_by_id(task_id)
        task.update_status(new_status)
        return self.update(task)
    
    def add_from_dict(self, task_data: Dict[str, Any]) -> Task:
        """Create and add a task from a dictionary."""        
        task = Task(**task_data)
        return self.add(task)
    
    def get_executed_tasks(self) -> List[Task]:
        """Get all executed tasks."""
        return self._task_execute_history.copy()