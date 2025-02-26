from copy import deepcopy
from datetime import datetime
from typing import List, Optional
from .models import Task, TaskStatus, TaskType

class TaskRepository:
    """
    Encapsulates all in-memory operations for Task.
    """
    def __init__(self):
        self._tasks: List[Task] = []
        self._id_counter = 1  # Simple counter for generating IDs
        # [NEW] 用于记录已执行完毕的任务 (DONE或FAILED)
        self._task_execute_history: List[Task] = []

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self._tasks if task.status == 'PENDING']

    def update_task_status(self, task_id: int, new_status: TaskStatus) -> None:
        task = self.get_task_by_id(task_id)
        if task:
            task.update_status(new_status)
            # [NEW] 如果状态变更为DONE或FAILED，则记录到history
            if new_status in (TaskStatus.DONE, TaskStatus.FAILED):
                # 深拷贝一份存入history，防止后续被修改
                self._task_execute_history.append(deepcopy(task))

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
    
    # [NEW] 返回指定状态的任务列表
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        return [task for task in self._tasks if task.status == status]
    
    # [NEW] 返回所有已执行完成的任务历史 (DONE / FAILED)
    def get_all_executed_tasks(self) -> List[Task]:
        # 这就是 _task_execute_history
        return self._task_execute_history

    def seed_demo_data(self):
        """
        Populate with example tasks for demonstration.
        This version seeds 1000 scheduled tasks (same cron) + 500 immediate tasks.
        """
        if not self._tasks:  # Only seed if empty
            # 1) 1000 scheduled tasks
            for i in range(1, 1001):
                self.add_task({
                    "name": f"Scheduled Test {i}",
                    "task_type": TaskType.SCHEDULED,
                    "cron_expr": "* * * * *",  # 同一个cron: 每分钟触发
                    "status": TaskStatus.PENDING
                })

            # 2) 500 immediate tasks
            for j in range(1, 501):
                self.add_task({
                    "name": f"Immediate Task {j}",
                    "task_type": TaskType.IMMEDIATE,
                    "status": TaskStatus.PENDING
                })