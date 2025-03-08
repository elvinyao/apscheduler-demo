"""
Core exception classes for standardized error handling across the application.
"""
from typing import Optional, Dict, Any

class BaseAppException(Exception):
    """Base exception for all application-specific exceptions."""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.code}: {self.message}"

# Integration Layer Exceptions
class IntegrationException(BaseAppException):
    """Base exception for all integration layer errors."""
    def __init__(self, message: str, code: str = "INTEGRATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ApiConnectionError(IntegrationException):
    """Raised when a connection to an external API fails."""
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to connect to {service_name} API",
            code="API_CONNECTION_ERROR",
            details=details
        )

class ApiAuthenticationError(IntegrationException):
    """Raised when authentication with an external API fails."""
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Authentication failed with {service_name} API",
            code="API_AUTH_ERROR",
            details=details
        )

class ApiResponseError(IntegrationException):
    """Raised when an API response indicates an error."""
    def __init__(self, service_name: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(
            message=f"Error response from {service_name} API",
            code="API_RESPONSE_ERROR",
            details=error_details
        )

# Domain Layer Exceptions
class DomainException(BaseAppException):
    """Base exception for all domain layer errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ValidationError(DomainException):
    """Raised when validation of domain data fails."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=error_details
        )

class BusinessRuleViolation(DomainException):
    """Raised when a business rule is violated."""
    def __init__(self, rule: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = message or f"Business rule violation: {rule}"
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details=details
        )

# Repository Layer Exceptions
class RepositoryException(BaseAppException):
    """Base exception for all repository layer errors."""
    def __init__(self, message: str, code: str = "REPOSITORY_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class EntityNotFoundError(RepositoryException):
    """Raised when an entity is not found in the repository."""
    def __init__(self, entity_type: str, entity_id: Any, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"entity_type": entity_type, "entity_id": str(entity_id)})
        
        super().__init__(
            message=f"{entity_type} with ID {entity_id} not found",
            code="ENTITY_NOT_FOUND",
            details=error_details
        )

class DataConsistencyError(RepositoryException):
    """Raised when there's a data consistency issue."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATA_CONSISTENCY_ERROR",
            details=details
        )

# Scheduler Exceptions
class SchedulerException(BaseAppException):
    """Base exception for all scheduler-related errors."""
    def __init__(self, message: str, code: str = "SCHEDULER_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class TaskExecutionError(SchedulerException):
    """Raised when a task execution fails."""
    def __init__(self, task_id: Any, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details["task_id"] = str(task_id)
        
        super().__init__(
            message=message or f"Error executing task {task_id}",
            code="TASK_EXECUTION_ERROR",
            details=error_details
        )