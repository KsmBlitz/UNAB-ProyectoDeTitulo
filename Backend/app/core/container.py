"""
Dependency Injection Container
Manages service and repository instances following Inversion of Control (IoC) pattern
This allows for easy testing and swapping implementations
"""

from typing import TypeVar, Type, Optional, Dict, Any, Callable
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Container:
    """
    Dependency Injection Container
    
    Implements the Service Locator / IoC Container pattern for managing dependencies.
    Supports singleton and transient lifetimes.
    
    Usage:
        container = Container()
        container.register_singleton(IAlertRepository, AlertRepository)
        container.register_transient(IAlertService, AlertService)
        
        alert_service = container.resolve(IAlertService)
    """
    
    _instance: Optional['Container'] = None
    
    def __new__(cls) -> 'Container':
        """Ensure singleton container instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._singletons: Dict[Type, Any] = {}
        self._singleton_factories: Dict[Type, Callable] = {}
        self._transient_factories: Dict[Type, Callable] = {}
        self._initialized = True
        logger.debug("Dependency container initialized")
    
    def register_singleton(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'Container':
        """
        Register a singleton dependency
        
        Singleton: Same instance is returned for all requests
        
        Args:
            interface: The interface/protocol type
            implementation: The implementing class (optional if factory or instance provided)
            factory: Factory function to create instance (optional)
            instance: Pre-created instance (optional)
            
        Returns:
            Container for method chaining
        """
        if instance is not None:
            self._singletons[interface] = instance
        elif factory is not None:
            self._singleton_factories[interface] = factory
        elif implementation is not None:
            self._singleton_factories[interface] = implementation
        else:
            raise ValueError("Must provide implementation, factory, or instance")
        
        logger.debug(f"Registered singleton: {interface.__name__}")
        return self
    
    def register_transient(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a transient dependency
        
        Transient: New instance is created for each request
        
        Args:
            interface: The interface/protocol type
            implementation: The implementing class (optional if factory provided)
            factory: Factory function to create instance (optional)
            
        Returns:
            Container for method chaining
        """
        if factory is not None:
            self._transient_factories[interface] = factory
        elif implementation is not None:
            self._transient_factories[interface] = implementation
        else:
            raise ValueError("Must provide implementation or factory")
        
        logger.debug(f"Registered transient: {interface.__name__}")
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency by its interface type
        
        Args:
            interface: The interface type to resolve
            
        Returns:
            Instance of the implementation
            
        Raises:
            KeyError: If interface is not registered
        """
        # Check pre-created singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check singleton factories
        if interface in self._singleton_factories:
            factory = self._singleton_factories[interface]
            instance = factory() if callable(factory) else factory
            self._singletons[interface] = instance
            return instance
        
        # Check transient factories
        if interface in self._transient_factories:
            factory = self._transient_factories[interface]
            return factory() if callable(factory) else factory
        
        raise KeyError(f"No registration found for {interface.__name__}")
    
    def is_registered(self, interface: Type) -> bool:
        """Check if an interface is registered"""
        return (
            interface in self._singletons or
            interface in self._singleton_factories or
            interface in self._transient_factories
        )
    
    def reset(self) -> None:
        """
        Reset container state
        
        Useful for testing to clear all registrations
        """
        self._singletons.clear()
        self._singleton_factories.clear()
        self._transient_factories.clear()
        logger.debug("Container reset")
    
    def override(self, interface: Type[T], instance: T) -> 'Container':
        """
        Override a registration with a specific instance
        
        Useful for testing with mocks
        
        Args:
            interface: The interface type to override
            instance: The mock/test instance
            
        Returns:
            Container for method chaining
        """
        # Remove from factories if exists
        self._singleton_factories.pop(interface, None)
        self._transient_factories.pop(interface, None)
        
        # Set as singleton instance
        self._singletons[interface] = instance
        logger.debug(f"Override registered: {interface.__name__}")
        return self


@lru_cache(maxsize=1)
def get_container() -> Container:
    """
    Get the singleton container instance
    
    This function is cached to ensure same container is returned
    
    Returns:
        The application container instance
    """
    return Container()


def configure_container(container: Container) -> Container:
    """
    Configure the container with all application dependencies
    
    This function sets up the dependency graph for the application.
    Called during application startup.
    
    Args:
        container: The container to configure
        
    Returns:
        Configured container
    """
    # Import implementations
    from app.repositories.alert_repository import AlertRepository
    from app.repositories.sensor_repository import SensorRepository
    from app.repositories.user_repository import UserRepository
    from app.services.alert_service import AlertService
    from app.services.sensor_service import SensorService
    from app.services.notification_service import NotificationService
    from app.services.cache import CacheService
    
    # Import interfaces
    from app.core.interfaces import (
        IAlertRepository,
        ISensorRepository,
        IUserRepository,
        IAlertService,
        ISensorService,
        INotificationService,
        ICacheService
    )
    
    # Register repositories (singletons)
    container.register_singleton(IAlertRepository, factory=AlertRepository)
    container.register_singleton(ISensorRepository, factory=SensorRepository)
    container.register_singleton(IUserRepository, factory=UserRepository)
    
    # Register services (singletons with dependency resolution)
    container.register_singleton(ICacheService, factory=CacheService)
    container.register_singleton(INotificationService, factory=NotificationService)
    
    # Services that depend on repositories
    container.register_singleton(
        ISensorService,
        factory=lambda: SensorService(
            sensor_repo=container.resolve(ISensorRepository)
        )
    )
    
    container.register_singleton(
        IAlertService,
        factory=lambda: AlertService(
            alert_repo=container.resolve(IAlertRepository),
            sensor_repo=container.resolve(ISensorRepository),
            notif_service=container.resolve(INotificationService)
        )
    )
    
    logger.info("Dependency container configured successfully")
    return container


# FastAPI dependency injection helpers
def get_alert_service() -> 'AlertService':
    """FastAPI dependency for AlertService"""
    from app.core.interfaces import IAlertService
    return get_container().resolve(IAlertService)


def get_sensor_service() -> 'SensorService':
    """FastAPI dependency for SensorService"""
    from app.core.interfaces import ISensorService
    return get_container().resolve(ISensorService)


def get_notification_service() -> 'NotificationService':
    """FastAPI dependency for NotificationService"""
    from app.core.interfaces import INotificationService
    return get_container().resolve(INotificationService)


def get_cache_service() -> 'CacheService':
    """FastAPI dependency for CacheService"""
    from app.core.interfaces import ICacheService
    return get_container().resolve(ICacheService)
