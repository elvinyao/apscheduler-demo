# scheduler/executors.py

from dataclasses import dataclass
from typing import Any

@dataclass
class Executors:
    """Container for executor instances used by the scheduler."""
    
    task_executor: Any
    confluence_updater: Any