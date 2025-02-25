# scheduler/service.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from scheduler.task_result_repo import ConfluenceUpdater, TaskResultRepository

from .fetch_service import ExternalTaskFetcher

class SchedulerService:
    """
    Orchestrates APScheduler to schedule and run tasks.
    Periodically polls the repository for new tasks.
    """
    def __init__(self, 
                 task_repository, 
                 task_executor,
                 task_result_repo,
                 confluence_updater,
                 poll_interval=30,
                 concurrency=5,
                 coalesce=False,
                 max_instances=5):
        self.task_repository = task_repository
        self.task_executor = task_executor
        self.task_result_repo = task_result_repo
        self.confluence_updater = confluence_updater
        self.fetcher = ExternalTaskFetcher(task_repository)

        self.poll_interval = poll_interval

        executors = {
            'default': ThreadPoolExecutor(max_workers=concurrency),
        }
        job_defaults = {
            'coalesce': coalesce,
            'max_instances': max_instances,
        }

        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )

    def start(self):
        logging.info("Starting APScheduler with poll_interval=%s", self.poll_interval)
        # 1) Poll DB for new tasks every self.poll_interval
        self.scheduler.add_job(
            func=self.poll_db_for_new_tasks,
            trigger='interval',
            seconds=self.poll_interval,
            id='poll_db_job',
            replace_existing=True
        )

        logging.info("Starting APScheduler with poll_interval=%s", self.poll_interval)
        # 1-2) AggregatorJob for confluence data update
        self.scheduler.add_job(
            func=self.update_confl_page,
            trigger='interval',
            seconds=self.poll_interval,
            id='update_confl_job',
            replace_existing=True
        )

        # 2) read_data job (every minute, for demo)
        self.scheduler.add_job(
            func=self.task_executor.read_data,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='read_data_cron'
        )

        # 3) fetch_from_confluence job (every minute, for demo)
        self.scheduler.add_job(
            func=self.fetcher.fetch_from_confluence,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='fetch_confluence_job'
        )

        self.scheduler.start()
        logging.info("Scheduler started.")

    def poll_db_for_new_tasks(self):
        logging.debug("Polling DB for new tasks.")
        pending_tasks = self.task_repository.get_pending_tasks()
        for t in pending_tasks:
            logging.info("Found pending task: %s", t)
            if t.task_type == 'scheduled' and t.cron_expr:
                self.add_scheduled_job(t.id, t.cron_expr)
                self.task_repository.update_task_status(t.id, 'SCHEDULED')
            elif t.task_type == 'immediate':
                self.add_immediate_job(t.id)
                self.task_repository.update_task_status(t.id, 'QUEUED')
    def update_confl_page(self):
        results = self.task_result_repo.get_all_results()
        if not results:
            logging.info("AggregatorJob: no new results to update.")
            return

        logging.info("AggregatorJob: found %d results, updating Confluence...", len(results))
        # 在此可做更多聚合、格式化
        self.confluence_updater.update_confluence(results)
        # 清空已处理的
        self.task_result_repo.clear_results()
        logging.info("AggregatorJob: done updating Confluence and clearing results.")

    def add_scheduled_job(self, task_id, cron_expr):
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
        logging.info("Scheduled recurring job for task_id=%s, cron=%s", task_id, cron_expr)

    def add_immediate_job(self, task_id):
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
        logging.info("Scheduled immediate job for task_id=%s", task_id)

    def shutdown(self):
        logging.info("Shutting down APScheduler...")
        self.scheduler.shutdown()
