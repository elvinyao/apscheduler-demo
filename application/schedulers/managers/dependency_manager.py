import logging
from typing import Dict, Set, Optional, List
from uuid import UUID

class DependencyManager:
    """
    Manages task dependencies, tracking which tasks are waiting on others
    and determining when dependent tasks can be executed.
    """
    def __init__(self, task_repository):
        self.task_repository = task_repository
        self.dependency_map = {}  # Maps task_id to set of tasks waiting on it
        self.waiting_on_dependencies = set()  # Set of task_ids waiting for dependencies
    
    def initialize_from_existing_tasks(self):
        """Initialize dependency map from existing tasks in the repository."""
        all_tasks = self.task_repository.get_all()
        
        for task in all_tasks:
            if task.dependencies:
                # Add task to waiting set if it has dependencies
                self.waiting_on_dependencies.add(task.id)
                
                # Add task as a dependent for each of its dependencies
                for dep_id in task.dependencies:
                    if dep_id not in self.dependency_map:
                        self.dependency_map[dep_id] = set()
                    self.dependency_map[dep_id].add(task.id)
        
        logging.info(f"Initialized dependency map with {len(self.dependency_map)} dependencies")
    
    def register_task_dependencies(self, task_id, dependency_ids):
        """Register dependencies for a task."""
        if not dependency_ids:
            return False  # No dependencies to register
            
        has_unmet_dependencies = False
        
        # Add task to waiting set
        self.waiting_on_dependencies.add(task_id)
        
        # Check each dependency
        for dep_id in dependency_ids:
            dep_task = self.task_repository.get_by_id(dep_id)
            if not dep_task or dep_task.status != "DONE":
                # Add to dependency map
                if dep_id not in self.dependency_map:
                    self.dependency_map[dep_id] = set()
                self.dependency_map[dep_id].add(task_id)
                has_unmet_dependencies = True
        
        return has_unmet_dependencies
    
    def get_ready_dependent_tasks(self, completed_task_id):
        """
        Get tasks that were waiting on the completed task and are now ready to execute.
        Returns a list of task IDs that are now ready.
        """
        ready_tasks = []
        
        # Get completed task status
        completed_task = self.task_repository.get_by_id(completed_task_id)
        if not completed_task or completed_task.status != "DONE":
            # Only proceed with dependent tasks if this task completed successfully
            return ready_tasks
            
        if completed_task_id in self.dependency_map:
            dependent_task_ids = self.dependency_map[completed_task_id].copy()
            
            for dep_task_id in dependent_task_ids:
                # Check if all dependencies are satisfied
                dep_task = self.task_repository.get_by_id(dep_task_id)
                if not dep_task:
                    continue
                    
                all_deps_satisfied = True
                for parent_id in dep_task.dependencies:
                    parent_task = self.task_repository.get_by_id(parent_id)
                    if not parent_task or parent_task.status != "DONE":
                        all_deps_satisfied = False
                        break
                
                if all_deps_satisfied:
                    # Remove from waiting list
                    if dep_task_id in self.waiting_on_dependencies:
                        self.waiting_on_dependencies.remove(dep_task_id)
                    
                    # Remove from dependency map
                    for parent_id in dep_task.dependencies:
                        if parent_id in self.dependency_map and dep_task_id in self.dependency_map[parent_id]:
                            self.dependency_map[parent_id].remove(dep_task_id)
                    
                    # Add to ready tasks
                    ready_tasks.append(dep_task_id)
        
        return ready_tasks
    
    def has_dependencies(self, task_id):
        """Check if a task has dependencies."""
        return task_id in self.waiting_on_dependencies 