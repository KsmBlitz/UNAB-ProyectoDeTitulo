"""
Sensor Repository
Data access layer for sensors
Implements ISensorRepository interface
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.config.database import db
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class SensorRepository(BaseRepository):
    """
    Repository for sensor operations
    Implements the ISensorRepository interface
    """
    
    def __init__(self):
        sensors_collection = db["sensors"]
        super().__init__(sensors_collection)
        self.sensor_data_collection = db["Sensor_Data"]
    
    async def find_by_sensor_id(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Find sensor by sensor_id field (interface method)
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Sensor document or None
        """
        return await self.find_one({"sensor_id": sensor_id})
    
    # Alias for backwards compatibility
    async def get_sensor_by_id(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Alias for find_by_sensor_id"""
        return await self.find_by_sensor_id(sensor_id)
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        """
        Get all active sensors (interface method)
        
        Returns:
            List of active sensor documents
        """
        # Return all sensors - filter for active status if status field exists
        return await self.find_many(
            {"$or": [
                {"status": "connected"},
                {"status": {"$exists": False}}
            ]},
            limit=1000
        )
    
    async def get_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Get all registered sensors
        
        Returns:
            List of sensor documents
        """
        return await self.find_many({}, limit=1000)
    
    async def update_connection_status(
        self,
        sensor_id: str,
        connected: bool
    ) -> bool:
        """
        Update sensor connection status (interface method)
        
        Args:
            sensor_id: Sensor identifier
            connected: Whether sensor is connected
            
        Returns:
            True if updated successfully
        """
        try:
            status = "connected" if connected else "disconnected"
            return await self.update_one(
                {"sensor_id": sensor_id},
                {
                    "$set": {
                        "status": status,
                        "connection_status": status,
                        "last_status_update": datetime.now(timezone.utc),
                        "last_seen": datetime.now(timezone.utc) if connected else None
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating connection status for {sensor_id}: {e}")
            return False
    
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
                        "updated_at": datetime.now(timezone.utc)
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
            now = datetime.now(timezone.utc)
            sensor_data["created_at"] = now
            sensor_data["updated_at"] = now
            sensor_data["status"] = sensor_data.get("status", "disconnected")
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
    
    async def get_latest_reading(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent reading for a sensor
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Most recent data document or None
        """
        try:
            cursor = self.sensor_data_collection.find({
                "SensorID": sensor_id
            }).sort("ProcessedAt", -1).limit(1)
            
            results = await cursor.to_list(length=1)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting latest reading for {sensor_id}: {e}")
            return None


# Singleton instance
sensor_repository = SensorRepository()
