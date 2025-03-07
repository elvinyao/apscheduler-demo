from copy import deepcopy
from datetime import datetime
from typing import List, Optional

from .persistence import TaskPersistenceManager
from .models import Task, TaskStatus, TaskType

class TaskRepository:
    """
    Encapsulates all operations for Task management with persistence support.
    """
    def __init__(self, persistence_manager: Optional[TaskPersistenceManager] = None):
        self._tasks: List[Task] = []
        self._id_counter = 1  # Simple counter for generating IDs
        # Used to record executed tasks (DONE or FAILED)
        self._task_execute_history: List[Task] = []
        self.persistence_manager = persistence_manager or TaskPersistenceManager()
        
        # Try to recover tasks on initialization
        self._recover_tasks()
    
    def _recover_tasks(self):
        """Recover tasks from persistence storage on startup."""
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
            
            # Update the ID counter to be greater than any recovered task ID
            self._id_counter = max(self._id_counter, task.id + 1)
    
    def persist_tasks(self):
        """Save current tasks to persistent storage."""
        # Combine active tasks and history for complete persistence
        all_tasks = self._tasks + self._task_execute_history
        self.persistence_manager.save_tasks_snapshot(all_tasks)


    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self._tasks if task.status == TaskStatus.PENDING]

    def update_task_status(self, task_id: int, new_status: TaskStatus) -> None:
        task = self.get_task_by_id(task_id)
        if task:
            task.update_status(new_status)
            # If status changes to DONE or FAILED, record to history
            if new_status in (TaskStatus.DONE, TaskStatus.FAILED):
                # Deep copy to history to prevent modification
                self._task_execute_history.append(deepcopy(task))
            
            # Persist changes to storage
            self.persist_tasks()

    def add_task(self, task_data: dict) -> Task:
        task = Task(
            id=self._id_counter,
            **task_data
        )
        self._tasks.append(task)
        self._id_counter += 1
        
        # Persist changes to storage
        self.persist_tasks()
        return task

    def get_all_tasks(self) -> List[Task]:
        return self._tasks
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        return [task for task in self._tasks if task.status == status]
    
    def get_all_executed_tasks(self) -> List[Task]:
        return self._task_execute_history

    def seed_demo_data(self):
        """
        Populate with example tasks for demonstration.
        This version seeds 1000 scheduled tasks (same cron) + 500 immediate tasks.
        """
        if not self._tasks:  # Only seed if empty
            # 1) 10 scheduled tasks
            for i in range(1, 10):
                self.add_task({
                    "name": f"Scheduled Test {i}",
                    "task_type": TaskType.SCHEDULED,
                    "cron_expr": "* * * * *",  # 同一个cron: 每分钟触发
                    "status": TaskStatus.PENDING
                })

            # 2) 10 immediate tasks
            for j in range(1, 10):
                self.add_task({
                    "name": f"Immediate Task {j}",
                    "task_type": TaskType.IMMEDIATE,
                    "status": TaskStatus.PENDING
                })