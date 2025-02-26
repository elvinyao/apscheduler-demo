# aggregator_demo.py
#
# 该示例演示仅保留 "AggregatorJob" 统一更新 Confluence 的相关实现。
# 不包含任何 JIRA 相关逻辑。

import logging
import threading
import time
from typing import Dict, Any, List
from copy import deepcopy

# -------------------------------------------------
# 1) TaskResultRepository
# -------------------------------------------------
class TaskResultRepository:
    """
    用于存储任务执行的结果信息(可替换为数据库实现)。
    这里仅保存在内存中，用一个列表 _results。
    """
    def __init__(self):
        self._results: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def save_task_result(self, result_item: Dict[str, Any]):
        """
        将任务执行的结果写入列表
        """
        with self._lock:
            self._results.append(deepcopy(result_item))

    def get_all_results(self) -> List[Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._results)

    def clear_results(self):
        with self._lock:
            self._results.clear()

# -------------------------------------------------
# 2) ConfluenceUpdater
# -------------------------------------------------
class ConfluenceUpdater:
    """
    统一的Confluence更新逻辑(这里仅用日志模拟)
    """
    def update_confluence(self, aggregated_data: List[Dict[str, Any]]):
        data_preview = str(aggregated_data)[:50] + "..." if len(str(aggregated_data)) > 50 else str(aggregated_data)
        logging.info("Updating Confluence with aggregated data: %s", data_preview)
        time.sleep(1)
        logging.info("Confluence update done.")
