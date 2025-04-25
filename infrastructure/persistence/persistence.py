# scheduler/persistence.py
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from domain.entities.models import Task, TaskStatus, TaskScheduleType, TaskPriority

class TaskPersistenceManager:
    """Handles persistence of tasks to allow recovery after application restart."""
    
    def __init__(self, storage_path: str = "task_storage"):
        self.storage_path = storage_path
        self.snapshot_file = os.path.join(storage_path, "tasks_snapshot.json")
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_tasks_snapshot(self, tasks: List[Task]) -> bool:
        """Save current tasks to a snapshot file."""
        try:
            task_dicts = [task.dict() for task in tasks]
            # Convert datetime objects to ISO format strings and UUID to string
            for task_dict in task_dicts:
                task_dict["created_at"] = task_dict["created_at"].isoformat()
                task_dict["updated_at"] = task_dict["updated_at"].isoformat()
                task_dict["id"] = str(task_dict["id"])  # Convert UUID to string
                
                # Also convert any UUID in dependencies list
                if "dependencies" in task_dict:
                    task_dict["dependencies"] = [str(dep) for dep in task_dict["dependencies"]]
            
            with open(self.snapshot_file, 'w') as f:
                json.dump(task_dicts, f, indent=2)
            logging.info(f"Successfully saved {len(tasks)} tasks to snapshot")
            return True
        except Exception as e:
            logging.error(f"Failed to save tasks snapshot: {e}")
            return False

    def load_tasks_snapshot(self) -> Optional[List[Dict[str, Any]]]:
        """Load tasks from the snapshot file."""
        if not os.path.exists(self.snapshot_file):
            logging.info("No tasks snapshot file found")
            return None
        
        try:
            with open(self.snapshot_file, 'r') as f:
                task_dicts = json.load(f)
            
            # Convert ISO format strings to datetime objects and string to UUID
            for task_dict in task_dicts:
                task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
                task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
                task_dict["id"] = UUID(task_dict["id"])  # Convert string to UUID
                
                # Also convert dependencies from string to UUID
                if "dependencies" in task_dict:
                    task_dict["dependencies"] = [UUID(dep) for dep in task_dict["dependencies"]]
            
            logging.info(f"Loaded {len(task_dicts)} tasks from snapshot")
            return task_dicts
        except Exception as e:
            logging.error(f"Failed to load tasks snapshot: {e}")
            return None