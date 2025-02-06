import logging
import sys
import time
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import uvicorn
from core.bot_task_scheduler import JobSchedulerManager
from tasks.task_reader import TaskReader

logger = logging.getLogger(__name__)
# 示例任务函数
def example_task(job_name):
    """示例任务函数，用于演示定时执行."""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Job '{job_name}' executed at {current_time} in thread: {threading.current_thread().name}")
    time.sleep(2) # 模拟任务执行时间

if __name__ == '__main__':
    import threading

    job_manager = JobSchedulerManager()
# (self, job_id, task_function, trigger_interval, trigger_args=None, job_kwargs=None)
    # 创建并添加多个定时 job
    job_manager.create_periodic_job(
        job_id='job_1',
        task_function=example_task,
        trigger_interval=5, # 每 5 秒执行一次
        job_kwargs={'job_name': 'Job 1'}
    )

    job_manager.create_periodic_job(
        job_id='job_2',
        task_function=example_task,
        trigger_interval=10, # 每 10 秒执行一次
        job_kwargs={'job_name': 'Job 2'}
    )

    job_manager.create_periodic_job(
        job_id='job_3',
        task_function=example_task,
        trigger_interval=3, # 每 3 秒执行一次
        trigger_args={'seconds': 3}, # 显式指定使用 seconds，尽管是默认的
        job_kwargs={'job_name': 'Job 3 - 短间隔'}
    )

    # 从内存中获取 job 信息
    job_1_info = job_manager.get_job_from_memory('job_1')
    if job_1_info:
        print("\nJob 'job_1' 的信息从内存中读取:")
        print(f"  Job ID: {job_1_info['job_id']}")
        print(f"  任务函数: {job_1_info['task_function'].__name__}")
        print(f"  触发间隔: {job_1_info['trigger_interval']} 秒")


    # 执行多线程 jobs (实际上是展示 scheduler 状态和内存 jobs 信息)
    print("\n--- 执行 execute_jobs_multithreaded 方法 ---")
    job_manager.execute_jobs_multithreaded()

    print("\n程序将继续运行，定时 jobs 将在后台自动执行...")
    time.sleep(30) # 让程序运行一段时间，观察定时任务的执行情况
    print("程序运行结束.")