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
from scheduler.models import TaskStatus, TaskType

class TaskExecutor:
    """
    Contains the logic for executing tasks with multi-threading support.
    """
    def __init__(self, task_repository, task_result_repo, di_container, max_task_threads=3):
        self.task_repository = task_repository
        self.task_result_repo = task_result_repo
        self.di_container = di_container
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
                        # 检查任务标签，处理JIRA_TASK_EXP标签
            if "JIRA_TASK_EXP" in task.tags:
                jira_processor = self.di_container.get_jira_data_processor()
                
                # 构造任务参数
                jira_task_params = {
                    "jira_envs": task.parameters.get('jira_envs', []),
                    "key_type": task.parameters.get('key_type'),  # "root_ticket" 或 "project"
                    "key_value": task.parameters.get('key_value'),
                    "user": task.parameters.get('user'),
                    "is_scheduled": task.task_type == TaskType.SCHEDULED
                }
                
                # 调用处理方法
                result = jira_processor.process_jira_task_exp(jira_task_params)
                logging.info(f"JIRA_TASK_EXP processing result: {result}")
                
                # 任务完成，标记为DONE
                self.task_repository.update_task_status(task_id, TaskStatus.DONE)
                logging.info(f"Task {task.id} completed successfully.")
                return result
            # For this specific task create a thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_task_threads, 
                                                     thread_name_prefix=f"Task{task_id}Worker") as task_executor:
                
                # ---------------------------
                # 1) Task processing (JIRA) - this part must execute first
                # ---------------------------
                jira_processor = self.di_container.get_jira_data_processor()
                need_post_process = jira_processor.check_and_process_tickets(
                    jql=task.parameters.get('jql', 'project = TEST')
                )

                # ---------------------------
                # 2) If post-processing is needed, execute follow-up tasks in parallel
                # ---------------------------
                if need_post_process:
                    logging.info("JIRA check indicates we need to proceed with post-processing...")
                    
                    # Submit two follow-up tasks in parallel
                    future_mattermost = task_executor.submit(self._process_mattermost)
                    future_confluence = task_executor.submit(self._process_confluence)
                    
                    # Wait for both tasks to complete
                    mattermost_result = future_mattermost.result()
                    confluence_result = future_confluence.result()
                    
                    logging.info(f"Parallel processing results - Mattermost: {mattermost_result}, Confluence: {confluence_result}")

            # Task completed, mark as DONE
            self.task_repository.update_task_status(task_id, TaskStatus.DONE)
            logging.info(f"Task {task.id} completed successfully.")
            result = {"success": True}

        except Exception as e:
            # If exception occurs, mark as FAILED
            self.task_repository.update_task_status(task_id, TaskStatus.FAILED)
            logging.error(f"Task {task.id} failed with error: {e}")
            result = {"success": False, "error": str(e)}
        
        finally:
            # Save the result regardless of success or failure
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

            # [新增] 使用外部注入类对结果进行后续处理（发送到 Mattermost 等）
            if taskDto:
                # 从 DIContainer 获取我们注册的 ResultReporter
                result_reporter = self.di_container.get_result_reporter()
                result_reporter.handle_task_result(taskDto, result_item)
            
            return result

    def _process_mattermost(self):
        """Process Mattermost operations as a parallelizable sub-task"""
        try:
            mattermost_processor = self.di_container.get_mattermost_data_processor()
            mattermost_processor.send_notification()
            return {"mattermost_success": True}
        except Exception as e:
            logging.error(f"Mattermost processing error: {e}")
            return {"mattermost_success": False, "error": str(e)}

    def _process_confluence(self):
        """Process Confluence operations as a parallelizable sub-task"""
        try:
            confluence_processor = self.di_container.get_confluence_data_processor()
            page_id = "123456"  # This should come from task parameters
            new_data = [{"Column1": "Value1"}, {"Column1": "Value2"}]  # This should come from task results
            success = confluence_processor.handle_page_update(page_id, new_data)
            return {"confluence_success": success}
        except Exception as e:
            logging.error(f"Confluence processing error: {e}")
            return {"confluence_success": False, "error": str(e)}