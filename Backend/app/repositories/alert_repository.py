"""
Alert Repository
Data access layer for alerts collection
Implements IAlertRepository interface
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.config import alerts_collection, alert_history_collection
from .base_repository import BaseRepository
import logging
import asyncio

logger = logging.getLogger(__name__)


class AlertRepository(BaseRepository):
    """
    Repository for alert operations
    Implements the IAlertRepository interface
    """
    
    def __init__(self):
        super().__init__(alerts_collection)
        self.history_collection = alert_history_collection
    
    async def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active (unresolved) alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of active alert documents
        """
        return await self.find_many(
            query={"is_resolved": False},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    async def get_critical_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get critical level alerts
        
        Args:
            limit: Maximum number of alerts
            
        Returns:
            List of critical alerts
        """
        return await self.find_many(
            query={"level": {"$in": ["critical", "crítica", "crítico"]}},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    async def dismiss_alert(
        self, 
        alert_id: str, 
        dismissed_by: str,
        dismissed_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Mark alert as resolved/dismissed
        
        Args:
            alert_id: Alert ID
            dismissed_by: Email of user dismissing
            dismissed_at: Optional timestamp of dismissal (defaults to now)
            reason: Optional reason for dismissal
            
        Returns:
            True if successful
        """
        try:
            # Use provided timestamp or default to now (timezone-aware UTC)
            resolved_time = dismissed_at or datetime.now(timezone.utc)

            # Use find_by_id helper to correctly handle ObjectId or string id
            # normalize to string when passing to helper
            try:
                alert = await self.find_by_id(str(alert_id))
            except Exception:
                alert = None
            
            if not alert:
                return False
            
            # Update alert as resolved
            update = {
                "$set": {
                    "is_resolved": True,
                    "status": "dismissed",
                    "resolved_at": resolved_time,
                    "resolved_by": dismissed_by,
                    "dismissal_reason": reason
                }
            }
            
            success = await self.update_one(
                {"_id": alert.get("_id")},
                update
            )

            if success:
                # Schedule moving to history and deletion in background to keep API responsive.
                # Build the coroutine first and pass it to create_task; if scheduling fails
                # the created coroutine must be closed to avoid "coroutine was never awaited" warnings.
                coro = None
                try:
                    coro = self._async_move_and_delete(alert, dismissed_by, reason)
                    asyncio.create_task(coro)
                except Exception:
                    # If scheduling the background task failed, make sure to close the
                    # coroutine object to avoid resource warnings, then perform the
                    # move/delete synchronously as a fallback.
                    try:
                        if coro is not None:
                            coro.close()
                    except Exception:
                        logger.exception("Failed closing coroutine after create_task failure")

                    # Fallback to synchronous move if scheduling fails
                    await self._move_to_history(alert, dismissed_by, reason)
                    await self.delete_one({"_id": alert.get("_id")})
            
            return success
            
        except Exception as e:
            logger.error(f"Error dismissing alert {alert_id}: {e}")
            return False
    
    async def _move_to_history(
        self, 
        alert: Dict[str, Any],
        dismissed_by: str,
        reason: Optional[str]
    ) -> None:
        """Move dismissed alert to history collection"""
        try:
            current_time = datetime.now(timezone.utc)
            alert_id_str = str(alert.get("_id"))
            
            # Calculate duration if created_at exists
            duration_minutes = None
            created_at = alert.get("created_at")
            if created_at:
                if isinstance(created_at, datetime):
                    # If stored datetime is naive, assume UTC
                    if getattr(created_at, 'tzinfo', None) is None:
                        try:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                    try:
                        duration = current_time - created_at
                        duration_minutes = int(duration.total_seconds() / 60)
                    except Exception:
                        duration_minutes = None
            
            # Determine resolution type based on who dismissed
            resolution_type = "manual_dismiss"
            if dismissed_by in ("system_auto", "system@auto", "system"):
                resolution_type = "auto_resolved"
            
            history_doc = {
                "alert_id": alert_id_str,
                "type": alert.get("type"),
                "level": alert.get("level"),
                "title": alert.get("title"),
                "message": alert.get("message"),
                "value": alert.get("value"),
                "threshold_info": alert.get("threshold_info", ""),
                "location": alert.get("location", "Sistema de Riego"),
                "sensor_id": alert.get("sensor_id"),
                "created_at": (created_at if isinstance(created_at, datetime) else alert.get("created_at", current_time)),
                "resolved_at": alert.get("resolved_at", current_time),
                "dismissed_at": current_time,
                "dismissed_by": dismissed_by,
                "dismissed_by_role": alert.get("dismissed_by_role", "system" if dismissed_by.startswith("system") else "operario"),
                "resolution_type": resolution_type,
                "duration_minutes": duration_minutes,
                "dismissal_reason": reason,
                "archived_at": current_time
            }
            
            await self.history_collection.insert_one(history_doc)
            logger.info(f"Alert moved to history: {alert_id_str} ({resolution_type})")
            
        except Exception as e:
            logger.error(f"Error moving alert to history: {e}")
            import traceback
            traceback.print_exc()

    async def _async_move_and_delete(self, alert: Dict[str, Any], dismissed_by: str, reason: Optional[str]) -> None:
        """Background helper: move to history and delete the active alert."""
        try:
            await self._move_to_history(alert, dismissed_by, reason)
            await self.delete_one({"_id": alert.get("_id")})
        except Exception as e:
            logger.error(f"Background move/delete failed for alert {alert.get('_id')}: {e}")
    
    async def get_alerts_by_sensor(
        self, 
        sensor_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get alerts for specific sensor
        
        Args:
            sensor_id: Sensor identifier
            limit: Maximum alerts to return
            
        Returns:
            List of alerts
        """
        return await self.find_many(
            query={"sensor_id": sensor_id},
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def archive_measurement_alerts_for_sensor(self, sensor_id: str) -> int:
        """
        Archive (move to history) all unresolved measurement alerts for a sensor.

        Returns the number of archived alerts.
        """
        try:
            # Temporarily remove 'water_level' from measurement types while feature is disabled
            measurement_types = ['ph', 'ph_range', 'temperature', 'ec', 'conductivity']
            cursor = self.collection.find({
                'sensor_id': sensor_id,
                'type': {'$in': measurement_types},
                'is_resolved': False
            })

            to_archive = await cursor.to_list(length=None)
            count = 0
            for alert in to_archive:
                try:
                    # Mark as resolved and move to history
                    alert_id = alert.get('_id')
                    now = datetime.now(timezone.utc)
                    await self.update_one({'_id': alert_id}, {'$set': {
                        'is_resolved': True,
                        'status': 'auto_resolved',
                        'resolved_at': now,
                        'resolved_by': 'system',
                        'dismissal_reason': 'Sensor disconnected - auto-archived'
                    }})

                    # Move to history synchronously
                    await self._move_to_history(alert, 'system', 'Sensor disconnected - auto-archived')
                    await self.delete_one({'_id': alert_id})
                    count += 1
                except Exception:
                    logger.exception(f"Failed to archive alert {alert.get('_id')} for sensor {sensor_id}")
                    continue

            logger.info(f"Archived {count} measurement alerts for sensor {sensor_id}")
            return count
        except Exception as e:
            logger.error(f"Error archiving measurement alerts for sensor {sensor_id}: {e}")
            return 0
    
    async def get_alerts_history(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get alert history for specified days
        
        Args:
            days: Number of days to look back
            limit: Maximum alerts
            
        Returns:
            List of historical alerts
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = self.history_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)

    async def create_alert(self, alert_doc: Dict[str, Any]) -> Optional[str]:
        """
        Safely create an alert ensuring business rules are respected.

        - Ensures a `source` field exists (defaults to 'system').
        - For measurement alerts (ph, temperature, ec, water_level, conductivity)
          verifies that the sensor is connected before inserting.

        Returns the inserted document id as string or None if skipped/failed.
        """
        try:
            # Ensure source is present and not None
            if not alert_doc.get("source"):
                alert_doc["source"] = "system"

            # Measurement alert types require connected sensors
            measurement_types = ['ph', 'temperature', 'ec', 'water_level', 'conductivity']
            alert_type = (alert_doc.get('type') or '').lower()
            sensor_id = alert_doc.get('sensor_id')

            if alert_type in measurement_types:
                # measurement alerts must reference a sensor
                if not sensor_id:
                    logger.info(f"Skipping insertion of measurement alert without sensor_id: {alert_type}")
                    return None

                # Import here to avoid circular imports at module import time
                from app.services.sensor_service import sensor_service
                try:
                    is_connected = await sensor_service.is_sensor_connected(sensor_id)
                except Exception:
                    # If we cannot determine connection status, be conservative and skip
                    logger.exception('Failed to check sensor connection; skipping alert insertion')
                    return None

                if not is_connected:
                    logger.info(f"Skipping insertion of measurement alert for disconnected sensor {sensor_id}")
                    return None

                # Prevent duplicate unresolved measurement alerts for same sensor/type
                try:
                    existing = await self.collection.find_one({
                        'sensor_id': sensor_id,
                        'type': alert_doc.get('type'),
                        'is_resolved': False
                    })
                    if existing:
                        logger.info(f"Similar unresolved alert already exists for {sensor_id} ({alert_doc.get('type')}); skipping insert")
                        return None
                except Exception:
                    logger.exception('Failed checking for existing alerts; continuing')

            # Insert using base repository insert (returns string id)
            return await self.insert_one(alert_doc)
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None


# Singleton instance
alert_repository = AlertRepository()
