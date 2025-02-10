"""
app.py
The main entry point of the application.
"""
import time
from scheduler.database import SessionLocal
from scheduler.repository import TaskRepository
from scheduler.executor import TaskExecutor
from scheduler.service import SchedulerService

def main():
    # Create the repository and executor instances
    task_repo = TaskRepository(SessionLocal)
    task_executor = TaskExecutor(task_repo)
    
    # Seed the database with demo tasks (optional, for illustration)
    task_repo.seed_demo_data()

    # Initialize and start the scheduler service
    scheduler_service = SchedulerService(task_repo, task_executor)
    scheduler_service.start()

    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        # Gracefully shut down on exit
        scheduler_service.shutdown()

if __name__ == "__main__":
    main()
