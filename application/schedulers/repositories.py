# scheduler/repositories.py

from dataclasses import dataclass
from typing import Any

@dataclass
class Repositories:
    """Container for repository instances used by the scheduler."""
    
    task_repository: Any
    task_result_repo: Any