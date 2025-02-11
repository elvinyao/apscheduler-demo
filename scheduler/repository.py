from datetime import datetime
from typing import List, Optional
from .models import Task

class TaskRepository:
    """
    Encapsulates all in-memory operations for Task.
    """
    def __init__(self):
        self._tasks: List[Task] = []
        self._id_counter = 1  # Simple counter for generating IDs

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self._tasks if task.status == 'PENDING']

    def update_task_status(self, task_id: int, new_status: str) -> None:
        task = self.get_task_by_id(task_id)
        if task:
            task.update_status(new_status)

    def add_task(self, task_data: dict) -> Task:
        task = Task(
            id=self._id_counter,
            **task_data
        )
        self._tasks.append(task)
        self._id_counter += 1
        return task

    def get_all_tasks(self) -> List[Task]:
        return self._tasks

    def seed_demo_data(self):
        """
        Populate with example tasks for demonstration.
        """
        if not self._tasks:  # Only seed if empty
            self.add_task({
                "name": "Scheduled DB Cleanup",
                "task_type": "scheduled",
                "cron_expr": "* * * * *",  # runs every minute for demo
                "status": "PENDING"
            })
            
            self.add_task({
                "name": "One-off Job",
                "task_type": "immediate",
                "status": "PENDING"
            })