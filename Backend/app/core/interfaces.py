"""
Interfaces and Protocols
Abstract base classes defining contracts for repositories and services
Following Dependency Inversion Principle (DIP) - depend on abstractions, not concretions
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime


T = TypeVar('T')


# ============================================================================
# Repository Interfaces
# ============================================================================

class IRepository(ABC, Generic[T]):
    """
    Base repository interface defining standard CRUD operations
    All repository implementations must adhere to this contract
    """
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find document by ID"""
        pass
    
    @abstractmethod
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching query"""
        pass
    
    @abstractmethod
    async def find_many(
        self, 
        query: Dict[str, Any],
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching query"""
        pass
    
    @abstractmethod
    async def insert_one(self, document: Dict[str, Any]) -> Optional[str]:
        """Insert single document, return inserted ID"""
        pass
    
    @abstractmethod
    async def update_one(
        self, 
        query: Dict[str, Any], 
        update: Dict[str, Any]
    ) -> bool:
        """Update single document, return success status"""
        pass
    
    @abstractmethod
    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """Delete single document, return success status"""
        pass
    
    @abstractmethod
    async def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query"""
        pass


class IAlertRepository(IRepository):
    """
    Alert repository interface
    Extends base repository with alert-specific operations
    """
    
    @abstractmethod
    async def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts"""
        pass
    
    @abstractmethod
    async def get_critical_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get critical level alerts"""
        pass
    
    @abstractmethod
    async def dismiss_alert(
        self,
        alert_id: str,
        dismissed_by: str,
        dismissed_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Dismiss/resolve an alert"""
        pass
    
    @abstractmethod
    async def get_alerts_by_sensor(
        self,
        sensor_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alerts for a specific sensor"""
        pass
    
    @abstractmethod
    async def create_alert(self, alert_doc: Dict[str, Any]) -> Optional[str]:
        """Create alert with business rule validation"""
        pass
    
    @abstractmethod
    async def archive_measurement_alerts_for_sensor(self, sensor_id: str) -> int:
        """Archive measurement alerts when sensor disconnects"""
        pass


class ISensorRepository(IRepository):
    """
    Sensor repository interface
    Extends base repository with sensor-specific operations
    """
    
    @abstractmethod
    async def get_sensor_by_id(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Get sensor by sensor_id field"""
        pass
    
    @abstractmethod
    async def get_all_sensors(self) -> List[Dict[str, Any]]:
        """Get all registered sensors"""
        pass
    
    @abstractmethod
    async def update_sensor_alert_config(
        self,
        sensor_id: str,
        alert_config: Dict[str, Any]
    ) -> bool:
        """Update alert configuration for a sensor"""
        pass
    
    @abstractmethod
    async def get_sensors_with_alert_config(self) -> List[Dict[str, Any]]:
        """Get sensors with alert configuration enabled"""
        pass
    
    @abstractmethod
    async def get_sensor_data(
        self,
        sensor_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent data readings for a sensor"""
        pass


class IUserRepository(IRepository):
    """
    User repository interface
    Extends base repository with user-specific operations
    """
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def get_admin_users(self) -> List[Dict[str, Any]]:
        """Get all users with admin role"""
        pass
    
    @abstractmethod
    async def update_password(
        self,
        user_id: str,
        hashed_password: str
    ) -> bool:
        """Update user password"""
        pass


# ============================================================================
# Service Interfaces
# ============================================================================

class IAlertService(ABC):
    """
    Alert service interface
    Defines business logic operations for alerts
    """
    
    @abstractmethod
    async def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        pass
    
    @abstractmethod
    async def get_critical_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get critical alerts only"""
        pass
    
    @abstractmethod
    async def dismiss_alert(
        self,
        alert_id: str,
        user_email: str,
        user_role: str = "operario",
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dismiss/close an alert"""
        pass
    
    @abstractmethod
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics and aggregations"""
        pass
    
    @abstractmethod
    async def get_alert_history(
        self,
        limit: int = 50,
        sensor_id: Optional[str] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alert history with optional filters"""
        pass
    
    @abstractmethod
    async def should_create_sensor_alert(
        self,
        alert_type: str,
        sensor_id: str,
        connection_threshold_minutes: int = 15
    ) -> tuple:
        """Determine if a sensor alert should be created"""
        pass


class ISensorService(ABC):
    """
    Sensor service interface
    Defines business logic operations for sensors
    """
    
    @abstractmethod
    def normalize_sensor_reading(self, reading: dict) -> dict:
        """Normalize sensor reading data to standard format"""
        pass
    
    @abstractmethod
    async def get_individual_sensor_data(
        self,
        sensor_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get individual sensor data with time range"""
        pass
    
    @abstractmethod
    async def get_latest_metrics(self) -> Dict[str, Any]:
        """Get latest metrics from all sensors"""
        pass
    
    @abstractmethod
    async def get_sensor_status(self) -> List[Dict[str, Any]]:
        """Get status of all sensors"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        sensor_ids: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Get historical data formatted for charts"""
        pass
    
    @abstractmethod
    async def is_sensor_connected(
        self,
        sensor_id: str,
        threshold_minutes: int = 5
    ) -> bool:
        """Check if a sensor is currently connected"""
        pass


class INotificationService(ABC):
    """
    Notification service interface
    Defines operations for sending notifications
    """
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        user_id: str,
        alert_type: str,
        sensor_id: str,
        location: str,
        title: str,
        value: str
    ) -> bool:
        """Send email notification with throttling"""
        pass
    
    @abstractmethod
    async def send_whatsapp(
        self,
        to_phone: str,
        user_id: str,
        alert_type: str,
        sensor_id: str,
        location: str,
        title: str,
        value: str
    ) -> bool:
        """Send WhatsApp notification with throttling"""
        pass
    
    @abstractmethod
    async def notify_admins(
        self,
        alert_data: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Send notifications to all admin users"""
        pass
    
    @abstractmethod
    async def clear_throttle_for_alert(self, alert_id: str) -> None:
        """Clear notification throttle for specific alert"""
        pass


class ICacheService(ABC):
    """
    Cache service interface
    Defines operations for caching
    """
    
    @abstractmethod
    async def connect(self, url: str) -> None:
        """Connect to cache backend"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from cache backend"""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
