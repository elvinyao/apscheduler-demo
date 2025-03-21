# scheduler/scheduler_service.py

import logging
import concurrent.futures
from uuid import UUID
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from domain.entities.models import TaskStatus, TaskScheduleType, TaskPriority, Task

from .managers.task_queue_manager import TaskQueueManager
from .managers.dependency_manager import DependencyManager
from .managers.retry_manager import RetryManager
from .managers.timeout_manager import TimeoutManager
from .managers.scheduled_task_manager import ScheduledTaskManager
from ..use_cases.fetch_service import ExternalTaskFetcher
from ..services.result_reporting_service import ResultReportingService

class SchedulerService:
    """
    Orchestrates task scheduling and execution by coordinating various managers.
    Each manager is responsible for a specific aspect of task handling.
    """
    def __init__(self, 
                 task_repository, 
                 task_executor,
                 task_result_repo,
                 confluence_updater,
                 poll_interval=30,
                 max_concurrent_jobs=5,
                 coalesce=False,
                 max_instances=5):
        self.task_repository = task_repository
        self.task_executor = task_executor
        self.task_result_repo = task_result_repo
        self.fetcher = ExternalTaskFetcher(task_repository)

        self.poll_interval = poll_interval
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # Setup executor
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_jobs,
            thread_name_prefix="TaskWorker"
        )
        
        # APScheduler setup
        executors = {
            'default': APSThreadPoolExecutor(max_workers=max_concurrent_jobs),
        }
        job_defaults = {
            'coalesce': coalesce,
            'max_instances': max_instances,
        }

        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )
        
        # Initialize managers
        self.task_queue_manager = TaskQueueManager()
        self.dependency_manager = DependencyManager(task_repository)
        self.retry_manager = RetryManager(task_repository, self.scheduler)
        self.timeout_manager = TimeoutManager()
        self.scheduled_task_manager = ScheduledTaskManager(self.scheduler, task_repository)
        
        # Initialize result reporting service
        self.result_reporting_service = ResultReportingService(
            task_result_repo=task_result_repo,
            confluence_updater=confluence_updater,
            report_interval=poll_interval
        )
        
        # Tracking futures for task execution
        self.futures = {}

    def start(self):
        logging.info("Starting Scheduler Service with poll_interval=%s", self.poll_interval)
        
        # Initialize dependency map from existing tasks
        self.dependency_manager.initialize_from_existing_tasks()
        
        # 1) Poll for new tasks
        self.scheduler.add_job(
            func=self.poll_db_for_new_tasks,
            trigger='interval',
            seconds=self.poll_interval,
            id='poll_db_job',
            replace_existing=True
        )

        # 2) Process task queue
        self.scheduler.add_job(
            func=self.process_task_queue,
            trigger='interval',
            seconds=1,  # Check queue every second
            id='process_queue_job',
            replace_existing=True
        )

        # 3) Read data task
        self.scheduler.add_job(
            func=self.task_executor.read_data,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='read_data_cron'
        )

        # 4) Fetch tasks from Confluence
        self.scheduler.add_job(
            func=self.fetcher.fetch_from_confluence,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='fetch_confluence_job'
        )
        
        # 5) Check and process retries
        self.scheduler.add_job(
            func=self.retry_manager.process_retries,
            trigger='interval',
            seconds=30,  # Check for retries every 30 seconds
            id='process_retries_job'
        )
        
        # 6) Start the result reporting service with our scheduler
        self.result_reporting_service.start(scheduler=self.scheduler)

        self.scheduler.start()
        logging.info("Scheduler started.")

    def poll_db_for_new_tasks(self):
        """Poll for new tasks and add to queue, respecting dependencies."""
        logging.debug("Polling DB for new tasks.")
        pending_tasks = self.task_repository.get_pending_tasks()
        
        for task in pending_tasks:
            logging.info("Found pending task: %s", task)
            
            # Check if task has unmet dependencies
            has_unmet_dependencies = False
            if task.dependencies:
                has_unmet_dependencies = self.dependency_manager.register_task_dependencies(
                    task.id, task.dependencies
                )
            
            if has_unmet_dependencies:
                continue
            
            # Process task depending on its type
            if task.task_type == TaskScheduleType.SCHEDULED and task.cron_expr:
                self.scheduled_task_manager.schedule_task(
                    task.id, 
                    task.cron_expr, 
                    task.priority,
                    self._scheduled_task_wrapper
                )
            
            elif task.task_type == TaskScheduleType.IMMEDIATE:
                # Add to priority queue
                self.task_queue_manager.add_task(task.id, task.priority)
                self.task_repository.update_task_status(task.id, TaskStatus.QUEUED)
                logging.info(f"Added immediate task {task.id} to queue with priority {task.priority}")

    def process_task_queue(self):
        """Process task queue based on priorities and available slots."""
        tasks_to_execute = self.task_queue_manager.get_next_tasks(self.max_concurrent_jobs)
        
        for priority, task_id in tasks_to_execute:
            task = self.task_repository.get_by_id(task_id)
            
            if not task:
                logging.warning(f"Task {task_id} not found in repository, skipping")
                self.task_queue_manager.mark_task_completed(task_id)
                continue
            
            # Submit task to thread pool
            future = self.executor.submit(self._execute_and_track, task_id)
            self.futures[task_id] = future
            
            # Set up timeout if needed
            if task.timeout_seconds:
                self.timeout_manager.setup_timeout(
                    task_id, 
                    task.timeout_seconds, 
                    self._handle_task_timeout
                )
            
            # Set callback to clean up completed tasks
            future.add_done_callback(lambda f, tid=task_id: self._task_completed(tid))
            
            logging.info(f"Started execution of task {task_id} with priority value {priority}")

    def _handle_task_timeout(self, task_id):
        """Handle a task timeout by cancelling it and updating status."""
        if task_id in self.futures:
            # Cancel the future if still running
            self.futures[task_id].cancel()
            
            # Update task status to TIMEOUT
            self.task_repository.update_task_status(task_id, TaskStatus.TIMEOUT)
            
            # Clean up
            self.task_queue_manager.mark_task_completed(task_id)
            if task_id in self.futures:
                del self.futures[task_id]
                
            logging.warning(f"Task {task_id} timed out after configured timeout period")
            
            # Check if the task should be retried
            task = self.task_repository.get_by_id(task_id)
            if task and task.should_retry():
                self.retry_manager.schedule_retry(task, self._retry_task)

    def _execute_and_track(self, task_id):
        """Execute task and track status."""
        try:
            self.task_repository.update_task_status(task_id, TaskStatus.RUNNING)
            result = self.task_executor.execute_task(task_id)
            
            # Clean up timeout timer if it exists
            self.timeout_manager.cancel_timeout(task_id)
                
            return result
        except Exception as e:
            logging.error(f"Error executing task {task_id}: {e}")
            self.task_repository.update_task_status(task_id, TaskStatus.FAILED)
            
            # Check if task should be retried
            task = self.task_repository.get_by_id(task_id)
            if task and task.should_retry():
                self.retry_manager.schedule_retry(task, self._retry_task)
                
            raise

    def _task_completed(self, task_id):
        """Clean up after task completion and check dependents."""
        # Mark task as completed in the queue manager
        self.task_queue_manager.mark_task_completed(task_id)
        
        # Remove from futures
        if task_id in self.futures:
            del self.futures[task_id]
            
        # Process dependent tasks
        ready_tasks = self.dependency_manager.get_ready_dependent_tasks(task_id)
        for dep_task_id in ready_tasks:
            dep_task = self.task_repository.get_by_id(dep_task_id)
            if not dep_task:
                continue
                
            # Process the task based on its type
            if dep_task.task_type == TaskScheduleType.SCHEDULED and dep_task.cron_expr:
                self.scheduled_task_manager.schedule_task(
                    dep_task.id,
                    dep_task.cron_expr,
                    dep_task.priority,
                    self._scheduled_task_wrapper
                )
            else:
                # Add to queue
                self.task_queue_manager.add_task(dep_task.id, dep_task.priority)
                self.task_repository.update_task_status(dep_task.id, TaskStatus.QUEUED)
                logging.info(f"Dependency satisfied - added task {dep_task.id} to queue")
                
        logging.info(f"Task {task_id} completed and removed from tracking")

    def _scheduled_task_wrapper(self, task_id, priority):
        """Wrapper for scheduled tasks to add them to the queue."""
        self.task_queue_manager.add_task(task_id, priority)
        self.task_repository.update_task_status(task_id, TaskStatus.QUEUED)
        logging.info(f"Scheduled task {task_id} triggered and added to queue")

    def _retry_task(self, task_id):
        """Handle task retry by adding it back to the queue."""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            logging.warning(f"Retry task {task_id} not found")
            return
            
        # Reset task status to PENDING
        self.task_repository.update_task_status(task_id, TaskStatus.PENDING)
        
        # Add back to queue with original priority
        self.task_queue_manager.add_task(task_id, task.priority)
        self.task_repository.update_task_status(task_id, TaskStatus.QUEUED)
        logging.info(f"Retrying task {task_id}, attempt {task.retry_policy.current_retries}")

    def shutdown(self):
        """Shutdown scheduler and executor."""
        logging.info("Shutting down Scheduler Service...")
        
        # Cancel all pending tasks
        for future in self.futures.values():
            future.cancel()
        
        # Cancel all timeout timers
        self.timeout_manager.shutdown()
        
        # Shutdown result reporting service
        self.result_reporting_service.shutdown()
        
        # Shutdown thread pool and scheduler
        self.executor.shutdown(wait=True)
        self.scheduler.shutdown()
        logging.info("Scheduler Service shutdown complete.")