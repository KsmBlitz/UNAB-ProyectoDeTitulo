"""
Sensor Service - Business Logic Layer
Handles sensor operations, data processing, and predictions
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from bson import ObjectId

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
        # Cache for resolved reservoir ids: sensor_id -> reservoirId
        self._reservoir_id_cache = {}

    async def resolve_reservoir_id(self, sensor_id: str) -> Optional[str]:
        """Resolve a deterministic reservoirId for a given sensor_id.

        Strategy:
        - Check in-memory cache.
        - Query the `sensors` collection for a `reservoir_id`/`reservoirId` field.
        - Fallback: query `Sensor_Data` for documents that reference the sensor_id
          (SensorID, sensor_id, raw.SensorID) and return the most recent reservoirId.
        """
        if not sensor_id:
            return None

        # Check cache first
        if sensor_id in self._reservoir_id_cache:
            return self._reservoir_id_cache[sensor_id]

        try:
            # Try sensors collection via repository
            sensor_doc = await self.sensor_repo.get_sensor_by_id(sensor_id)
            if sensor_doc:
                for key in ("reservoir_id", "reservoirId", "reservoir"):
                    if key in sensor_doc and sensor_doc.get(key):
                        self._reservoir_id_cache[sensor_id] = sensor_doc.get(key)
                        return sensor_doc.get(key)

            # Fallback: look into Sensor_Data for any recent document referencing this sensor_id
            from app.config.database import db
            sensor_data_collection = db["Sensor_Data"]

            or_clauses = [
                {"SensorID": sensor_id},
                {"sensor_id": sensor_id},
                {"reservoirId": sensor_id},
                {"reservoir_id": sensor_id},
                {"raw.SensorID": sensor_id},
            ]

            doc = await sensor_data_collection.find_one({"$or": or_clauses}, sort=[("ReadTime", -1)])
            if doc:
                reservoir = doc.get('reservoirId') or doc.get('reservoir_id')
                if reservoir:
                    self._reservoir_id_cache[sensor_id] = reservoir
                    return reservoir

        except Exception as e:
            logger.debug(f"resolve_reservoir_id fallback failed for {sensor_id}: {e}")

        # No mapping found
        return None
    
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
        
        # Convert MongoDB ObjectId to string for JSON serialization
        if '_id' in normalized:
            if isinstance(normalized['_id'], ObjectId):
                normalized['_id'] = str(normalized['_id'])
        
        # Map common field variations to standard names
        field_mappings = {
            'ph': ['pH', 'PH', 'pH_Value'],
            'temperature': ['temp', 'TEMP', 'Temperature'],
            'ec': ['EC', 'conductivity', 'Conductivity'],
            'water_level': ['waterLevel', 'water_level', 'Water_Level', 'nivel_agua']
        }
        
        for standard_field, variations in field_mappings.items():
            if standard_field not in normalized:
                for variation in variations:
                    if variation in normalized:
                        normalized[standard_field] = normalized[variation]
                        break
        
        # Ensure timestamp is present - try multiple sources
        if 'timestamp' not in normalized:
            if 'ReadTime' in normalized:
                normalized['timestamp'] = normalized['ReadTime']
            elif 'created_at' in normalized:
                normalized['timestamp'] = normalized['created_at']
            else:
                normalized['timestamp'] = None
        
        # Set default values for missing fields
        for field in ['ph', 'temperature', 'ec', 'water_level']:
            if field not in normalized:
                normalized[field] = 0
        
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
            Dictionary with latest sensor readings in the format expected by frontend:
            {
                "temperature": float,
                "ph": float,
                "conductivity": float (EC),
                "water_level": float,
                "timestamp": datetime,
                "sensor_id": str
            }
        """
        try:
            from app.config.database import db
            sensor_data_collection = db["Sensor_Data"]
            
            # Get the most recent reading from any sensor
            latest_reading = await sensor_data_collection.find_one(
                sort=[("ReadTime", -1)]
            )
            
            if not latest_reading:
                logger.warning("No sensor data found in database")
                return {
                    "temperature": 0,
                    "ph": 0,
                    "conductivity": 0,
                    "water_level": 0,
                    "timestamp": None,
                    "sensor_id": None
                }
            
            # Normalize the reading
            normalized = self.normalize_sensor_reading(latest_reading)
            
            # Build response in frontend-expected format
            response = {
                "temperature": normalized.get("temperature", 0),
                "ph": normalized.get("ph", 0),
                "conductivity": normalized.get("ec", 0),  # EC maps to conductivity
                "water_level": normalized.get("water_level", 0),
                "timestamp": normalized.get("timestamp"),
                "sensor_id": latest_reading.get("reservoirId", latest_reading.get("sensor_id"))
            }
            
            logger.info(f"Retrieved latest metrics for sensor {response['sensor_id']}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            raise
    
    async def get_sensor_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all sensors (online/offline based on last reading)
        
        Returns:
            List of sensor status dictionaries with format expected by frontend
        """
        try:
            from app.config.database import db
            sensor_data_collection = db["Sensor_Data"]
            current_time = datetime.now(timezone.utc)
            
            # Get unique sensors and their latest readings using aggregation
            pipeline = [
                {"$sort": {"ReadTime": -1}},
                {"$group": {
                    "_id": "$reservoirId",
                    "lastReading": {"$first": "$$ROOT"}
                }},
                {"$limit": 20}
            ]
            
            db_sensors = await sensor_data_collection.aggregate(pipeline).to_list(length=None)
            sensor_status_list = []
            
            for sensor_group in db_sensors:
                reservoir_id = sensor_group["_id"]
                latest_reading = sensor_group["lastReading"]
                
                # Normalize data
                normalized = self.normalize_sensor_reading(latest_reading)
                
                # Get timestamp
                last_reading_time = normalized["timestamp"]
                if last_reading_time and last_reading_time.tzinfo is None:
                    last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
                
                # Calculate time difference
                if last_reading_time:
                    time_diff = (current_time - last_reading_time).total_seconds()
                    minutes_diff = time_diff / 60
                else:
                    minutes_diff = 999999
                
                # Determine status
                if minutes_diff < 15:
                    status_label = "online"
                elif minutes_diff < 30:
                    status_label = "warning"
                else:
                    status_label = "offline"
                
                sensor_data = {
                    "uid": reservoir_id,
                    "last_values": {
                        "temperature": round(normalized["temperature"], 1) if normalized["temperature"] is not None and normalized["temperature"] != 0 else normalized["temperature"],
                        "ph": round(normalized["ph"], 2) if normalized["ph"] is not None and normalized["ph"] != 0 else normalized["ph"],
                        "ec": round(normalized["ec"], 1) if normalized["ec"] is not None and normalized["ec"] != 0 else normalized["ec"],
                        "water_level": round(normalized["water_level"], 1) if normalized["water_level"] is not None and normalized["water_level"] != 0 else normalized["water_level"]
                    },
                    "status": status_label,
                    "location": f"Embalse {reservoir_id}",
                    "last_reading": last_reading_time.isoformat() if last_reading_time else None,
                    "minutes_since_reading": int(minutes_diff)
                }
                
                sensor_status_list.append(sensor_data)
            
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
    ) -> Dict[str, Any]:
        """
        Get historical data formatted for charts
        
        Args:
            sensor_ids: List of reservoir IDs (None = all sensors)
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum readings
            
        Returns:
            Dictionary with labels and data arrays for charts
        """
        try:
            from app.config.database import db
            sensor_data_collection = db["Sensor_Data"]
            
            # Build query
            query = {}
            if sensor_ids:
                query["reservoirId"] = {"$in": sensor_ids}
            if start_time:
                query["ReadTime"] = {"$gte": start_time}
            if end_time:
                if "ReadTime" in query:
                    query["ReadTime"]["$lte"] = end_time
                else:
                    query["ReadTime"] = {"$lte": end_time}
            
            # Fetch data
            cursor = sensor_data_collection.find(query).sort("ReadTime", 1).limit(limit)
            readings = await cursor.to_list(length=limit)
            
            # Format data for charts
            labels = []
            temperatura_data = []
            ph_data = []
            conductividad_data = []
            nivel_agua_data = []
            
            # Chile timezone offset
            CHILE_OFFSET = timedelta(hours=-3)
            
            for reading in readings:
                # Normalize data
                normalized = self.normalize_sensor_reading(reading)
                
                # Format timestamp - convertir UTC a hora de Chile (UTC-3)
                timestamp = normalized["timestamp"]
                if timestamp:
                    if hasattr(timestamp, 'isoformat'):
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                        chile_time = timestamp.astimezone(timezone(CHILE_OFFSET))
                        labels.append(chile_time.strftime('%Y-%m-%dT%H:%M:%S'))
                    elif isinstance(timestamp, str):
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            chile_time = dt.astimezone(timezone(CHILE_OFFSET))
                            labels.append(chile_time.strftime('%Y-%m-%dT%H:%M:%S'))
                        except:
                            labels.append(timestamp)
                    else:
                        labels.append(str(timestamp))
                else:
                    labels.append("")
                
                # Extract values
                temperatura_data.append(normalized["temperature"])
                ph_data.append(normalized["ph"])
                conductividad_data.append(normalized["ec"])
                nivel_agua_data.append(normalized["water_level"])
            
            return {
                "labels": labels,
                "temperatura": temperatura_data,
                "ph": ph_data,
                "conductividad": conductividad_data,
                "nivel_agua": nivel_agua_data,
                "count": len(readings),
                "period_hours": int((end_time - start_time).total_seconds() / 3600) if start_time and end_time else 0
            }
            
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
    
    async def is_sensor_connected(self, sensor_id: str, threshold_minutes: int = 15) -> bool:
        """
        Check if a sensor is currently connected (has recent data)
        
        Args:
            sensor_id: Sensor identifier
            threshold_minutes: Minutes threshold to consider sensor as connected (default: 15)
            
        Returns:
            True if sensor is connected (has data within threshold), False otherwise
        """
        try:
            from app.config.database import db
            sensor_data_collection = db["Sensor_Data"]
            current_time = datetime.now(timezone.utc)
            
            # Try a set of possible identifier variants so we match different naming conventions
            # First try deterministic mapping from sensors collection -> reservoirId
            reservoir = await self.resolve_reservoir_id(sensor_id)
            possible_ids = {sensor_id}
            if reservoir:
                possible_ids.add(reservoir)
            # If sensor_id contains a prefix like 'AWS_IoT_<HEX>', add the suffix
            if "_" in sensor_id:
                possible_ids.add(sensor_id.split("_", 1)[-1])
            # Also add last 12 characters (common device hex) as a fallback
            if len(sensor_id) >= 12:
                possible_ids.add(sensor_id[-12:])

            # Build a $or query combining exact matches and case-insensitive regex matches
            or_clauses = []
            for pid in possible_ids:
                or_clauses.extend([
                    {"reservoirId": pid},
                    {"sensor_id": pid},
                    {"reservoir_id": pid},
                    {"reservoirId": {"$regex": pid, "$options": "i"}}
                ])

            latest_reading = await sensor_data_collection.find_one({"$or": or_clauses}, sort=[("ReadTime", -1)])

            if not latest_reading:
                logger.info(f"Sensor {sensor_id} has no data - considered disconnected")
                return False

            # Normalize the reading so we can handle multiple timestamp fields/formats
            try:
                normalized = self.normalize_sensor_reading(latest_reading)
            except Exception:
                normalized = latest_reading

            # Get timestamp from normalized reading first, then fall back to common fields
            last_reading_time = normalized.get("timestamp") or latest_reading.get("ReadTime") or latest_reading.get("created_at")
            if not last_reading_time:
                logger.debug(f"Sensor {sensor_id} latest reading has no timestamp - considered disconnected")
                return False

            # If timestamp is a string, try to parse ISO format
            if isinstance(last_reading_time, str):
                try:
                    # Handle trailing Z
                    last_reading_time = datetime.fromisoformat(last_reading_time.replace('Z', '+00:00'))
                except Exception:
                    try:
                        # Try generic parse fallback
                        from dateutil import parser as _parser
                        last_reading_time = _parser.parse(last_reading_time)
                    except Exception:
                        logger.debug(f"Unable to parse timestamp string for sensor {sensor_id}: {last_reading_time}")
                        return False

            # Ensure timezone aware. If naive, assume sensor timestamps are in Chile local time (UTC-3)
            if getattr(last_reading_time, 'tzinfo', None) is None:
                try:
                    # Use datetime.timezone with CHILE_OFFSET
                    from datetime import timezone as _timezone
                    last_reading_time = last_reading_time.replace(tzinfo=_timezone(CHILE_OFFSET))
                    # Convert to UTC for comparison
                    last_reading_time = last_reading_time.astimezone(timezone.utc)
                except Exception:
                    # Last resort: assume UTC
                    last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            # Calculate time difference
            time_diff_minutes = (current_time - last_reading_time).total_seconds() / 60
            
            is_connected = time_diff_minutes < threshold_minutes
            logger.debug(
                f"Sensor {sensor_id}: last reading {time_diff_minutes:.1f} min ago - "
                f"{'connected' if is_connected else 'disconnected'}"
            )
            
            return is_connected
            
        except Exception as e:
            logger.error(f"Error checking sensor connection status: {e}")
            return False


# Singleton instance
sensor_service = SensorService()

