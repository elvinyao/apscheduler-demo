# scheduler/managers/timeout_manager.py

import logging
from threading import Timer
from typing import Dict, Callable
from uuid import UUID

class TimeoutManager:
    """Manages task timeout timers and handlers."""
    
    def __init__(self):
        self.timeout_timers: Dict[UUID, Timer] = {}
    
    def set_timeout(self, task_id: UUID, timeout_seconds: int, timeout_handler: Callable) -> None:
        """
        Set a timeout for a task with the specified handler.
        
        Args:
            task_id: The task identifier
            timeout_seconds: Timeout duration in seconds
            timeout_handler: Function to call when timeout occurs
        """
        # Cancel any existing timer for this task
        self.cancel_timeout(task_id)
        
        # Create new timer
        timer = Timer(timeout_seconds, timeout_handler, args=[task_id])
        timer.daemon = True
        timer.start()
        self.timeout_timers[task_id] = timer
        logging.debug(f"Set timeout for task {task_id} to {timeout_seconds} seconds")
    
    def cancel_timeout(self, task_id: UUID) -> bool:
        """
        Cancel a task timeout.
        
        Args:
            task_id: The task identifier
            
        Returns:
            bool: True if a timeout was cancelled, False otherwise
        """
        if task_id in self.timeout_timers:
            self.timeout_timers[task_id].cancel()
            del self.timeout_timers[task_id]
            logging.debug(f"Cancelled timeout for task {task_id}")
            return True
        return False
    
    def has_timeout(self, task_id: UUID) -> bool:
        """Check if a task has an active timeout."""
        return task_id in self.timeout_timers
    
    def cleanup(self) -> None:
        """Cancel all timeouts and clean up resources."""
        for timer in self.timeout_timers.values():
            timer.cancel()
        self.timeout_timers.clear()