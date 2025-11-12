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
        reason: Optional[str] = None
    ) -> bool:
        """
        Mark alert as resolved/dismissed
        
        Args:
            alert_id: Alert ID
            dismissed_by: Email of user dismissing
            reason: Optional reason for dismissal
            
        Returns:
            True if successful
        """
        try:
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
                    "resolved_at": datetime.utcnow(),
                    "resolved_by": dismissed_by,
                    "dismissal_reason": reason
                }
            }
            
            success = await self.update_one(
                {"_id": alert.get("_id")},
                update
            )
            
            if success:
                # Move to history
                await self._move_to_history(alert, dismissed_by, reason)
            
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
            history_doc = {
                **alert,
                "dismissed_at": datetime.utcnow(),
                "dismissed_by": dismissed_by,
                "dismissal_reason": reason,
                "archived_at": datetime.utcnow()
            }
            
            # Remove _id for new insert
            history_doc.pop("_id", None)
            
            await self.history_collection.insert_one(history_doc)
            logger.info(f"Alert moved to history: {alert.get('id')}")
            
        except Exception as e:
            logger.error(f"Error moving alert to history: {e}")
    
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
