"""
Core module
Contains interfaces, abstractions, and core infrastructure components
following SOLID principles (especially Dependency Inversion Principle)
"""

from .interfaces import (
    IRepository,
    IAlertRepository,
    ISensorRepository,
    IUserRepository,
    INotificationService,
    IAlertService,
    ISensorService,
    ICacheService
)

from .exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ServiceException,
    RepositoryException,
    RateLimitException,
    ExternalServiceException,
    SensorException,
    AlertException
)

from .container import (
    Container,
    get_container,
    configure_container,
    get_alert_service,
    get_sensor_service,
    get_notification_service,
    get_cache_service
)

from .handlers import register_exception_handlers

from .validators import (
    BaseValidator,
    AlertConfigValidator,
    SensorValidator,
    UserValidator
)

__all__ = [
    # Interfaces
    "IRepository",
    "IAlertRepository",
    "ISensorRepository",
    "IUserRepository",
    "INotificationService",
    "IAlertService",
    "ISensorService",
    "ICacheService",
    # Exceptions
    "AppException",
    "NotFoundException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "ServiceException",
    "RepositoryException",
    "RateLimitException",
    "ExternalServiceException",
    "SensorException",
    "AlertException",
    # Container
    "Container",
    "get_container",
    "configure_container",
    "get_alert_service",
    "get_sensor_service",
    "get_notification_service",
    "get_cache_service",
    # Handlers
    "register_exception_handlers",
    # Validators
    "BaseValidator",
    "AlertConfigValidator",
    "SensorValidator",
    "UserValidator"
]
