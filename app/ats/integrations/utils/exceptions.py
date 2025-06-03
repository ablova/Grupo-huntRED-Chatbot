"""
Custom exceptions for integration handling.
Provides specific exception types for different integration scenarios.
"""

from typing import Optional, Dict, Any

class IntegrationError(Exception):
    """
    Base exception for all integration-related errors.
    """
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            context: Additional context about the error
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class PlatformConnectionError(IntegrationError):
    """
    Exception raised when there are issues connecting to a platform.
    """
    pass

class MessageSendError(IntegrationError):
    """
    Exception raised when there are issues sending messages.
    """
    pass

class WebhookError(IntegrationError):
    """
    Exception raised when there are issues with webhooks.
    """
    pass

class AuthenticationError(IntegrationError):
    """
    Exception raised when there are authentication issues.
    """
    pass

class RateLimitError(IntegrationError):
    """
    Exception raised when rate limits are exceeded.
    """
    pass

class ValidationError(IntegrationError):
    """
    Exception raised when data validation fails.
    """
    pass

class CacheError(IntegrationError):
    """
    Exception raised when there are issues with caching.
    """
    pass

class ConfigurationError(IntegrationError):
    """
    Exception raised when there are configuration issues.
    """
    pass

class BusinessUnitError(IntegrationError):
    """
    Exception raised when there are business unit related issues.
    """
    pass

class MenuError(IntegrationError):
    """
    Exception raised when there are issues with menu handling.
    """
    pass

class UserDataError(IntegrationError):
    """
    Exception raised when there are issues with user data.
    """
    pass

def handle_integration_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> IntegrationError:
    """
    Convert any exception to an IntegrationError with proper context.
    
    Args:
        error: The original exception
        context: Additional context about the error
        
    Returns:
        IntegrationError: Properly formatted integration error
    """
    if isinstance(error, IntegrationError):
        return error
        
    error_type = error.__class__.__name__
    error_message = str(error)
    
    # Map common exceptions to integration exceptions
    error_mapping = {
        'ConnectionError': PlatformConnectionError,
        'TimeoutError': PlatformConnectionError,
        'AuthenticationError': AuthenticationError,
        'ValidationError': ValidationError,
        'RateLimitError': RateLimitError,
        'CacheError': CacheError,
        'ConfigurationError': ConfigurationError
    }
    
    # Get the appropriate exception class
    exception_class = error_mapping.get(error_type, IntegrationError)
    
    # Create the error context
    error_context = {
        'original_error_type': error_type,
        'original_error_message': error_message,
        **(context or {})
    }
    
    return exception_class(
        f"Integration error: {error_message}",
        context=error_context
    ) 