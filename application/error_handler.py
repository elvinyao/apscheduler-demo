"""
Central error handling utilities for the application.
"""
import logging
import sys
import traceback
from typing import Dict, Any, Optional, Callable, Type

from domain.exceptions import BaseAppException, IntegrationException, DomainException, RepositoryException, SchedulerException

class ErrorHandler:
    """
    Central error handler that provides consistent error handling across the application.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Map exception types to handlers
        self.handlers: Dict[Type[Exception], Callable] = {
            IntegrationException: self._handle_integration_error,
            DomainException: self._handle_domain_error,
            RepositoryException: self._handle_repository_error,
            SchedulerException: self._handle_scheduler_error,
            Exception: self._handle_generic_error
        }
    
    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an exception by delegating to the appropriate handler.
        
        Args:
            exception: The exception to handle
            context: Optional additional context about where the error occurred
            
        Returns:
            A dictionary with standardized error information
        """
        context = context or {}
        
        # Find the most specific handler for this exception type
        handler = self._get_handler(exception.__class__)
        return handler(exception, context)
    
    def _get_handler(self, exception_class: Type[Exception]) -> Callable:
        """Get the most specific handler for an exception type."""
        for cls, handler in self.handlers.items():
            if issubclass(exception_class, cls):
                return handler
        return self._handle_generic_error
    
    def _handle_integration_error(self, exception: IntegrationException, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle integration layer errors."""
        self.logger.error(
            f"Integration error: {exception.code} - {exception.message}",
            extra={"details": exception.details, "context": context}
        )
        return {
            "success": False,
            "error": {
                "type": "integration_error",
                "code": exception.code,
                "message": exception.message,
                "details": exception.details
            }
        }
    
    def _handle_domain_error(self, exception: DomainException, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain layer errors."""
        self.logger.error(
            f"Domain error: {exception.code} - {exception.message}",
            extra={"details": exception.details, "context": context}
        )
        return {
            "success": False,
            "error": {
                "type": "domain_error",
                "code": exception.code,
                "message": exception.message,
                "details": exception.details
            }
        }
    
    def _handle_repository_error(self, exception: RepositoryException, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle repository layer errors."""
        self.logger.error(
            f"Repository error: {exception.code} - {exception.message}",
            extra={"details": exception.details, "context": context}
        )
        return {
            "success": False,
            "error": {
                "type": "repository_error",
                "code": exception.code,
                "message": exception.message,
                "details": exception.details
            }
        }
    
    def _handle_scheduler_error(self, exception: SchedulerException, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduler errors."""
        self.logger.error(
            f"Scheduler error: {exception.code} - {exception.message}",
            extra={"details": exception.details, "context": context}
        )
        return {
            "success": False,
            "error": {
                "type": "scheduler_error",
                "code": exception.code,
                "message": exception.message,
                "details": exception.details
            }
        }
    
    def _handle_generic_error(self, exception: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other unclassified errors."""
        exc_info = sys.exc_info()
        stack_trace = traceback.format_exception(*exc_info)
        
        self.logger.error(
            f"Unexpected error: {str(exception)}",
            extra={"traceback": "".join(stack_trace), "context": context},
            exc_info=True
        )
        
        # For BaseAppException we can still use its fields
        if isinstance(exception, BaseAppException):
            return {
                "success": False,
                "error": {
                    "type": "application_error",
                    "code": exception.code,
                    "message": exception.message,
                    "details": exception.details
                }
            }
        
        # For standard exceptions we have less info
        return {
            "success": False,
            "error": {
                "type": "unexpected_error",
                "code": "UNEXPECTED_ERROR",
                "message": str(exception)
            }
        }

# Create a singleton instance for global use
error_handler = ErrorHandler()