"""
executor.py
Contains logic for executing different types of tasks with multi-threading support.
"""

import logging
import time
import concurrent.futures
from datetime import datetime

from domain.jira_data_processor import JiraDataProcessor
from domain.mattermost_data_processor import MattermostDataProcessor
from domain.confluence_data_processor import ConfluenceDataProcessor
from scheduler.models import TaskStatus

class TaskExecutor:
    """
    Contains the logic for executing tasks with multi-threading support.
    """
    def __init__(self, task_repository, task_result_repo, max_task_threads=3):
        self.task_repository = task_repository
        self.task_result_repo = task_result_repo
        self.max_task_threads = max_task_threads

    def read_data(self):
        """
        Example function to read data from an external source (Confluence, REST API, etc.)
        and store it in the DB or process it as needed.
        """
        print(f"[{datetime.now()}] Running read_data()...")
        time.sleep(2)  # Simulate I/O or network call
        print("Sample Data read from external source.")

    def execute_task(self, task_id):
        """
        Execute a task with support for internal parallel processing.
        Returns a result dictionary that can be saved to task_result_repo.
        """
        # Mark the task as RUNNING
        self.task_repository.update_task_status(task_id, TaskStatus.RUNNING)
        task = self.task_repository.get_task_by_id(task_id)
        if not task:
            logging.warning(f"Task with id={task_id} not found.")
            return {"success": False, "error": "Task not found"}

        logging.info(f"[{datetime.now()}] Executing task: id={task.id}, name={task.name}, type={task.task_type}...")

        try:
            # 为这个特定任务创建线程池
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_task_threads, 
                                                     thread_name_prefix=f"Task{task_id}Worker") as task_executor:
                
                # ---------------------------
                # 1) 任务处理 (JIRA) - 这部分必须先执行
                # ---------------------------
                jira_processor = JiraDataProcessor()
                need_post_process = jira_processor.process_jira_ticket()

                # ---------------------------
                # 2) 如果需要后续处理，并行执行后续任务
                # ---------------------------
                if need_post_process:
                    logging.info("Comment indicates we need to proceed with post-processing...")
                    
                    # 并行提交两个后续任务
                    future_mattermost = task_executor.submit(self._process_mattermost)
                    future_confluence = task_executor.submit(self._process_confluence)
                    
                    # 等待两个任务完成
                    mattermost_result = future_mattermost.result()
                    confluence_result = future_confluence.result()
                    
                    logging.info(f"Parallel processing results - Mattermost: {mattermost_result}, Confluence: {confluence_result}")

            # 任务完成，标记为DONE
            self.task_repository.update_task_status(task_id, TaskStatus.DONE)
            logging.info(f"Task {task.id} completed successfully.")
            result = {"success": True}

        except Exception as e:
            # 如果发生异常, 标记FAILED
            self.task_repository.update_task_status(task_id, TaskStatus.FAILED)
            logging.error(f"Task {task.id} failed with error: {e}")
            result = {"success": False, "error": str(e)}
        
        finally:
            # 无论成功与否，保存结果
            taskDto = self.task_repository.get_task_by_id(task_id)
            result_item = {
                "task_id": task_id,
                "result_value": f"processed_{task_id}",
                "result_status_value": f"{taskDto}",
                "timestamp": time.time(),
                "execution_details": result
            }
            self.task_result_repo.save_task_result(result_item)
            logging.info(f"execute_task({task_id}) done, result saved.")
            
            return result

    def _process_mattermost(self):
        """处理Mattermost相关操作，作为可并行执行的子任务"""
        try:
            mattermost_processor = MattermostDataProcessor()
            result = mattermost_processor.send_notification()
            return {"mattermost_success": True, "details": result}
        except Exception as e:
            logging.error(f"Mattermost processing error: {e}")
            return {"mattermost_success": False, "error": str(e)}

    def _process_confluence(self):
        """处理Confluence相关操作，作为可并行执行的子任务"""
        try:
            confluence_processor = ConfluenceDataProcessor()
            result = confluence_processor.update_confluence_page()
            return {"confluence_success": True, "details": result}
        except Exception as e:
            logging.error(f"Confluence processing error: {e}")
            return {"confluence_success": False, "error": str(e)}