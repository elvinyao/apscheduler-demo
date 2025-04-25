"""
Repository implementation for Task Result entities.
"""
import threading
from typing import List, Optional, Dict, Any, TypeVar, Generic
from copy import deepcopy
from uuid import UUID

from domain.entities.repositories import BaseRepository
from domain.exceptions import EntityNotFoundError

# Define a type for task results (using dict for flexibility)
TaskResult = Dict[str, Any]
T = TypeVar('T', bound=TaskResult)

class TaskResultRepository(BaseRepository[TaskResult], Generic[T]):
    """
    Repository for task execution results.
    This is an in-memory implementation.
    """
    
    def __init__(self):
        self._results: List[TaskResult] = []
        self._lock = threading.Lock()
    
    def get_by_id(self, entity_id: Any) -> Optional[TaskResult]:
        """Get a result by its task_id."""
        with self._lock:
            for result in self._results:
                if result.get('task_id') == entity_id:
                    return deepcopy(result)
        
        raise EntityNotFoundError("TaskResult", entity_id)
    
    def get_all(self) -> List[TaskResult]:
        """Get all results."""
        with self._lock:
            return deepcopy(self._results)
    
    def add(self, entity: TaskResult) -> TaskResult:
        """Add a new result."""
        with self._lock:
            self._results.append(deepcopy(entity))
            return entity
    
    def update(self, entity: TaskResult) -> TaskResult:
        """Update an existing result."""
        with self._lock:
            for i, result in enumerate(self._results):
                if result.get('task_id') == entity.get('task_id'):
                    self._results[i] = deepcopy(entity)
                    return entity
        
        raise EntityNotFoundError("TaskResult", entity.get('task_id'))
    
    def delete(self, entity_id: Any) -> bool:
        """Delete a result by its task_id."""
        with self._lock:
            for i, result in enumerate(self._results):
                if result.get('task_id') == entity_id:
                    del self._results[i]
                    return True
        
        raise EntityNotFoundError("TaskResult", entity_id)
    
    # Additional methods
    
    def clear_all(self) -> None:
        """Clear all results."""
        with self._lock:
            self._results.clear()
    
    def get_by_task_ids(self, task_ids: List[UUID]) -> List[TaskResult]:
        """Get results for multiple task IDs."""
        with self._lock:
            return deepcopy([r for r in self._results if r.get('task_id') in task_ids])