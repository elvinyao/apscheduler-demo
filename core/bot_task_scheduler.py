from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import time

class JobSchedulerManager:
    def __init__(self):
        """
        初始化 JobSchedulerManager 类。
        配置 scheduler，包括 job store 和 executor。
        """
        self.scheduler = self._create_scheduler()
        self.jobs_in_memory = {}  # 用于存储job信息到内存中，key为job_id, value为job配置信息

    def _create_scheduler(self):
        """
        创建并配置 APScheduler 的后台调度器。
        配置 jobstore 为内存存储 MemoryJobStore。
        配置 executor 为线程池 ThreadPoolExecutor，用于多线程执行 job。
        """
        jobstores = {
            'default': MemoryJobStore()  # 使用内存作为 job 存储
        }
        executors = {
            'default': ThreadPoolExecutor(20)  # 使用线程池执行器，设置最大线程数为 20
        }
        scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
        scheduler.start() # 启动scheduler
        return scheduler

    def create_periodic_job(self, job_id, task_function, trigger_interval, trigger_args=None, job_kwargs=None):
        """
        创建并添加一个定时 job 到 scheduler，并将 job 信息存储到内存。

        Args:
            job_id (str): Job 的唯一标识符。
            task_function (callable): 要定时执行的任务函数。
            trigger_interval (int): 触发间隔，单位为秒。
            trigger_args (dict, optional): 触发器的参数，例如 seconds, minutes, hours 等，用于定义间隔。 默认为 None，将使用 seconds 作为默认间隔单位。
            job_kwargs (dict, optional): 传递给 job 函数的其他关键字参数。默认为 None。

        Returns:
            str: 添加到 scheduler 的 job 的 ID。
        """
        if trigger_args is None:
            trigger_args = {'seconds': trigger_interval} # 默认使用秒作为间隔

        if job_kwargs is None:
            job_kwargs = {}

        try:
            added_job = self.scheduler.add_job(
                task_function,
                'interval',
                id=job_id,
                args=trigger_args,
                kwargs=job_kwargs
            )
            self.jobs_in_memory[job_id] = { # 将job信息存储到内存
                'job_id': job_id,
                'task_function': task_function,
                'trigger_interval': trigger_interval,
                'trigger_args': trigger_args,
                'job_kwargs': job_kwargs,
                'next_run_time': added_job.next_run_time # 记录下次运行时间
            }
            return added_job.id
        except Exception as e:
            print(f"添加 job 失败，job_id: {job_id}, 错误信息: {e}")
            return None

    def get_job_from_memory(self, job_id):
        """
        从内存中读取 job 的配置信息。

        Args:
            job_id (str): 要获取的 job 的 ID。

        Returns:
            dict or None: job 的配置信息字典，如果 job_id 不存在则返回 None。
        """
        return self.jobs_in_memory.get(job_id)

    def execute_jobs_multithreaded(self):
        """
        此方法主要用于展示 scheduler 已经启动，并且 jobs 会被 scheduler 自动读取并多线程执行。
        实际上，scheduler 在创建时通过 ThreadPoolExecutor 已经配置为多线程执行。
        本方法可以用来查看当前内存中存储的 jobs 信息，以及 scheduler 的运行状态。
        """
        print("Scheduler 已经启动，并配置为多线程执行 jobs。")
        print("当前内存中存储的 jobs 信息:")
        for job_info in self.jobs_in_memory.values():
            print(f"  Job ID: {job_info['job_id']}")
            print(f"    任务函数: {job_info['task_function'].__name__}") # 打印函数名
            print(f"    触发间隔: {job_info['trigger_interval']} 秒")
            print(f"    下次运行时间: {job_info['next_run_time']}")
            print("-" * 30)

        print("\nScheduler 运行状态:")
        if self.scheduler.running:
            print("  Scheduler 正在运行")
        else:
            print("  Scheduler 未运行")

        running_jobs = self.scheduler.get_jobs() # 获取当前 scheduler 中正在运行的 jobs
        if running_jobs:
            print("\n当前 Scheduler 中运行的 jobs:")
            for job in running_jobs:
                print(f"  Job ID: {job.id}, 任务函数: {job.func.__name__}, 下次运行时间: {job.next_run_time}") # 打印 job 的信息
        else:
            print("\n当前 Scheduler 中没有运行的 jobs。")

