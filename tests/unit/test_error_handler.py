import pytest
from application.error_handler import ErrorHandler
from domain.exceptions import (
    IntegrationException, ApiConnectionError, ApiAuthenticationError, ApiResponseError,
    DomainException, ValidationError, BusinessRuleViolation,
    RepositoryException, EntityNotFoundError, DataConsistencyError,
    SchedulerException, TaskExecutionError
)

@pytest.fixture
def error_handler():
    return ErrorHandler()

def test_handle_integration_error(error_handler):
    error = ApiConnectionError("test_service", {"reason": "timeout"})
    result = error_handler.handle_error(error)
    assert result["success"] is False
    assert result["error"]["type"] == "integration_error"
    assert result["error"]["code"] == "API_CONNECTION_ERROR"
    assert "test_service" in result["error"]["message"]
    assert result["error"]["details"]["reason"] == "timeout"

def test_handle_domain_error(error_handler):
    error = ValidationError("Invalid input", field="email", details={"value": "invalid"})
    result = error_handler.handle_error(error)
    assert result["success"] is False
    assert result["error"]["type"] == "domain_error"
    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert result["error"]["details"]["field"] == "email"

def test_handle_repository_error(error_handler):
    error = EntityNotFoundError("Task", "123", {"context": "query"})
    result = error_handler.handle_error(error)
    assert result["success"] is False
    assert result["error"]["type"] == "repository_error"
    assert result["error"]["code"] == "ENTITY_NOT_FOUND"
    assert result["error"]["details"]["entity_id"] == "123"

def test_handle_scheduler_error(error_handler):
    error = TaskExecutionError("task123", "Execution failed", {"reason": "timeout"})
    result = error_handler.handle_error(error)
    assert result["success"] is False
    assert result["error"]["type"] == "scheduler_error"
    assert result["error"]["code"] == "TASK_EXECUTION_ERROR"
    assert result["error"]["details"]["task_id"] == "task123"

def test_handle_generic_error(error_handler):
    error = Exception("Unexpected error")
    result = error_handler.handle_error(error)
    assert result["success"] is False
    assert result["error"]["type"] == "unexpected_error"
    assert result["error"]["code"] == "UNEXPECTED_ERROR"

def test_handle_error_with_context(error_handler):
    error = ApiResponseError("test_service", status_code=500)
    context = {"request_id": "req123", "user_id": "user456"}
    result = error_handler.handle_error(error, context)
    assert result["success"] is False
    assert result["error"]["type"] == "integration_error"
    assert result["error"]["details"]["status_code"] == 500

def test_error_handler_singleton():
    from application.error_handler import error_handler
    assert isinstance(error_handler, ErrorHandler) 