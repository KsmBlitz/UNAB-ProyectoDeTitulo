"""
Alert Service - Business Logic Layer
Handles alert operations following SOLID principles
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from bson import ObjectId

from app.repositories.alert_repository import alert_repository
from app.repositories.sensor_repository import sensor_repository
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service layer for alert business logic
    
    Responsibilities:
    - Alert lifecycle management (create, dismiss, resolve)
    - Business rules enforcement
    - Alert statistics and aggregation
    - Coordination with notification service
    """
    
    def __init__(
        self,
        alert_repo=None,
        sensor_repo=None,
        notif_service=None
    ):
        """Initialize with repositories (dependency injection for testability)"""
        self.alert_repo = alert_repo or alert_repository
        self.sensor_repo = sensor_repo or sensor_repository
        self.notif_service = notif_service or notification_service
    
    async def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active (unresolved) alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of active alert dictionaries
        """
        try:
            alerts = await self.alert_repo.get_active_alerts(limit=limit)
            logger.info(f"Retrieved {len(alerts)} active alerts")
            return alerts
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            raise
    
    async def get_critical_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get critical level alerts only
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of critical alert dictionaries
        """
        try:
            alerts = await self.alert_repo.get_critical_alerts(limit=limit)
            logger.info(f"Retrieved {len(alerts)} critical alerts")
            return alerts
        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}")
            raise
    
    async def dismiss_alert(
        self,
        alert_id: str,
        user_email: str,
        user_role: str = "operario",
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dismiss/close an alert and move to history
        
        Business logic:
        1. Validate alert exists and is not already resolved
        2. Mark as resolved with user and timestamp info
        3. Calculate duration and move to history
        4. Clear notification throttling for this alert
        5. Return dismissal confirmation
        
        Args:
            alert_id: Alert identifier (can be _id or custom id field)
            user_email: Email of user dismissing the alert
            user_role: Role of user (operario, admin)
            reason: Optional reason for dismissal
            ip_address: Optional IP address for audit trail
            
        Returns:
            Dictionary with dismissal confirmation
            
        Raises:
            ValueError: If alert not found or already resolved
            RuntimeError: If dismissal fails
        """
        try:
            logger.info(f"Attempting to dismiss alert {alert_id} by {user_email}")
            
            # Validate alert exists and get full document
            alert_doc = await self._find_alert_by_id(alert_id)
            
            if not alert_doc:
                raise ValueError(f"Alert not found: {alert_id}")
            
            # Check if already resolved
            if alert_doc.get("is_resolved", False):
                raise ValueError("Alert is already resolved")
            
            current_time = datetime.now(timezone.utc)
            
            # Use repository to dismiss alert
            result = await self.alert_repo.dismiss_alert(
                alert_id=alert_doc["_id"],
                dismissed_by=user_email,
                dismissed_at=current_time,
                reason=reason
            )
            
            if not result:
                raise RuntimeError("Failed to dismiss alert")
            
            # Clear notification throttling
            await self._clear_alert_notifications(alert_doc)
            
            logger.info(f"Alert {alert_id} dismissed by {user_email} ({user_role})")
            
            return {
                "message": "Alert dismissed successfully",
                "alert_id": str(alert_id),
                "dismissed_at": current_time.isoformat(),
                "dismissed_by": user_email
            }
            
        except ValueError as ve:
            logger.warning(f"Validation error dismissing alert: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error dismissing alert {alert_id}: {e}")
            raise RuntimeError(f"Failed to dismiss alert: {e}")
    
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get alert statistics and aggregations
        
        Returns:
            Dictionary with:
            - total_active: Count of active alerts
            - by_level: Counts grouped by severity level
            - by_type: Counts grouped by alert type
            - critical_count: Count of critical alerts
        """
        try:
            from app.config import alerts_collection
            
            # Count active alerts
            total_active = await alerts_collection.count_documents({"is_resolved": False})
            
            # Count by level
            pipeline_level = [
                {"$match": {"is_resolved": False}},
                {"$group": {"_id": "$level", "count": {"$sum": 1}}}
            ]
            level_counts = await alerts_collection.aggregate(pipeline_level).to_list(length=None)
            by_level = {item["_id"]: item["count"] for item in level_counts}
            
            # Count by type
            pipeline_type = [
                {"$match": {"is_resolved": False}},
                {"$group": {"_id": "$type", "count": {"$sum": 1}}}
            ]
            type_counts = await alerts_collection.aggregate(pipeline_type).to_list(length=None)
            by_type = {item["_id"]: item["count"] for item in type_counts}
            
            # Critical alerts
            critical_count = by_level.get("critical", 0) + by_level.get("crítica", 0) + by_level.get("crítico", 0)
            
            return {
                "total_active": total_active,
                "by_level": by_level,
                "by_type": by_type,
                "critical_count": critical_count
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            raise
    
    async def get_alert_history(
        self,
        limit: int = 50,
        sensor_id: Optional[str] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alert history with optional filters
        
        Args:
            limit: Maximum records to return
            sensor_id: Filter by sensor (optional)
            alert_type: Filter by alert type (optional)
            
        Returns:
            List of historical alert dictionaries
        """
        try:
            from app.config import alert_history_collection
            
            # Build filter
            query_filter = {}
            if sensor_id:
                query_filter["sensor_id"] = sensor_id
            if alert_type:
                query_filter["type"] = alert_type
            
            # Query history
            cursor = alert_history_collection.find(query_filter)\
                .sort("dismissed_at", -1)\
                .limit(limit)
            
            history_list = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for item in history_list:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
            
            logger.info(f"Retrieved {len(history_list)} history records")
            return history_list
            
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            raise
    
    # Private helper methods
    
    async def _find_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Find alert by ID (supports both _id and custom id field)
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            Alert document or None
        """
        from app.config import alerts_collection
        
        # Try to find by either _id or id field
        alert_doc = await alerts_collection.find_one({
            "$or": [
                {"_id": alert_id},
                {"id": alert_id}
            ]
        })
        
        return alert_doc
    
    async def _clear_alert_notifications(self, alert_doc: Dict[str, Any]) -> None:
        """
        Clear notification throttling for dismissed alert
        
        Args:
            alert_doc: Alert document with type and sensor_id
        """
        try:
            alert_type = alert_doc.get("type")
            sensor_id = alert_doc.get("sensor_id")
            
            if alert_type and sensor_id:
                # Clear throttling in notification service
                self.notif_service.clear_throttle_for_alert(
                    alert_type=alert_type,
                    sensor_id=sensor_id
                )
                logger.debug(f"Cleared notification throttle for {alert_type}/{sensor_id}")
                
        except Exception as e:
            logger.warning(f"Error clearing notification throttle: {e}")
            # Don't fail dismissal due to throttle clearing error
    
    async def create_manual_alert(
        self,
        alert_type: str,
        level: str,
        title: str,
        message: str,
        location: str,
        created_by: str,
        sensor_id: Optional[str] = None,
        value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a manual alert (triggered by user, not sensor)
        
        Args:
            alert_type: Type of alert (temperature, ph, etc)
            level: Severity level (info, warning, critical)
            title: Alert title
            message: Detailed message
            location: Location/sensor location
            created_by: Email of user creating alert
            sensor_id: Optional sensor identifier
            value: Optional sensor value
            
        Returns:
            Created alert dictionary
        """
        try:
            from app.config import alerts_collection
            
            current_time = datetime.now(timezone.utc)
            
            alert_doc = {
                "type": alert_type,
                "level": level.lower(),
                "title": title,
                "message": message,
                "location": location,
                "created_at": current_time,
                "created_by": created_by,
                "is_resolved": False,
                "status": "active",
                "source": "manual"
            }
            
            # Optional fields
            if sensor_id:
                alert_doc["sensor_id"] = sensor_id
            if value is not None:
                alert_doc["value"] = value
            
            result = await alerts_collection.insert_one(alert_doc)
            alert_doc["_id"] = result.inserted_id
            alert_doc["id"] = str(result.inserted_id)
            
            logger.info(f"Manual alert created by {created_by}: {title}")
            
            # Notify admins if critical
            if level.lower() in ["critical", "crítica", "crítico"]:
                await self._notify_critical_alert(alert_doc)
            
            return alert_doc
            
        except Exception as e:
            logger.error(f"Error creating manual alert: {e}")
            raise
    
    async def _notify_critical_alert(self, alert_doc: Dict[str, Any]) -> None:
        """
        Send notifications for critical alert
        
        Args:
            alert_doc: Alert document
        """
        try:
            await self.notif_service.notify_admins(
                alert_type=alert_doc.get("type"),
                sensor_id=alert_doc.get("sensor_id"),
                location=alert_doc.get("location", "Unknown"),
                title=alert_doc.get("title", "Critical Alert"),
                value=str(alert_doc.get("value", "N/A"))
            )
            logger.info(f"Sent critical alert notifications for {alert_doc.get('title')}")
        except Exception as e:
            logger.error(f"Error sending critical alert notifications: {e}")
            # Don't fail alert creation due to notification error
    
    async def should_create_sensor_alert(
        self,
        alert_type: str,
        sensor_id: str,
        connection_threshold_minutes: int = 15
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if a sensor alert should be created based on sensor connection status
        
        Business rules:
        - Sensor measurement alerts (pH, temperature, EC, water_level) should only be
          created if the sensor is connected (has recent data)
        - Sensor disconnection alerts should only be created if sensor is actually disconnected
        
        Args:
            alert_type: Type of alert ('ph', 'temperature', 'ec', 'water_level', 'sensor_disconnected')
            sensor_id: Sensor identifier
            connection_threshold_minutes: Minutes to consider sensor as connected
            
        Returns:
            Tuple of (should_create: bool, reason: Optional[str])
            - should_create: True if alert should be created
            - reason: Explanation if alert should NOT be created
        """
        try:
            # Import sensor service to check connection status
            from app.services.sensor_service import sensor_service
            
            is_connected = await sensor_service.is_sensor_connected(
                sensor_id=sensor_id,
                threshold_minutes=connection_threshold_minutes
            )
            
            # Measurement alerts (pH, temp, EC, water_level) require connected sensor
            measurement_alert_types = ['ph', 'temperature', 'ec', 'water_level', 'conductivity']
            
            if alert_type.lower() in measurement_alert_types:
                if not is_connected:
                    reason = (
                        f"Sensor {sensor_id} is disconnected - skipping {alert_type} alert. "
                        f"Measurement alerts only created for connected sensors."
                    )
                    logger.info(reason)
                    return False, reason
                else:
                    logger.debug(f"Sensor {sensor_id} is connected - {alert_type} alert allowed")
                    return True, None
            
            # Disconnection alerts only for actually disconnected sensors
            elif alert_type.lower() in ['sensor_disconnected', 'disconnected', 'offline']:
                if is_connected:
                    reason = f"Sensor {sensor_id} is still connected - not creating disconnection alert"
                    logger.debug(reason)
                    return False, reason
                else:
                    logger.info(f"Sensor {sensor_id} is disconnected - disconnection alert allowed")
                    return True, None
            
            # Other alert types (manual, system, etc) - always allow
            else:
                logger.debug(f"Alert type '{alert_type}' is not sensor-dependent - always allowed")
                return True, None
                
        except Exception as e:
            logger.error(f"Error checking if alert should be created: {e}")
            # On error, allow alert creation (fail open)
            return True, None


# Singleton instance
alert_service = AlertService()
