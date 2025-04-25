"""
Base repository interfaces for the application.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict

T = TypeVar('T')  # Generic type for entity

class BaseRepository(Generic[T], ABC):
    """Base repository interface that all repositories should implement."""
    
    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Get an entity by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete an entity by ID."""
        pass

class UnitOfWork(ABC):
    """
    Unit of Work pattern implementation.
    Coordinates the work of multiple repositories in a single transaction.
    """
    
    @abstractmethod
    def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    def __enter__(self):
        self.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()