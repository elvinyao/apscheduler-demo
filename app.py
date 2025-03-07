# app.py

import sys
from fastapi import FastAPI
from typing import List
import uvicorn
import logging

# 新增导入
from core.di_container import DIContainer
from scheduler.task_result_repo import ConfluenceUpdater, TaskResultRepository
from scheduler.config import load_config, setup_logging

from scheduler.repository import TaskRepository
from scheduler.executor import TaskExecutor
from scheduler.schemas import TaskListResponse
from scheduler.scheduler_service import SchedulerService
from scheduler.models import TaskStatus

def create_app() -> FastAPI:
    # 1) Load global config
    config = load_config()  # Default from config.yaml
    # 2) Set up logging
    setup_logging(config.get("log", {}))

    app = FastAPI()

    # 3) Create dependency injection container
    di_container = DIContainer(config)
    
    # 4) Initialize repositories and services
    task_repo = TaskRepository()
    result_repo = TaskResultRepository()
    task_executor = TaskExecutor(task_repo, result_repo, di_container)
    
    # 5) Create ConfluenceUpdater
    conf_updater = ConfluenceUpdater()
    sched_conf = config.get("scheduler", {})
    logging.info("Scheduler config loaded: %s", sched_conf)
    scheduler_service = SchedulerService(
        task_repository=task_repo,
        task_executor=task_executor,
        task_result_repo=result_repo,
        confluence_updater=conf_updater,
        poll_interval=sched_conf.get("poll_interval", 30),
        max_concurrent_jobs=sched_conf.get("concurrency", 5),
        coalesce=sched_conf.get("coalesce", False),
        max_instances=sched_conf.get("max_instances", 5)
    )

    @app.on_event("startup")
    async def on_startup():
        # task_repo.seed_demo_data()  # optional
        # logging.info("Seeding demo data and starting scheduler.")
        scheduler_service.start()

    @app.on_event("shutdown")
    async def on_shutdown():
        logging.info("Shutting down scheduler.")
        scheduler_service.shutdown()

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks():
        tasks = task_repo.get_all_tasks()
        return TaskListResponse(
            total_count=len(tasks),
            data=tasks
        )

    

    # [NEW] 查询指定状态的tasks
    @app.get("/tasks/status/{status}", response_model=TaskListResponse)
    def list_tasks_by_status(status: TaskStatus):
        """
        Return tasks that match the given status.
        Possible statuses: PENDING, RUNNING, DONE, FAILED, SCHEDULED, QUEUED, ...
        """
        tasks=task_repo.get_tasks_by_status(status)
        return TaskListResponse(
            total_count=len(tasks),
            data=tasks
        )
    

    # [NEW] 查询已完成任务 (执行历史)
    @app.get("/task_history", response_model=TaskListResponse)
    def get_task_history():
        """
        Return the entire list of tasks that have ended up in DONE or FAILED.
        """
        tasks=task_repo.get_all_executed_tasks()
        return TaskListResponse(
            total_count=len(tasks),
            data=tasks
        )

    return app

def main():
    """
    Main function to parse arguments, create the app, and run with uvicorn.
    """
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
