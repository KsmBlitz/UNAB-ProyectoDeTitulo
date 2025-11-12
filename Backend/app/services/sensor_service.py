"""
Sensor Service - Business Logic Layer
Handles sensor operations, data processing, and predictions
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from app.repositories.sensor_repository import sensor_repository
from app.services.prediction import predict_sensor_values

logger = logging.getLogger(__name__)

# Timezone offset for Chile (UTC-3)
CHILE_OFFSET = timedelta(hours=-3)


class SensorService:
    """
    Service layer for sensor business logic
    
    Responsibilities:
    - Sensor data retrieval and processing
    - Sensor status management
    - Alert configuration
    - Predictions and analytics
    """
    
    def __init__(self, sensor_repo=None):
        """Initialize with sensor repository (dependency injection for testability)"""
        self.sensor_repo = sensor_repo or sensor_repository
    
    def normalize_sensor_reading(self, reading: dict) -> dict:
        """
        Normalize sensor reading data
        
        Ensures consistent field names and data types across different
        sensor configurations and IoT message formats.
        
        Args:
            reading: Raw sensor reading dictionary
            
        Returns:
            Normalized reading dictionary
        """
        normalized = reading.copy()
        
        # Map common field variations to standard names
        field_mappings = {
            'ph': ['pH', 'PH'],
            'temperature': ['temp', 'TEMP', 'Temperature'],
            'ec': ['EC', 'conductivity', 'Conductivity'],
            'water_level': ['waterLevel', 'water_level', 'nivel_agua']
        }
        
        for standard_field, variations in field_mappings.items():
            if standard_field not in normalized:
                for variation in variations:
                    if variation in normalized:
                        normalized[standard_field] = normalized[variation]
                        break
        
        # Ensure timestamp is present
        if 'timestamp' not in normalized and 'created_at' in normalized:
            normalized['timestamp'] = normalized['created_at']
        
        return normalized
    
    async def get_individual_sensor_data(
        self,
        sensor_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get individual sensor data with time range
        
        Args:
            sensor_id: Sensor identifier
            hours: Number of hours of historical data
            limit: Maximum number of readings
            
        Returns:
            List of normalized sensor readings
        """
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # Get data from repository
            readings = await self.sensor_repo.get_sensor_data(
                sensor_id=sensor_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            # Normalize readings
            normalized_readings = [
                self.normalize_sensor_reading(reading)
                for reading in readings
            ]
            
            logger.info(f"Retrieved {len(normalized_readings)} readings for sensor {sensor_id}")
            return normalized_readings
            
        except Exception as e:
            logger.error(f"Error getting sensor data for {sensor_id}: {e}")
            raise
    
    async def get_latest_metrics(self) -> Dict[str, Any]:
        """
        Get latest metrics from all sensors
        
        Returns:
            Dictionary with latest readings for each sensor
        """
        try:
            from app.config import sensor_collection
            
            # Get latest reading from each sensor
            latest_readings = {}
            
            # Query sensor_collection for latest data
            cursor = sensor_collection.find().sort("timestamp", -1).limit(10)
            readings = await cursor.to_list(length=10)
            
            for reading in readings:
                sensor_id = reading.get("sensor_id") or reading.get("device_id")
                if sensor_id:
                    normalized = self.normalize_sensor_reading(reading)
                    latest_readings[sensor_id] = normalized
            
            logger.info(f"Retrieved latest metrics for {len(latest_readings)} sensors")
            return latest_readings
            
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            raise
    
    async def get_sensor_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all sensors (online/offline based on last reading)
        
        Returns:
            List of sensor status dictionaries
        """
        try:
            sensors = await self.sensor_repo.get_all_sensors()
            
            sensor_status_list = []
            for sensor in sensors:
                sensor_id = sensor.get("sensor_id")
                
                # Get latest reading
                latest_readings = await self.sensor_repo.get_sensor_data(
                    sensor_id=sensor_id,
                    limit=1
                )
                
                if latest_readings:
                    latest = latest_readings[0]
                    last_reading_time = latest.get("timestamp") or latest.get("created_at")
                    
                    # Check if sensor is online (reading within last hour)
                    if isinstance(last_reading_time, str):
                        last_reading_time = datetime.fromisoformat(last_reading_time.replace('Z', '+00:00'))
                    
                    time_diff = datetime.now(timezone.utc) - last_reading_time
                    is_online = time_diff < timedelta(hours=1)
                    
                    status = {
                        "sensor_id": sensor_id,
                        "name": sensor.get("name", sensor_id),
                        "location": sensor.get("location", "Unknown"),
                        "is_online": is_online,
                        "last_reading": last_reading_time.isoformat(),
                        "minutes_since_last_reading": int(time_diff.total_seconds() / 60)
                    }
                else:
                    status = {
                        "sensor_id": sensor_id,
                        "name": sensor.get("name", sensor_id),
                        "location": sensor.get("location", "Unknown"),
                        "is_online": False,
                        "last_reading": None,
                        "minutes_since_last_reading": None
                    }
                
                sensor_status_list.append(status)
            
            logger.info(f"Retrieved status for {len(sensor_status_list)} sensors")
            return sensor_status_list
            
        except Exception as e:
            logger.error(f"Error getting sensor status: {e}")
            raise
    
    async def get_historical_data(
        self,
        sensor_ids: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical data for multiple sensors
        
        Args:
            sensor_ids: List of sensor IDs (None = all sensors)
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum readings per sensor
            
        Returns:
            Dictionary mapping sensor_id to list of readings
        """
        try:
            # Default time range: last 24 hours
            if not end_time:
                end_time = datetime.now(timezone.utc)
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Get sensors to query
            if not sensor_ids:
                sensors = await self.sensor_repo.get_all_sensors()
                sensor_ids = [s.get("sensor_id") for s in sensors if s.get("sensor_id")]
            
            # Get data for each sensor
            historical_data = {}
            for sensor_id in sensor_ids:
                readings = await self.sensor_repo.get_sensor_data(
                    sensor_id=sensor_id,
                    start_time=start_time,
                    end_time=end_time,
                    limit=limit
                )
                
                normalized_readings = [
                    self.normalize_sensor_reading(r)
                    for r in readings
                ]
                
                historical_data[sensor_id] = normalized_readings
            
            logger.info(f"Retrieved historical data for {len(historical_data)} sensors")
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            raise
    
    async def predict_sensor_value(
        self,
        sensor_type: str,
        sensor_id: Optional[str] = None,
        hours_ahead: int = 6
    ) -> Dict[str, Any]:
        """
        Generate predictions for sensor values
        
        Args:
            sensor_type: Type of sensor (ph, temperature, ec, water_level)
            sensor_id: Optional specific sensor ID
            hours_ahead: Hours to predict ahead
            
        Returns:
            Dictionary with predictions and confidence intervals
        """
        try:
            # Get historical data for prediction
            if sensor_id:
                historical = await self.get_individual_sensor_data(
                    sensor_id=sensor_id,
                    hours=168,  # 7 days
                    limit=500
                )
            else:
                # Use all sensors
                historical_dict = await self.get_historical_data(
                    start_time=datetime.now(timezone.utc) - timedelta(days=7),
                    limit=500
                )
                historical = []
                for readings in historical_dict.values():
                    historical.extend(readings)
            
            # Extract values for the sensor type
            values = []
            timestamps = []
            
            for reading in historical:
                if sensor_type in reading and reading[sensor_type] is not None:
                    values.append(float(reading[sensor_type]))
                    timestamp = reading.get("timestamp") or reading.get("created_at")
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamps.append(timestamp)
            
            if len(values) < 10:
                raise ValueError(f"Insufficient data for prediction: only {len(values)} readings")
            
            # Call prediction service
            predictions = await predict_sensor_values(
                sensor_type=sensor_type,
                historical_values=values,
                timestamps=timestamps,
                hours_ahead=hours_ahead
            )
            
            logger.info(f"Generated predictions for {sensor_type}")
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting sensor value for {sensor_type}: {e}")
            raise
    
    async def update_sensor_alert_config(
        self,
        sensor_id: str,
        alert_config: Dict[str, Any],
        updated_by: str
    ) -> Dict[str, Any]:
        """
        Update alert configuration for a sensor
        
        Args:
            sensor_id: Sensor identifier
            alert_config: New alert configuration
            updated_by: Email of user making the update
            
        Returns:
            Updated sensor configuration
            
        Raises:
            ValueError: If sensor not found or config invalid
        """
        try:
            # Validate sensor exists
            sensor = await self.sensor_repo.get_sensor_by_id(sensor_id)
            if not sensor:
                raise ValueError(f"Sensor not found: {sensor_id}")
            
            # Validate alert config structure
            self._validate_alert_config(alert_config)
            
            # Update configuration
            updated_sensor = await self.sensor_repo.update_sensor_alert_config(
                sensor_id=sensor_id,
                alert_config=alert_config
            )
            
            if not updated_sensor:
                raise RuntimeError("Failed to update sensor alert configuration")
            
            logger.info(f"Alert config updated for sensor {sensor_id} by {updated_by}")
            return updated_sensor
            
        except ValueError as ve:
            logger.warning(f"Validation error updating alert config: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error updating alert config for {sensor_id}: {e}")
            raise RuntimeError(f"Failed to update alert config: {e}")
    
    def _validate_alert_config(self, config: Dict[str, Any]) -> None:
        """
        Validate alert configuration structure
        
        Args:
            config: Alert configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ["alerts_enabled"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate threshold ranges if present
        if "thresholds" in config:
            thresholds = config["thresholds"]
            for metric, threshold in thresholds.items():
                if isinstance(threshold, dict):
                    if "min" in threshold and "max" in threshold:
                        if threshold["min"] >= threshold["max"]:
                            raise ValueError(f"Invalid range for {metric}: min must be < max")
    
    async def get_sensor_alert_config(self, sensor_id: str) -> Dict[str, Any]:
        """
        Get alert configuration for a specific sensor
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Alert configuration dictionary
            
        Raises:
            ValueError: If sensor not found
        """
        try:
            sensor = await self.sensor_repo.get_sensor_by_id(sensor_id)
            if not sensor:
                raise ValueError(f"Sensor not found: {sensor_id}")
            
            # Return alert configuration or defaults
            alert_config = sensor.get("alert_config", {
                "alerts_enabled": False,
                "thresholds": {}
            })
            
            return {
                "sensor_id": sensor_id,
                "alert_config": alert_config
            }
            
        except ValueError as ve:
            logger.warning(f"Validation error getting alert config: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error getting alert config for {sensor_id}: {e}")
            raise


# Singleton instance
sensor_service = SensorService()
