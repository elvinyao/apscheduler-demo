import sys
import uvicorn
import logging
from fastapi import FastAPI
from application.di_container import DIContainer
from infrastructure.config.config import setup_logging
from application.use_cases.executor import TaskExecutor
from interface_adapters.api.schemas import TaskListResponse
from application.schedulers.scheduler_service import SchedulerService
from domain.entities.models import TaskStatus, TaskScheduleType, TaskTags
from settings import get_settings
from examples.demo_tasks import get_demo_tasks


'''
code comment
'''
def create_app() -> FastAPI:
    # 1) Load global config
    s = get_settings()
    config = s.config_file
    # 2) Set up logging
    setup_logging(config.get("log", {}))

    app = FastAPI()

    # 3) Create dependency injection container
    di_container = DIContainer(s)

    # 4) Get repositories from DI container
    task_repo = di_container.get_task_repository()
    result_repo = di_container.get_task_result_repository()
    confluence_repo = di_container.get_confluence_repository()

    # Use repository add demo data
    for task in get_demo_tasks():
        task_repo.add_from_dict(task)

    # 5) Create task executor
    task_executor = TaskExecutor(task_repo, result_repo, di_container)

    # 6) Create scheduler
    sched_conf = config.get("scheduler", {})
    logging.info("Scheduler config loaded: %s", sched_conf)

    # Get result reporting service from DI container
    result_reporting_service = di_container.get_result_reporting_service()

    scheduler_service = SchedulerService(
        task_repository=task_repo,
        task_executor=task_executor,
        task_result_repo=result_repo,
        confluence_updater=confluence_repo,
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
        # No need to start the result_reporting_service separately as it's now handled by the scheduler service

    @app.on_event("shutdown")
    async def on_shutdown():
        logging.info("Shutting down scheduler.")
        scheduler_service.shutdown()

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks():
        tasks = task_repo.get_all()
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
        tasks = task_repo.get_by_status(status)
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
        tasks = task_repo.get_executed_tasks()
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
