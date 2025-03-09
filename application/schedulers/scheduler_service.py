# scheduler/scheduler_service.py

import logging
import concurrent.futures
import time
from queue import PriorityQueue
from threading import Lock, Timer
from datetime import datetime, timedelta
from uuid import UUID
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from domain.entities.models import TaskStatus, TaskType, TaskPriority, Task, RetryPolicy

from ..use_cases.fetch_service import ExternalTaskFetcher
from typing import Dict, Set, Any, Optional

class SchedulerService:
    """
    Orchestrates APScheduler to schedule and run tasks with priority-based execution,
    retry support, timeout handling, and task dependencies.
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
        self.confluence_updater = confluence_updater
        self.fetcher = ExternalTaskFetcher(task_repository)

        self.poll_interval = poll_interval
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # Priority queue and execution tracking
        self.task_queue = PriorityQueue()
        self.running_tasks = set()
        self.queue_lock = Lock()
        
        # Thread pool for task execution
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_jobs,
            thread_name_prefix="TaskWorker"
        )
        
        # APScheduler for scheduling timed tasks
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
        
        # Task execution result tracking
        self.futures = {}
        
        # Timeout tracking
        self.timeout_timers = {}
        
        # Dependency tracking
        self.dependency_map = {}  # Maps task_id to set of tasks waiting on it
        self.waiting_on_dependencies = set()  # Set of task_ids waiting for dependencies

    def start(self):
        logging.info("Starting Scheduler Service with poll_interval=%s", self.poll_interval)
        
        # Initialize dependency map from existing tasks
        self._initialize_dependency_map()
        
        # 1) Poll for new tasks
        self.scheduler.add_job(
            func=self.poll_db_for_new_tasks,
            trigger='interval',
            seconds=self.poll_interval,
            id='poll_db_job',
            replace_existing=True
        )
        
        # 2) Update Confluence page
        self.scheduler.add_job(
            func=self.update_confl_page,
            trigger='interval',
            seconds=self.poll_interval,
            id='update_confl_job',
            replace_existing=True
        )

        # 3) Process task queue
        self.scheduler.add_job(
            func=self.process_task_queue,
            trigger='interval',
            seconds=1,  # Check queue every second
            id='process_queue_job',
            replace_existing=True
        )

        # 4) Read data task
        self.scheduler.add_job(
            func=self.task_executor.read_data,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='read_data_cron'
        )

        # 5) Fetch tasks from Confluence
        self.scheduler.add_job(
            func=self.fetcher.fetch_from_confluence,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='fetch_confluence_job'
        )
        
        # 6) Check and process retries
        self.scheduler.add_job(
            func=self.process_retries,
            trigger='interval',
            seconds=30,  # Check for retries every 30 seconds
            id='process_retries_job'
        )

        self.scheduler.start()
        logging.info("Scheduler started.")

    def _initialize_dependency_map(self):
        """Initialize dependency map from existing tasks."""
        all_tasks = self.task_repository.get_all()
        
        for task in all_tasks:
            if task.dependencies:
                # Add task to waiting set if it has dependencies
                self.waiting_on_dependencies.add(task.id)
                
                # Add task as a dependent for each of its dependencies
                for dep_id in task.dependencies:
                    if dep_id not in self.dependency_map:
                        self.dependency_map[dep_id] = set()
                    self.dependency_map[dep_id].add(task.id)

    def poll_db_for_new_tasks(self):
        """Poll for new tasks and add to queue, respecting dependencies."""
        logging.debug("Polling DB for new tasks.")
        pending_tasks = self.task_repository.get_pending_tasks()
        
        for task in pending_tasks:
            logging.info("Found pending task: %s", task)
            
            # Check if task has unmet dependencies
            has_unmet_dependencies = False
            if task.dependencies:
                for dep_id in task.dependencies:
                    dep_task = self.task_repository.get_by_id(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.DONE:
                        # Add to waiting list and skip for now
                        self.waiting_on_dependencies.add(task.id)
                        if dep_id not in self.dependency_map:
                            self.dependency_map[dep_id] = set()
                        self.dependency_map[dep_id].add(task.id)
                        has_unmet_dependencies = True
                        break
            
            if has_unmet_dependencies:
                continue
            
            # Process task depending on its type
            if task.task_type == TaskType.SCHEDULED and task.cron_expr:
                self.add_scheduled_job(task.id, task.cron_expr, task.priority)
                self.task_repository.update_task_status(task.id, TaskStatus.SCHEDULED)
            
            elif task.task_type == TaskType.IMMEDIATE:
                # Add to priority queue
                with self.queue_lock:
                    priority_value = self._get_priority_value(task.priority)
                    self.task_queue.put((priority_value, task.id))
                self.task_repository.update_task_status(task.id, TaskStatus.QUEUED)
                logging.info(f"Added immediate task {task.id} to queue with priority {task.priority}")

    def _get_priority_value(self, priority):
        """Convert task priority to numeric value, lower is higher priority."""
        if priority == TaskPriority.HIGH:
            return 0
        elif priority == TaskPriority.MEDIUM:
            return 50
        elif priority == TaskPriority.LOW:
            return 100
        else:
            return 50  # Default medium priority

    def process_task_queue(self):
        """Process task queue based on priorities and available slots."""
        with self.queue_lock:
            # Check available slots
            available_slots = self.max_concurrent_jobs - len(self.running_tasks)
            
            # If no slots or empty queue, return
            if available_slots <= 0 or self.task_queue.empty():
                return
                
            # Execute up to available_slots tasks
            for _ in range(available_slots):
                if self.task_queue.empty():
                    break
                    
                priority, task_id = self.task_queue.get()
                task = self.task_repository.get_by_id(task_id)
                
                if not task:
                    logging.warning(f"Task {task_id} not found in repository, skipping")
                    continue
                
                self.running_tasks.add(task_id)
                
                # Submit task to thread pool
                future = self.executor.submit(self._execute_and_track, task_id)
                self.futures[task_id] = future
                
                # Set up timeout if needed
                if task.timeout_seconds:
                    self._setup_task_timeout(task_id, task.timeout_seconds)
                
                # Set callback to clean up completed tasks
                future.add_done_callback(lambda f, tid=task_id: self._task_completed(tid))
                
                logging.info(f"Started execution of task {task_id} with priority value {priority}")

    def _setup_task_timeout(self, task_id: int, timeout_seconds: int):
        """Set up a timer to cancel the task if it exceeds the timeout."""
        timer = Timer(timeout_seconds, self._handle_task_timeout, args=[task_id])
        timer.daemon = True
        timer.start()
        self.timeout_timers[task_id] = timer

    def _handle_task_timeout(self, task_id: int):
        """Handle a task timeout by cancelling it and updating status."""
        with self.queue_lock:
            if task_id in self.futures and task_id in self.running_tasks:
                # Cancel the future if still running
                self.futures[task_id].cancel()
                
                # Update task status to TIMEOUT
                self.task_repository.update_task_status(task_id, TaskStatus.TIMEOUT)
                
                # Clean up
                if task_id in self.running_tasks:
                    self.running_tasks.remove(task_id)
                if task_id in self.futures:
                    del self.futures[task_id]
                    
                logging.warning(f"Task {task_id} timed out after configured timeout period")
                
                # Check if the task should be retried
                task = self.task_repository.get_by_id(task_id)
                if task and task.should_retry():
                    self._schedule_retry(task)

    def _execute_and_track(self, task_id):
        """Execute task and track status."""
        try:
            self.task_repository.update_task_status(task_id, TaskStatus.RUNNING)
            result = self.task_executor.execute_task(task_id)
            
            # Clean up timeout timer if it exists
            if task_id in self.timeout_timers:
                self.timeout_timers[task_id].cancel()
                del self.timeout_timers[task_id]
                
            return result
        except Exception as e:
            logging.error(f"Error executing task {task_id}: {e}")
            self.task_repository.update_task_status(task_id, TaskStatus.FAILED)
            
            # Check if task should be retried
            task = self.task_repository.get_by_id(task_id)
            if task and task.should_retry():
                self._schedule_retry(task)
                
            raise

    def _task_completed(self, task_id):
        """Clean up after task completion and check dependents."""
        with self.queue_lock:
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
            if task_id in self.futures:
                del self.futures[task_id]
                
            # Check if there are tasks waiting on this task
            self._process_dependent_tasks(task_id)
                
        logging.info(f"Task {task_id} completed and removed from tracking")

    def _process_dependent_tasks(self, completed_task_id):
        """Process tasks that were waiting on the completed task."""
        # Get completed task status
        completed_task = self.task_repository.get_by_id(completed_task_id)
        if not completed_task or completed_task.status != TaskStatus.DONE:
            # Only proceed with dependent tasks if this task completed successfully
            return
            
        if completed_task_id in self.dependency_map:
            dependent_task_ids = self.dependency_map[completed_task_id].copy()
            
            for dep_task_id in dependent_task_ids:
                # Check if all dependencies are satisfied
                dep_task = self.task_repository.get_by_id(dep_task_id)
                if not dep_task:
                    continue
                    
                all_deps_satisfied = True
                for parent_id in dep_task.dependencies:
                    parent_task = self.task_repository.get_by_id(parent_id)
                    if not parent_task or parent_task.status != TaskStatus.DONE:
                        all_deps_satisfied = False
                        break
                
                if all_deps_satisfied:
                    # Remove from waiting list
                    if dep_task_id in self.waiting_on_dependencies:
                        self.waiting_on_dependencies.remove(dep_task_id)
                    
                    # Remove from dependency map
                    for parent_id in dep_task.dependencies:
                        if parent_id in self.dependency_map and dep_task_id in self.dependency_map[parent_id]:
                            self.dependency_map[parent_id].remove(dep_task_id)
                    
                    # If the dependent task is still PENDING, add it to the queue
                    if dep_task.status == TaskStatus.PENDING:
                        if dep_task.task_type == TaskType.SCHEDULED and dep_task.cron_expr:
                            self.add_scheduled_job(dep_task.id, dep_task.cron_expr, dep_task.priority)
                            self.task_repository.update_task_status(dep_task.id, TaskStatus.SCHEDULED)
                        else:
                            # Add to queue
                            priority_value = self._get_priority_value(dep_task.priority)
                            self.task_queue.put((priority_value, dep_task.id))
                            self.task_repository.update_task_status(dep_task.id, TaskStatus.QUEUED)
                            logging.info(f"Dependency satisfied - added task {dep_task.id} to queue")

    def add_scheduled_job(self, task_id: UUID, cron_expr, priority=TaskPriority.MEDIUM):
        """Add a scheduled job with the given cron expression."""
        job_id = f"task_{str(task_id)}"  # Convert UUID to string for job_id
        priority_value = self._get_priority_value(priority)

        cron_trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(
            func=self._scheduled_task_wrapper,
            trigger=cron_trigger,
            args=[task_id, priority_value],
            id=job_id,
            replace_existing=True
        )
        logging.info(f"Scheduled recurring job for task_id={task_id}, cron={cron_expr}, priority={priority}")
        
    def _scheduled_task_wrapper(self, task_id, priority_value):
        """Wrapper for scheduled tasks to add them to the queue."""
        with self.queue_lock:
            self.task_queue.put((priority_value, task_id))
        self.task_repository.update_task_status(task_id, TaskStatus.QUEUED)
        logging.info(f"Scheduled task {task_id} triggered and added to queue with priority {priority_value}")

    def update_confl_page(self):
        """Update Confluence page with task results."""
        results = self.task_result_repo.get_all()
        if not results:
            logging.info("AggregatorJob: no new results to update.")
            return

        logging.info("AggregatorJob: found %d results, updating Confluence...", len(results))
        self.confluence_updater.update_confluence(results)
        self.task_result_repo.clear_results()
        logging.info("AggregatorJob: done updating Confluence and clearing results.")

    def _schedule_retry(self, task: Task):
        """Schedule a retry for the failed task."""
        if not task.retry_policy:
            return
            
        task.increment_retry_counter()
        next_retry_time = task.get_next_retry_time()
        
        # Update task status to RETRY
        self.task_repository.update_task_status(task.id, TaskStatus.RETRY)
        
        # Schedule the retry with a date trigger
        retry_job_id = f"retry_task_{task.id}_{task.retry_policy.current_retries}"
        self.scheduler.add_job(
            func=self._retry_task,
            trigger=DateTrigger(run_date=next_retry_time),
            args=[task.id],
            id=retry_job_id
        )
        
        logging.info(f"Scheduled retry {task.retry_policy.current_retries}/{task.retry_policy.max_retries} "
                    f"for task {task.id} at {next_retry_time}")

    def _retry_task(self, task_id: int):
        """Handle task retry by adding it back to the queue."""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            logging.warning(f"Retry task {task_id} not found")
            return
            
        # Reset task status to PENDING
        self.task_repository.update_task_status(task_id, TaskStatus.PENDING)
        
        # Add back to queue with original priority
        with self.queue_lock:
            priority_value = self._get_priority_value(task.priority)
            self.task_queue.put((priority_value, task_id))
            
        self.task_repository.update_task_status(task_id, TaskStatus.QUEUED)
        logging.info(f"Retrying task {task_id}, attempt {task.retry_policy.current_retries}")

    def process_retries(self):
        """Check for tasks that need to be retried."""
        # This is a placeholder - the actual retry scheduling happens in _schedule_retry
        # This method could be used for more complex retry logic if needed
        pass

    def shutdown(self):
        """Shutdown scheduler and executor."""
        logging.info("Shutting down Scheduler Service...")
        # Cancel all pending tasks
        for future in self.futures.values():
            future.cancel()
        
        # Cancel all timeout timers
        for timer in self.timeout_timers.values():
            timer.cancel()
        
        # Shutdown thread pool and scheduler
        self.executor.shutdown(wait=True)
        self.scheduler.shutdown()
        logging.info("Scheduler Service shutdown complete.")