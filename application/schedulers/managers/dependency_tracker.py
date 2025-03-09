# scheduler/managers/dependency_tracker.py

import logging
from typing import Dict, Set, List, Optional
from uuid import UUID

from domain.entities.models import TaskStatus, Task

class DependencyTracker:
    """Tracks and manages task dependencies."""
    
    def __init__(self, task_repository):
        self.task_repository = task_repository
        self.dependency_map: Dict[UUID, Set[UUID]] = {}  # Maps task_id to set of tasks waiting on it
        self.waiting_on_dependencies: Set[UUID] = set()  # Set of task_ids waiting for dependencies
        
        # Initialize from existing tasks
        self._initialize_dependency_map()
    
    def _initialize_dependency_map(self) -> None:
        """Initialize dependency map from existing tasks."""
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
    
    def register_task_dependencies(self, task: Task) -> None:
        """Register a task's dependencies in the tracker."""
        if not task.dependencies:
            return
            
        # Add task to waiting set if it has dependencies
        self.waiting_on_dependencies.add(task.id)
        
        # Add task as a dependent for each of its dependencies
        for dep_id in task.dependencies:
            if dep_id not in self.dependency_map:
                self.dependency_map[dep_id] = set()
            self.dependency_map[dep_id].add(task.id)
    
    def has_unmet_dependencies(self, task: Task) -> bool:
        """Check if task has any unmet dependencies."""
        if not task.dependencies:
            return False
            
        for dep_id in task.dependencies:
            dep_task = self.task_repository.get_by_id(dep_id)
            if not dep_task or dep_task.status != TaskStatus.DONE:
                return True
        
        return False
    
    def get_dependent_tasks(self, completed_task_id: UUID) -> List[UUID]:
        """Get list of task IDs that depend on the completed task."""
        if completed_task_id in self.dependency_map:
            return list(self.dependency_map[completed_task_id])
        return []
    
    def clear_dependency(self, dependent_task_id: UUID, dependency_id: UUID) -> None:
        """Clear a specific dependency relationship."""
        if dependency_id in self.dependency_map and dependent_task_id in self.dependency_map[dependency_id]:
            self.dependency_map[dependency_id].remove(dependent_task_id)
    
    def clear_task_dependencies(self, task_id: UUID) -> None:
        """Clear all dependencies for a task when all are satisfied."""
        if task_id in self.waiting_on_dependencies:
            self.waiting_on_dependencies.remove(task_id)
        
        # Remove task from all dependency mappings
        task = self.task_repository.get_by_id(task_id)
        if task and task.dependencies:
            for dep_id in task.dependencies:
                self.clear_dependency(task_id, dep_id)