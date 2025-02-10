"""
executor.py
Contains logic for executing different types of tasks.
"""

import time
from datetime import datetime

class TaskExecutor:
    """
    Contains the logic for executing tasks.
    """
    def __init__(self, task_repository):
        self.task_repository = task_repository

    def read_data(self):
        """
        Example function to read data from an external source (Confluence, REST API, etc.)
        and store it in the DB or process it as needed.
        """
        print(f"[{datetime.now()}] Running read_data()...")
        time.sleep(2)  # Simulate I/O or network call
        print("Data read from external source and stored in the DB.")

    def execute_task(self, task_id):
        """
        Fetch the task from DB, mark it RUNNING, simulate the work,
        then mark it DONE or FAILED.
        """
        self.task_repository.update_task_status(task_id, 'RUNNING')
        task = self.task_repository.get_task_by_id(task_id)
        if not task:
            print(f"Task with id={task_id} not found.")
            return

        print(f"[{datetime.now()}] Executing task: id={task.id}, name={task.name}, type={task.task_type}...")
        try:
            # Simulate workload
            time.sleep(3)
            self.task_repository.update_task_status(task_id, 'DONE')
            print(f"Task {task.id} completed successfully.")
        except Exception as e:
            self.task_repository.update_task_status(task_id, 'FAILED')
            print(f"Task {task.id} failed with error: {e}")
