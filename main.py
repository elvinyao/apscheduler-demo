import logging
import sys
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import uvicorn
from core.bot_task_scheduler import BotTaskScheduler
from tasks.task_reader import TaskReader

logger = logging.getLogger(__name__)


# jobstores={
#     'default': MemoryJobStore()
# }

# scheduler = AsyncIOScheduler(jobstores=jobstores,timezone='Asia/Tokyo')

# @scheduler.scheduled_job('interval', seconds=10)
# def scheduled_job_1():
#     print("scheduled_job_1!")

# @scheduler.scheduled_job('date', run_date='2025-02-03 22:34:00')
# def scheduled_job_2():
#     print("scheduled_job_2!")

# @scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=22, minute=35)
# def scheduled_job_3():
#     print("scheduled_job_3!")


def main():
    """
    Main function to parse arguments, create the app, and run with uvicorn.
    """
    # Create a FastAPI app instance
    app = FastAPI()

    scheduler = BotTaskScheduler().create_scheduler(task_reader=TaskReader)

    @app.on_event("startup")
    async def startup_event():
        scheduler.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.shutdown()

    @app.get("/")
    async def read_root():
        return {"message": "Hello World"+str(scheduler.get_jobs())}
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception("An unexpected error occurred in main: %s", e)
        sys.exit(1)
