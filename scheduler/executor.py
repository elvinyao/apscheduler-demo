"""
executor.py
Contains logic for executing different types of tasks.
"""

import logging
import time
from datetime import datetime

from domain.jira_data_processor import JiraDataProcessor
from domain.mattermost_data_processor import MattermostDataProcessor
from domain.confluence_data_processor import ConfluenceDataProcessor

class TaskExecutor:
    """
    Contains the logic for executing tasks.
    """
    def __init__(self, task_repository,task_result_repo):
        self.task_repository = task_repository
        self.task_result_repo = task_result_repo

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
        Fetch the task from the repository, mark it RUNNING, then simulate:
          1) 通过JiraDataProcessor调用JIRA API获取最后评论，判断是否需要后续业务
          2) 若需要，则调用 MattermostDataProcessor + ConfluenceDataProcessor 
             完成后续处理
        Finally mark the task as DONE or FAILED.
        """
        # Mark the task as RUNNING
        self.task_repository.update_task_status(task_id, 'RUNNING')
        task = self.task_repository.get_task_by_id(task_id)
        if not task:
            logging.warning(f"Task with id={task_id} not found.")
            return

        logging.info(f"[{datetime.now()}] Executing task: id={task.id}, name={task.name}, type={task.task_type}...")

        try:
            # ---------------------------
            # 1) 任务处理 (JIRA)
            # ---------------------------
            jira_processor = JiraDataProcessor()
            need_post_process = jira_processor.process_jira_ticket()

            # ---------------------------
            # 2) 后续操作 (Mattermost + Confluence)
            # ---------------------------
            if need_post_process:
                logging.info("Comment indicates we need to proceed with post-processing...")

                mattermost_processor = MattermostDataProcessor()
                mattermost_processor.send_notification()

                confluence_processor = ConfluenceDataProcessor()
                confluence_processor.update_confluence_page()

            # 最终标记DONE
            self.task_repository.update_task_status(task_id, 'DONE')
            logging.info(f"Task {task.id} completed successfully.")

        except Exception as e:
            # 如果发生异常, 标记FAILED
            self.task_repository.update_task_status(task_id, 'FAILED')
            logging.error(f"Task {task.id} failed with error: {e}")
        finally:
            # 无论成功与否
            logging.info(f"execute_task({task_id}) finally block.")
            time.sleep(1)  # 模拟某种处理
            taskDto=self.task_repository.get_task_by_id(task_id)
            result_item = {
                "task_id": task_id,
                "result_value": f"processed_{task_id}",
                "result_status_value": f"{taskDto}",
                "timestamp": time.time()
            }
            self.task_result_repo.save_task_result(result_item)
            logging.info(f"execute_task({task_id}) done, result saved.")
