# fetch_service.py
import requests

from domain.entities.models import TaskStatus, TaskScheduleType
from infrastructure.repositories.task_repository import TaskRepository

class ExternalTaskFetcher:
    """
    用于从Confluence、REST API等外部系统获取任务数据并存储到DB的类。
    """
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository
    
    def fetch_from_confluence(self):
        """
        示例：调用Confluence的REST API (或者抓取页面表格) 并返回数据
        """
        # 假设我们通过Confluence的REST获取JSON
        # response = requests.get("https://confluence.example.com/rest/api/...")
        # data = response.json()
        # 这里用假数据演示
        data = [
            # {"name": "Confluence Task 1", "task_type": TaskType.IMMEDIATE, "cron_expr": None},
            # {"name": "Confluence Task 2", "task_type": TaskType.SCHEDULED, "cron_expr": "*/10 * * * *"}

        ]
        # 将这些数据写入数据库
        self._save_tasks(data)
    
    def fetch_from_rest_api(self, endpoint: str):
        """
        示例：调用其他系统的REST接口获取Task信息
        """
        # response = requests.get(endpoint)
        # data = response.json()
        data = [
            # {"name": "api Task 1", "task_type": TaskType.IMMEDIATE, "cron_expr": None},
            # {"name": "api Task 2", "task_type": TaskType.SCHEDULED, "cron_expr": "*/10 * * * *"},
        ]
        # 假设data是一个任务列表
        self._save_tasks(data)
    
    def _save_tasks(self, tasks_data: list[dict]):
        """
        负责把外部数据转换为Task对象并插入到内存Repository中
        (或其他自定义的存储).
        """
        for item in tasks_data:
            task_data = {
                "name": item["name"],
                "task_type": item.get("task_type"),
                "cron_expr": item.get("cron_expr"),
                "status": TaskStatus.PENDING
            }
            # 直接调用 in-memory repository 的 add_task
            self.task_repository.add_from_dict(task_data)

