import sys
from fastapi import FastAPI
from typing import List
import uvicorn

from scheduler.database import SessionLocal
from scheduler.repository import TaskRepository
from scheduler.executor import TaskExecutor
from scheduler.service import SchedulerService
from scheduler.models import Task, TaskOut

def create_app() -> FastAPI:
    app = FastAPI()

    task_repo = TaskRepository(SessionLocal)
    task_executor = TaskExecutor(task_repo)
    scheduler_service = SchedulerService(task_repo, task_executor)

    @app.on_event("startup")
    async def on_startup():
        task_repo.seed_demo_data()  # optional
        scheduler_service.start()

    @app.on_event("shutdown")
    async def on_shutdown():
        scheduler_service.shutdown()

    @app.get("/tasks", response_model=List[TaskOut])
    def list_tasks():
        with SessionLocal() as session:
            tasks = session.query(Task).all()
            return tasks
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
        sys.exit(1)