# scheduler/config.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class SchedulerConfig:
    """Configuration for the scheduler service."""
    
    # Concurrency settings
    max_concurrent_jobs: int = 5
    
    # Scheduler settings
    coalesce: bool = False
    max_instances: int = 5
    
    # Polling intervals (seconds)
    poll_interval: int = 30
    queue_processing_interval: int = 1
    retry_processing_interval: int = 30
    
    # Cron expressions
    read_data_cron: str = '* * * * *'  # Every minute
    fetch_confluence_cron: str = '* * * * *'  # Every minute