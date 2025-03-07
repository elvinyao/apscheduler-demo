# scheduler/service.py

import logging
import concurrent.futures
from queue import PriorityQueue
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from scheduler.models import TaskStatus, TaskType, TaskPriority
from scheduler.task_result_repo import ConfluenceUpdater, TaskResultRepository

from .fetch_service import ExternalTaskFetcher

class SchedulerService:
    """
    Orchestrates APScheduler to schedule and run tasks with priority-based execution.
    Periodically polls the repository for new tasks.
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
        
        # 任务优先级队列与执行状态跟踪
        self.task_queue = PriorityQueue()
        self.running_tasks = set()
        self.queue_lock = Lock()
        
        # 线程池用于任务执行
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_jobs,
            thread_name_prefix="TaskWorker"
        )
        
        # APScheduler用于调度定时任务
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
        
        # 任务执行结果跟踪
        self.futures = {}

    def start(self):
        logging.info("Starting Scheduler Service with poll_interval=%s", self.poll_interval)
        
        # 1) 轮询数据库获取新任务
        self.scheduler.add_job(
            func=self.poll_db_for_new_tasks,
            trigger='interval',
            seconds=self.poll_interval,
            id='poll_db_job',
            replace_existing=True
        )
        
        # 2) 更新Confluence页面
        self.scheduler.add_job(
            func=self.update_confl_page,
            trigger='interval',
            seconds=self.poll_interval,
            id='update_confl_job',
            replace_existing=True
        )

        # 3) 任务执行器 - 持续处理任务队列
        self.scheduler.add_job(
            func=self.process_task_queue,
            trigger='interval',
            seconds=1,  # 每秒检查一次队列
            id='process_queue_job',
            replace_existing=True
        )

        # 4) 读取数据任务
        self.scheduler.add_job(
            func=self.task_executor.read_data,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='read_data_cron'
        )

        # 5) 从Confluence获取任务
        self.scheduler.add_job(
            func=self.fetcher.fetch_from_confluence,
            trigger=CronTrigger.from_crontab('* * * * *'),
            id='fetch_confluence_job'
        )

        self.scheduler.start()
        logging.info("Scheduler started.")

    def poll_db_for_new_tasks(self):
        """轮询数据库获取新任务并加入队列"""
        logging.debug("Polling DB for new tasks.")
        pending_tasks = self.task_repository.get_pending_tasks()
        
        for task in pending_tasks:
            logging.info("Found pending task: %s", task)
            
            if task.task_type == TaskType.SCHEDULED and task.cron_expr:
                self.add_scheduled_job(task.id, task.cron_expr, task.priority)
                self.task_repository.update_task_status(task.id, TaskStatus.SCHEDULED)
            
            elif task.task_type == TaskType.IMMEDIATE:
                # 添加到优先级队列
                with self.queue_lock:
                    # 队列项格式: (优先级值, 任务ID)，值越小优先级越高
                    priority_value = self._get_priority_value(task.priority)
                    self.task_queue.put((priority_value, task.id))
                self.task_repository.update_task_status(task.id, TaskStatus.QUEUED)
                logging.info(f"Added immediate task {task.id} to queue with priority {task.priority}")

    def _get_priority_value(self, priority):
        """将任务优先级转换为数值，值越小优先级越高"""
        if priority == TaskPriority.HIGH:
            return 0
        elif priority == TaskPriority.MEDIUM:
            return 50
        elif priority == TaskPriority.LOW:
            return 100
        else:
            return 50  # 默认中等优先级

    def process_task_queue(self):
        """处理任务队列，根据可用资源和优先级执行任务"""
        with self.queue_lock:
            # 检查有多少个槽位可用
            available_slots = self.max_concurrent_jobs - len(self.running_tasks)
            
            # 如果没有可用槽位或队列为空，直接返回
            if available_slots <= 0 or self.task_queue.empty():
                return
                
            # 执行最多available_slots个任务
            for _ in range(available_slots):
                if self.task_queue.empty():
                    break
                    
                priority, task_id = self.task_queue.get()
                self.running_tasks.add(task_id)
                
                # 提交任务到线程池
                future = self.executor.submit(self._execute_and_track, task_id)
                self.futures[task_id] = future
                
                # 设置回调来清理已完成任务
                future.add_done_callback(lambda f, tid=task_id: self._task_completed(tid))
                
                logging.info(f"Started execution of task {task_id} with priority value {priority}")

    def _execute_and_track(self, task_id):
        """执行任务并跟踪状态"""
        try:
            self.task_repository.update_task_status(task_id, TaskStatus.RUNNING)
            result = self.task_executor.execute_task(task_id)
            return result
        except Exception as e:
            logging.error(f"Error executing task {task_id}: {e}")
            self.task_repository.update_task_status(task_id, TaskStatus.FAILED)
            raise

    def _task_completed(self, task_id):
        """任务完成后的清理工作"""
        with self.queue_lock:
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
            if task_id in self.futures:
                del self.futures[task_id]
        logging.info(f"Task {task_id} completed and removed from tracking")

    def add_scheduled_job(self, task_id, cron_expr, priority=TaskPriority.MEDIUM):
        """添加定时任务，优先级通过传入execute_task"""
        job_id = f"task_{task_id}"        
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
        """定时任务的包装器，将任务添加到优先级队列"""
        with self.queue_lock:
            self.task_queue.put((priority_value, task_id))
        self.task_repository.update_task_status(task_id, TaskStatus.QUEUED)
        logging.info(f"Scheduled task {task_id} triggered and added to queue with priority {priority_value}")

    def update_confl_page(self):
        """更新Confluence页面的任务"""
        results = self.task_result_repo.get_all_results()
        if not results:
            logging.info("AggregatorJob: no new results to update.")
            return

        logging.info("AggregatorJob: found %d results, updating Confluence...", len(results))
        self.confluence_updater.update_confluence(results)
        self.task_result_repo.clear_results()
        logging.info("AggregatorJob: done updating Confluence and clearing results.")

    def shutdown(self):
        """关闭调度器和任务执行器"""
        logging.info("Shutting down Scheduler Service...")
        # 取消所有待处理的任务
        for future in self.futures.values():
            future.cancel()
        
        # 关闭线程池和调度器
        self.executor.shutdown(wait=True)
        self.scheduler.shutdown()
        logging.info("Scheduler Service shutdown complete.")