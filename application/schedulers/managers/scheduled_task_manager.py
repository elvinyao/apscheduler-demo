import logging
from uuid import UUID
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from domain.entities.models import TaskPriority, TaskStatus

class ScheduledTaskManager:
    """
    Manages scheduled tasks using APScheduler, handling the scheduling, 
    execution, and management of tasks with cron expressions.
    """
    def __init__(self, scheduler: BackgroundScheduler, task_repository):
        self.scheduler = scheduler
        self.task_repository = task_repository
    
    def schedule_task(self, task_id, cron_expr, priority=TaskPriority.MEDIUM, on_trigger_callback=None):
        """
        Schedule a task with the given cron expression.
        
        Args:
            task_id: ID of the task to schedule
            cron_expr: Cron expression for scheduling
            priority: Priority level for the task
            on_trigger_callback: Callback to execute when the task is triggered
        """
        job_id = f"task_{str(task_id)}"  # Convert UUID to string for job_id
        
        # Create the cron trigger
        cron_trigger = CronTrigger.from_crontab(cron_expr)
        
        # Add the job to the scheduler
        self.scheduler.add_job(
            func=on_trigger_callback,
            trigger=cron_trigger,
            args=[task_id, priority],
            id=job_id,
            replace_existing=True
        )
        
        # Update task status
        self.task_repository.update_task_status(task_id, TaskStatus.SCHEDULED)
        
        logging.info(f"Scheduled recurring job for task_id={task_id}, cron={cron_expr}, priority={priority}")
    
    def remove_scheduled_task(self, task_id):
        """Remove a scheduled task from the scheduler."""
        job_id = f"task_{str(task_id)}"
        try:
            self.scheduler.remove_job(job_id)
            logging.info(f"Removed scheduled job for task_id={task_id}")
            return True
        except Exception as e:
            logging.warning(f"Error removing scheduled job for task_id={task_id}: {e}")
            return False 