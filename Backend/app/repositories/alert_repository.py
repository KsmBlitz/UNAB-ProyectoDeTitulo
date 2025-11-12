"""
Alert Repository
Data access layer for alerts collection
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.config import alerts_collection, alert_history_collection
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class AlertRepository(BaseRepository):
    """Repository for alert operations"""
    
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
            # Use provided timestamp or default to now
            resolved_time = dismissed_at or datetime.utcnow()
            
            # Find alert by ID or _id
            alert = await self.find_one({
                "$or": [
                    {"_id": alert_id},
                    {"id": alert_id}
                ]
            })
            
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
                # Move to history and delete from active alerts
                await self._move_to_history(alert, dismissed_by, reason)
                # Delete from active alerts collection
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
            current_time = datetime.utcnow()
            alert_id_str = str(alert.get("_id"))
            
            # Calculate duration if created_at exists
            duration_minutes = None
            if alert.get("created_at"):
                created_at = alert.get("created_at")
                if isinstance(created_at, datetime):
                    duration = current_time - created_at
                    duration_minutes = int(duration.total_seconds() / 60)
            
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
                "created_at": alert.get("created_at", current_time),
                "resolved_at": alert.get("resolved_at", current_time),
                "dismissed_at": current_time,
                "dismissed_by": dismissed_by,
                "dismissed_by_role": alert.get("dismissed_by_role", "operario"),
                "resolution_type": "manual_dismiss",
                "duration_minutes": duration_minutes,
                "dismissal_reason": reason,
                "archived_at": current_time
            }
            
            await self.history_collection.insert_one(history_doc)
            logger.info(f"Alert moved to history: {alert_id_str}")
            
        except Exception as e:
            logger.error(f"Error moving alert to history: {e}")
            import traceback
            traceback.print_exc()
    
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
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor = self.history_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)


# Singleton instance
alert_repository = AlertRepository()
