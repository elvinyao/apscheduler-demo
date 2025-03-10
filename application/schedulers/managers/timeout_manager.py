# scheduler/managers/timeout_manager.py

import logging
from threading import Timer
from typing import Dict, Callable
from uuid import UUID

class TimeoutManager:
    """
    Manages task timeouts, creating and tracking timers for tasks that 
    have a timeout setting and handling timeout events.
    """
    def __init__(self):
        self.timeout_timers = {}  # task_id -> Timer mapping
    
    def setup_timeout(self, task_id, timeout_seconds, on_timeout_callback):
        """
        Set up a timer to trigger when a task exceeds its timeout period.
        
        Args:
            task_id: The ID of the task
            timeout_seconds: Number of seconds after which the task times out
            on_timeout_callback: Function to call when timeout occurs
        """
        if task_id in self.timeout_timers:
            # Cancel existing timer if there is one
            self.cancel_timeout(task_id)
            
        timer = Timer(timeout_seconds, on_timeout_callback, args=[task_id])
        timer.daemon = True
        timer.start()
        self.timeout_timers[task_id] = timer
        
        logging.info(f"Set up timeout timer for task {task_id}: {timeout_seconds} seconds")
    
    def cancel_timeout(self, task_id):
        """
        Cancel a timeout timer for a task.
        Typically called when a task completes before timeout occurs.
        """
        if task_id in self.timeout_timers:
            self.timeout_timers[task_id].cancel()
            del self.timeout_timers[task_id]
            logging.debug(f"Cancelled timeout timer for task {task_id}")
    
    def shutdown(self):
        """Cancel all timeout timers."""
        for timer in self.timeout_timers.values():
            timer.cancel()
        self.timeout_timers.clear()
        logging.info("All timeout timers cancelled")