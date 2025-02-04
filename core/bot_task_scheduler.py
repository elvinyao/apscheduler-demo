# -*- coding: utf-8 -*-

"""
Create and configure a BackgroundScheduler with DB-based tasks.

1) read_tasks_job: every 'reading_interval' minutes => read tasks from Confluence, store in DB
2) check_and_run_job: every 1 min => fetch due tasks from DB, run in ThreadPool
"""

import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor

from core.db import add_or_update_tasks
# from tasks.task_executor import TaskExecutor
# from tasks.task_processor import TaskProcessor
from tasks.task_reader import TaskReader

# from core.env_store import ENVIRONMENTS_SERVICES

# from tasks.task_reader import TaskReader
# from tasks.task_processor import TaskProcessor
# from tasks.task_executor import TaskExecutor

# DB operations
# from core.db import add_or_update_tasks, fetch_due_tasks, mark_task_done

logger = logging.getLogger(__name__)


class BotTaskScheduler():
    """
    BotTaskScheduler defines the interface for task schedulers,
    managing task queues and multi-threaded task execution.
    """

    max_threads_count = 10
    read_tasks_job_interval = 2

    def __init__(self, max_threads_count: int = max_threads_count, read_tasks_job_interval: int = read_tasks_job_interval):
        """
        Init BotTaskScheduler with max_threads and interval.
        :param max_threads_count: Maximum number of threads to use for task execution.
        :param read_tasks_job_interval: Interval in seconds for the read_tasks_job.        
        """
        self.max_threads_count = max_threads_count
        self.read_tasks_job_interval = read_tasks_job_interval
        self.scheduler = BackgroundScheduler()
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_threads_count)

    def create_scheduler(self,
                         task_reader: TaskReader,
                         # task_processor: TaskProcessor,
                         # task_executor: TaskExecutor
                         ) -> BackgroundScheduler:
        """
        Create and configure a BackgroundScheduler with TaskReader to read tasks from source.Then use TaskProcessor
        to process tasks and TaskExecutor to execute tasks.

        TaskReader reads tasks from source (e.g. Confluence) and stores them in the database.
        TaskProcessor processes tasks and stores the results in the database.
        TaskExecutor executes tasks and sends notifications.

        """
        global thread_pool_executor

        scheduler = BackgroundScheduler()

        # Job execute first: read tasks using TaskReader
        scheduler.add_job(
            func=self.read_tasks_job,

            args=[task_reader],
            trigger="interval",
            minutes=self.read_tasks_job_interval

        )

        # Job 2: check tasks in DB
        # scheduler.add_job(
        #     check_and_run_job,
        #     "interval",
        #     minutes=1,
        #     args=[task_processor, task_executor]
        # )

        return scheduler

    def read_tasks_job(task_reader: TaskReader):
        """
        Periodic job that reads tasks from Confluence
        and stores (or updates) them in the DB.
        """
        logger.info("Running read_tasks_job...")
        page_i = 1

        # 1) read from Confluence
        new_tasks = task_reader.read_tasks_from_confluence(page_i)
        if not new_tasks:
            logger.info("No tasks read from Confluence this time.")
            return

        # 2) add or update them in the DB
        add_or_update_tasks(new_tasks)

        logger.info(
            "Successfully added/updated %d tasks in the DB.", len(new_tasks))

    # def check_and_run_job(task_processor: TaskProcessor, task_executor: TaskExecutor):
    #     """
    #     Periodic job that checks the DB for tasks whose schedule_time == now.
    #     Then processes them with a thread pool, updates their status in DB.
    #     """
    #     now_str = datetime.datetime.now().strftime("%H:%M")
    #     logger.info("check_and_run_job: Searching tasks due at %s", now_str)

    #     due_tasks = fetch_due_tasks(now_str)
    #     if not due_tasks:
    #         logger.info("No tasks due at this time.")
    #         return

    #     logger.info(
    #         "%d task(s) are due; scheduling them to run in threads...", len(due_tasks))
    #     for db_task in due_tasks:
    #         # submit each to thread pool
    #         thread_pool_executor.submit(
    #             run_task_flow, db_task, task_processor, task_executor)

    # def run_task_flow(db_task, task_processor: TaskProcessor, task_executor: TaskExecutor):
    #     """
    #     Orchestrates the entire flow for a single due task:
    #     1) parse payload from DB
    #     2) call task_processor.process_task
    #     3) call task_executor.execute_task_result
    #     4) mark the task as done or failed in DB
    #     """
    #     import json
    #     try:
    #         payload = json.loads(db_task.payload)
    #         env_name = payload.get("env", "A")  # default to A if not specified
    #         task_id = payload.get("task_id", f"db_id_{db_task.id}")

    #         # Retrieve the correct environment's services
    #         if env_name not in ENVIRONMENTS_SERVICES:
    #             raise ValueError(
    #                 f"Environment {env_name} is not loaded or invalid.")

    #         env_services = ENVIRONMENTS_SERVICES[env_name]
    #         task_processor = env_services["task_processor"]
    #         task_executor = env_services["task_executor"]

    #         logger.info("Running flow for task_id=%s in env=%s",
    #                     task_id, env_name)

    #         result = task_processor.process_task(payload)
    #         task_executor.execute_task_result(result)

    #         mark_task_done(task_id, "done")
    #     except Exception as e:
    #         logger.exception(
    #             "Error running task flow for db_task_id=%d: %s", db_task.id, e)
    #         mark_task_done(db_task.task_id, "failed")
