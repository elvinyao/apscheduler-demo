"""
service.py
Manages APScheduler configuration and scheduling logic.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from .fetch_service import ExternalTaskFetcher

class SchedulerService:
    """
    Orchestrates APScheduler to schedule and run tasks.
    Periodically polls the database for new tasks.
    """
    def __init__(self, task_repository, task_executor):
        self.task_repository = task_repository
        self.task_executor = task_executor
        self.fetcher = ExternalTaskFetcher(task_repository)

        self.scheduler = BackgroundScheduler(
            executors={
                'default': ThreadPoolExecutor(max_workers=5),
            },
            job_defaults={
                'coalesce': False,
                'max_instances': 5,
            }
        )

    def start(self):
        """
        Start the scheduler and add initial jobs.
        """
        # 1) Poll DB for new tasks every 30 seconds
        self.scheduler.add_job(
            func=self.poll_db_for_new_tasks,
            trigger='interval',
            seconds=30,
            id='poll_db_job',
            replace_existing=True
        )

        # 2) Add a recurring job for read_data() every 5 minutes
        self.scheduler.add_job(
            func=self.task_executor.read_data,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='read_data_cron'
        )

        # 额外：每小时一次从Confluence拉取最新任务
        self.scheduler.add_job(
            func=self.fetcher.fetch_from_confluence,
            trigger=CronTrigger.from_crontab('* * * * *'),  # 每整点
            id='fetch_confluence_job'
        )

        # self.scheduler.add_job(
        #     func=self.fetcher.fetch_from_rest_api,
        #     trigger=CronTrigger.from_crontab('* * * * *'),  # 每整点
        #     id='fetch_confluence_job'
        # )

        self.scheduler.start()

    def poll_db_for_new_tasks(self):
        """
        Check the DB for PENDING tasks.
         - If scheduled + cron_expr -> schedule or update cron job
         - If immediate -> schedule once
        """
        pending_tasks = self.task_repository.get_pending_tasks()
        for t in pending_tasks:
            if t.task_type == 'scheduled' and t.cron_expr:
                self.add_scheduled_job(t.id, t.cron_expr)
                self.task_repository.update_task_status(t.id, 'SCHEDULED')
            elif t.task_type == 'immediate':
                self.add_immediate_job(t.id)
                self.task_repository.update_task_status(t.id, 'QUEUED')

    def add_scheduled_job(self, task_id, cron_expr):
        """
        Create or replace a cron-based job for the given task_id.
        """
        job_id = f"task_{task_id}"
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)

        cron_trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(
            func=self.task_executor.execute_task,
            trigger=cron_trigger,
            args=[task_id],
            id=job_id,
            replace_existing=True
        )
        print(f"Scheduled recurring job for task_id={task_id}, cron='{cron_expr}'.")

    def add_immediate_job(self, task_id):
        """
        Schedule a one-time job to run as soon as possible.
        """
        job_id = f"task_{task_id}_immediate"
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            func=self.task_executor.execute_task,
            trigger='date',
            args=[task_id],
            id=job_id
        )
        print(f"Scheduled immediate job for task_id={task_id}.")

    def shutdown(self):
        """
        Shuts down the scheduler (e.g., on application exit).
        """
        print("Shutting down scheduler...")
        self.scheduler.shutdown()
