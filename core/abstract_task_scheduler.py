from abc import ABC, abstractmethod
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler


class AbstractTaskScheduler(ABC):
    """
    AbstractTaskScheduler defines the interface for task schedulers,
    managing task queues and multi-threaded task execution.
    """

    @abstractmethod
    def create_scheduler(self, tasks: list, read_func, process_func, execute_func) -> BackgroundScheduler:
        """
        Create and configure a BackgroundScheduler with DB-based tasks.

        1) read_tasks_job: every 'reading_interval' minutes => read tasks from Confluence, store in DB
        2) check_and_run_job: every 1 min => fetch due tasks from DB, run in ThreadPool
        """
        pass

    @abstractmethod
    def schedule_tasks(self, tasks: list, read_func, process_func, execute_func) -> dict:
        """
        Schedule a batch of tasks and process them with the configured max thread count.
        Each task will first call process_func, then execute_func.

        :param tasks: List of tasks to process, each task is a dict with task_id and environment
        :param process_func: Task processing function that takes a single task and returns result
        :param execute_func: Task execution function that takes a single task and returns result
        :return: Dictionary containing all task processing and execution results
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        Start the task scheduler with configured interval and thread pool.

        :return: None
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        Stop the task scheduler and its thread pool gracefully.

        :return: None
        """
        pass

    @abstractmethod
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current status of the scheduler including thread pool metrics.

        :return: Dictionary containing scheduler status information
        """
        pass
