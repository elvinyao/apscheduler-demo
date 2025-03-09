# scheduler/managers/scheduler_manager.py

import logging
from typing import Dict, Callable, Any, Optional
from uuid import UUID
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from domain.entities.models import TaskPriority

class SchedulerManager:
    """Manages APScheduler for task scheduling."""
    
    def __init__(self, max_workers: int = 5, coalesce: bool = False, max_instances: int = 5):
        # APScheduler setup
        executors = {
            'default': APSThreadPoolExecutor(max_workers=max_workers),
        }
        job_defaults = {
            'coalesce': coalesce,
            'max_instances': max_instances,
        }

        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )
        
        # Job tracking
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logging.info("Scheduler started.")
    
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logging.info("Scheduler shutdown.")
    
    def add_cron_job(self, job_id: str, func: Callable, cron_expr: str, 
                     args: list = None, kwargs: dict = None, replace_existing: bool = True) -> str:
        """
        Add a job with a cron trigger.
        
        Returns:
            str: The job ID
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        job = self.scheduler.add_job(
            func=func,
            trigger=CronTrigger.from_crontab(cron_expr),
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=replace_existing
        )
        
        self.jobs[job_id] = {
            'type': 'cron',
            'expression': cron_expr,
            'job': job
        }
        
        logging.info(f"Added cron job {job_id} with expression {cron_expr}")
        return job_id
    
    def add_interval_job(self, job_id: str, func: Callable, seconds: int, 
                         args: list = None, kwargs: dict = None, replace_existing: bool = True) -> str:
        """
        Add a job with an interval trigger.
        
        Returns:
            str: The job ID
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        job = self.scheduler.add_job(
            func=func,
            trigger='interval',
            seconds=seconds,
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=replace_existing
        )
        
        self.jobs[job_id] = {
            'type': 'interval',
            'seconds': seconds,
            'job': job
        }
        
        logging.info(f"Added interval job {job_id} with seconds={seconds}")
        return job_id
    
    def add_date_job(self, job_id: str, func: Callable, run_date: datetime, 
                     args: list = None, kwargs: dict = None, replace_existing: bool = True) -> str:
        """
        Add a job with a date trigger (one-time execution).
        
        Returns:
            str: The job ID
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        job = self.scheduler.add_job(
            func=func,
            trigger=DateTrigger(run_date=run_date),
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=replace_existing
        )
        
        self.jobs[job_id] = {
            'type': 'date',
            'run_date': run_date,
            'job': job
        }
        
        logging.info(f"Added date job {job_id} to run at {run_date}")
        return job_id
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Returns:
            bool: True if job was removed, False otherwise
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logging.info(f"Removed job {job_id}")
            return True
        except Exception as e:
            logging.error(f"Error removing job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a job.
        
        Returns:
            bool: True if job was paused, False otherwise
        """
        try:
            self.scheduler.pause_job(job_id)
            logging.info(f"Paused job {job_id}")
            return True
        except Exception as e:
            logging.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.
        
        Returns:
            bool: True if job was resumed, False otherwise
        """
        try:
            self.scheduler.resume_job(job_id)
            logging.info(f"Resumed job {job_id}")
            return True
        except Exception as e:
            logging.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a job."""
        if job_id in self.jobs:
            return self.jobs[job_id]
        return None