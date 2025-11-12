"""
Sensor Repository
Data access layer for sensors
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.config import db
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class SensorRepository(BaseRepository):
    """Repository for sensor operations"""
    
    def __init__(self):
        sensors_collection = db["sensors"]
        super().__init__(sensors_collection)
        self.sensor_data_collection = db["Sensor_Data"]
    
    async def get_sensor_by_id(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sensor by sensor_id field
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Sensor document or None
        """
        return await self.find_one({"sensor_id": sensor_id})
    
    async def get_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Get all registered sensors
        
        Returns:
            List of sensor documents
        """
        return await self.find_many({}, limit=1000)
    
    async def update_sensor_alert_config(
        self,
        sensor_id: str,
        alert_config: Dict[str, Any]
    ) -> bool:
        """
        Update alert configuration for a sensor
        
        Args:
            sensor_id: Sensor identifier
            alert_config: New alert configuration
            
        Returns:
            True if updated successfully
        """
        try:
            return await self.update_one(
                {"sensor_id": sensor_id},
                {
                    "$set": {
                        "alert_config": alert_config,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating sensor alert config: {e}")
            return False
    
    async def create_sensor(self, sensor_data: Dict[str, Any]) -> Optional[str]:
        """
        Create new sensor
        
        Args:
            sensor_data: Sensor data including sensor_id, name, etc.
            
        Returns:
            Inserted document ID or None
        """
        try:
            sensor_data["created_at"] = datetime.utcnow()
            sensor_data["updated_at"] = datetime.utcnow()
            return await self.insert_one(sensor_data)
        except Exception as e:
            logger.error(f"Error creating sensor: {e}")
            return None
    
    async def get_sensor_data(
        self,
        sensor_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent data readings for a sensor
        
        Args:
            sensor_id: Sensor identifier (SensorID field)
            limit: Maximum readings to return
            
        Returns:
            List of sensor data documents
        """
        try:
            cursor = self.sensor_data_collection.find({
                "SensorID": sensor_id
            }).sort("ProcessedAt", -1).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting sensor data: {e}")
            return []
    
    async def get_sensors_with_alert_config(self) -> List[Dict[str, Any]]:
        """
        Get sensors that have alert configuration enabled
        
        Returns:
            List of sensors with alert config
        """
        return await self.find_many(
            {"alert_config.enabled": True},
            limit=1000
        )


# Singleton instance
sensor_repository = SensorRepository()
