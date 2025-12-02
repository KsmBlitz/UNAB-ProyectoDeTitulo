"""
Custom Exceptions
Application-specific exceptions for better error handling
Following Single Responsibility Principle - each exception type handles specific error category
"""

from typing import Optional, Dict, Any


class AppException(Exception):
    """
    Base application exception
    All custom exceptions should inherit from this
    """
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class NotFoundException(AppException):
    """
    Resource not found exception
    Used when a requested resource doesn't exist
    """
    
    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} not found: {identifier}"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details or {"resource": resource, "identifier": identifier}
        )


class ValidationException(AppException):
    """
    Validation exception
    Used when input data fails validation
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=error_details
        )


class AuthenticationException(AppException):
    """
    Authentication exception
    Used when authentication fails (invalid credentials, expired token, etc)
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details or {}
        )


class AuthorizationException(AppException):
    """
    Authorization exception
    Used when user lacks permission for an action
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        required_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_role:
            error_details["required_role"] = required_role
        
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=error_details
        )


class ServiceException(AppException):
    """
    Service layer exception
    Used when a service operation fails
    """
    
    def __init__(
        self,
        service: str,
        operation: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["service"] = service
        error_details["operation"] = operation
        
        super().__init__(
            message=message,
            code="SERVICE_ERROR",
            status_code=500,
            details=error_details
        )


class RepositoryException(AppException):
    """
    Repository layer exception
    Used when a database operation fails
    """
    
    def __init__(
        self,
        repository: str,
        operation: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["repository"] = repository
        error_details["operation"] = operation
        
        super().__init__(
            message=message,
            code="REPOSITORY_ERROR",
            status_code=500,
            details=error_details
        )


class RateLimitException(AppException):
    """
    Rate limit exceeded exception
    Used when user exceeds API rate limits
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=error_details
        )


class ExternalServiceException(AppException):
    """
    External service exception
    Used when an external service (Twilio, email, etc) fails
    """
    
    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["external_service"] = service_name
        
        super().__init__(
            message=f"{service_name} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=error_details
        )


class SensorException(AppException):
    """
    Sensor-related exception
    Used for sensor-specific errors
    """
    
    def __init__(
        self,
        sensor_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["sensor_id"] = sensor_id
        
        super().__init__(
            message=message,
            code="SENSOR_ERROR",
            status_code=400,
            details=error_details
        )


class AlertException(AppException):
    """
    Alert-related exception
    Used for alert-specific errors
    """
    
    def __init__(
        self,
        alert_id: Optional[str],
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if alert_id:
            error_details["alert_id"] = alert_id
        
        super().__init__(
            message=message,
            code="ALERT_ERROR",
            status_code=400,
            details=error_details
        )
