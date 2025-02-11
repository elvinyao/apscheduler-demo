from pydantic import BaseModel
from typing import List
from scheduler.models import Task  # 已有的单个任务模型

class TaskListResponse(BaseModel):
    total_count: int
    data: List[Task]
