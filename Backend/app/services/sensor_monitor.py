"""
Sensor Monitor Service
Monitors sensor data and creates alerts when values exceed configured thresholds
Runs as a background task checking for threshold violations
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from bson import ObjectId

from app.config.database import db
from app.services.alert_service import alert_service
from app.services.sensor_service import sensor_service

logger = logging.getLogger(__name__)


class SensorMonitor:
    """
    Background service that monitors sensor readings and creates alerts
    
    Responsibilities:
    - Check sensor readings against configured thresholds
    - Create alerts for threshold violations
    - Only create alerts for connected sensors
    - Prevent duplicate alerts (throttling)
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize sensor monitor
        
        Args:
            check_interval_seconds: How often to check sensors (default: 60s)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.sensors_collection = db["sensors"]
        self.sensor_data_collection = db["Sensor_Data"]
        self.alerts_collection = db["alerts"]
    
    async def start(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info(f"Sensor monitor started (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self._check_all_sensors()
            except Exception as e:
                logger.error(f"Error in sensor monitor loop: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Sensor monitor stopped")
    
    async def _check_all_sensors(self):
        """Check all sensors for threshold violations"""
        try:
            # Get all sensors with alert configuration enabled
            sensors = await self.sensors_collection.find({
                "alert_config.enabled": True
            }).to_list(length=100)
            
            if not sensors:
                logger.debug("No sensors with alerts enabled")
                return
            
            logger.debug(f"Checking {len(sensors)} sensors for threshold violations")
            
            for sensor_config in sensors:
                try:
                    await self._check_sensor(sensor_config)
                except Exception as e:
                    sensor_id = sensor_config.get("sensor_id", "unknown")
                    logger.error(f"Error checking sensor {sensor_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error getting sensors to check: {e}")
    
    async def _check_sensor(self, sensor_config: Dict[str, Any]):
        """
        Check a single sensor for threshold violations
        
        Args:
            sensor_config: Sensor configuration document with alert_config
        """
        sensor_id = sensor_config.get("sensor_id")
        alert_config = sensor_config.get("alert_config", {})
        
        if not alert_config.get("enabled"):
            return
        
        # Check if sensor is connected (required for measurement alerts)
        is_connected = await sensor_service.is_sensor_connected(sensor_id)
        
        if not is_connected:
            # Only check for disconnection alert
            await self._check_disconnection_alert(sensor_id, sensor_config)
            return
        
        # Sensor is connected - check measurement thresholds
        # Get latest reading
        latest_reading = await self.sensor_data_collection.find_one(
            {"reservoirId": sensor_id},
            sort=[("ReadTime", -1)]
        )
        
        if not latest_reading:
            return
        
        # Normalize reading
        normalized = sensor_service.normalize_sensor_reading(latest_reading)
        
        # Get thresholds
        thresholds = alert_config.get("thresholds", {})
        
        # Check each parameter
        await self._check_ph_threshold(sensor_id, normalized, thresholds, sensor_config)
        await self._check_temperature_threshold(sensor_id, normalized, thresholds, sensor_config)
        await self._check_ec_threshold(sensor_id, normalized, thresholds, sensor_config)
        await self._check_water_level_threshold(sensor_id, normalized, thresholds, sensor_config)
    
    async def _check_ph_threshold(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check pH value against thresholds"""
        ph_value = reading.get("ph")
        if ph_value is None or ph_value == 0:
            return
        
        ph_config = thresholds.get("ph", {})
        min_val = ph_config.get("min")
        max_val = ph_config.get("max")
        critical_min = ph_config.get("critical_min")
        critical_max = ph_config.get("critical_max")
        
        # Check critical thresholds
        if critical_min and ph_value < critical_min:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ph",
                level="critical",
                value=ph_value,
                message=f"pH crítico bajo: {ph_value:.2f} (mínimo: {critical_min})",
                sensor_config=sensor_config
            )
        elif critical_max and ph_value > critical_max:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ph",
                level="critical",
                value=ph_value,
                message=f"pH crítico alto: {ph_value:.2f} (máximo: {critical_max})",
                sensor_config=sensor_config
            )
        # Check warning thresholds
        elif min_val and ph_value < min_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ph",
                level="warning",
                value=ph_value,
                message=f"pH bajo: {ph_value:.2f} (óptimo: {min_val}-{max_val})",
                sensor_config=sensor_config
            )
        elif max_val and ph_value > max_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ph",
                level="warning",
                value=ph_value,
                message=f"pH alto: {ph_value:.2f} (óptimo: {min_val}-{max_val})",
                sensor_config=sensor_config
            )
    
    async def _check_temperature_threshold(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check temperature value against thresholds"""
        temp_value = reading.get("temperature")
        if temp_value is None or temp_value == 0:
            return
        
        temp_config = thresholds.get("temperature", {})
        min_val = temp_config.get("min")
        max_val = temp_config.get("max")
        critical_min = temp_config.get("critical_min")
        critical_max = temp_config.get("critical_max")
        
        # Check critical thresholds
        if critical_min and temp_value < critical_min:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="temperature",
                level="critical",
                value=temp_value,
                message=f"Temperatura crítica baja: {temp_value:.1f}°C (mínimo: {critical_min}°C)",
                sensor_config=sensor_config
            )
        elif critical_max and temp_value > critical_max:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="temperature",
                level="critical",
                value=temp_value,
                message=f"Temperatura crítica alta: {temp_value:.1f}°C (máximo: {critical_max}°C)",
                sensor_config=sensor_config
            )
        # Check warning thresholds
        elif min_val and temp_value < min_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="temperature",
                level="warning",
                value=temp_value,
                message=f"Temperatura baja: {temp_value:.1f}°C (óptimo: {min_val}-{max_val}°C)",
                sensor_config=sensor_config
            )
        elif max_val and temp_value > max_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="temperature",
                level="warning",
                value=temp_value,
                message=f"Temperatura alta: {temp_value:.1f}°C (óptimo: {min_val}-{max_val}°C)",
                sensor_config=sensor_config
            )
    
    async def _check_ec_threshold(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check EC (conductivity) value against thresholds"""
        ec_value = reading.get("ec")
        if ec_value is None:
            return
        
        ec_config = thresholds.get("ec", {})
        min_val = ec_config.get("min")
        max_val = ec_config.get("max")
        critical_min = ec_config.get("critical_min")
        critical_max = ec_config.get("critical_max")
        
        # Check critical thresholds
        if critical_min and ec_value < critical_min:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ec",
                level="critical",
                value=ec_value,
                message=f"Conductividad crítica baja: {ec_value:.1f} dS/m (mínimo: {critical_min})",
                sensor_config=sensor_config
            )
        elif critical_max and ec_value > critical_max:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ec",
                level="critical",
                value=ec_value,
                message=f"Conductividad crítica alta: {ec_value:.1f} dS/m (máximo: {critical_max})",
                sensor_config=sensor_config
            )
        # Check warning thresholds
        elif min_val and ec_value < min_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ec",
                level="warning",
                value=ec_value,
                message=f"Conductividad baja: {ec_value:.1f} dS/m (óptimo: {min_val}-{max_val})",
                sensor_config=sensor_config
            )
        elif max_val and ec_value > max_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="ec",
                level="warning",
                value=ec_value,
                message=f"Conductividad alta: {ec_value:.1f} dS/m (óptimo: {min_val}-{max_val})",
                sensor_config=sensor_config
            )
    
    async def _check_water_level_threshold(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check water level value against thresholds"""
        water_level = reading.get("water_level")
        if water_level is None:
            return
        
        wl_config = thresholds.get("water_level", {})
        min_val = wl_config.get("min")
        max_val = wl_config.get("max")
        critical_min = wl_config.get("critical_min")
        critical_max = wl_config.get("critical_max")
        
        # Check critical thresholds
        if critical_min and water_level < critical_min:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="water_level",
                level="critical",
                value=water_level,
                message=f"Nivel de agua crítico: {water_level:.1f}% (mínimo: {critical_min}%)",
                sensor_config=sensor_config
            )
        elif critical_max and water_level > critical_max:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="water_level",
                level="critical",
                value=water_level,
                message=f"Nivel de agua crítico: {water_level:.1f}% (máximo: {critical_max}%)",
                sensor_config=sensor_config
            )
        # Check warning thresholds
        elif min_val and water_level < min_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="water_level",
                level="warning",
                value=water_level,
                message=f"Nivel de agua bajo: {water_level:.1f}% (óptimo: {min_val}-{max_val}%)",
                sensor_config=sensor_config
            )
        elif max_val and water_level > max_val:
            await self._create_alert_if_needed(
                sensor_id=sensor_id,
                alert_type="water_level",
                level="warning",
                value=water_level,
                message=f"Nivel de agua alto: {water_level:.1f}% (óptimo: {min_val}-{max_val}%)",
                sensor_config=sensor_config
            )
    
    async def _check_disconnection_alert(
        self,
        sensor_id: str,
        sensor_config: Dict[str, Any]
    ):
        """Create alert if sensor is disconnected"""
        # Check if disconnection alert already exists
        existing_alert = await self.alerts_collection.find_one({
            "sensor_id": sensor_id,
            "type": "sensor_disconnected",
            "is_resolved": False
        })
        
        if existing_alert:
            logger.debug(f"Disconnection alert already exists for {sensor_id}")
            return
        
        # Create disconnection alert
        location = sensor_config.get("location", f"Sensor {sensor_id}")
        
        alert_doc = {
            "type": "sensor_disconnected",
            "level": "warning",
            "title": f"Sensor Desconectado",
            "message": f"El sensor {sensor_id} no ha enviado datos en los últimos 15 minutos",
            "location": location,
            "threshold_info": "Timeout crítico: 15 minutos",
            "sensor_id": sensor_id,
            "created_at": datetime.now(timezone.utc),
            "is_resolved": False,
            "status": "active",
            "source": "sensor_monitor"
        }
        
        result = await self.alerts_collection.insert_one(alert_doc)
        logger.info(f"Disconnection alert created for sensor {sensor_id}")
    
    async def _create_alert_if_needed(
        self,
        sensor_id: str,
        alert_type: str,
        level: str,
        value: float,
        message: str,
        sensor_config: Dict[str, Any]
    ):
        """
        Create alert if one doesn't already exist for this sensor/type
        
        Prevents duplicate alerts by checking for existing unresolved alerts
        """
        # Check if similar alert already exists
        existing_alert = await self.alerts_collection.find_one({
            "sensor_id": sensor_id,
            "type": alert_type,
            "is_resolved": False
        })
        
        if existing_alert:
            logger.debug(f"Alert already exists: {alert_type} for {sensor_id}")
            return
        
        # Validate that alert should be created (sensor must be connected for measurement alerts)
        should_create, skip_reason = await alert_service.should_create_sensor_alert(
            alert_type=alert_type,
            sensor_id=sensor_id
        )
        
        if not should_create:
            logger.debug(f"Skipping alert creation: {skip_reason}")
            return
        
        # Create the alert
        location = sensor_config.get("location", f"Sensor {sensor_id}")
        sensor_name = sensor_config.get("name", f"Sensor {sensor_id}")
        
        # Build threshold info string
        threshold_info = f"Nivel {level}"
        if level == "critical":
            threshold_info = "Valor fuera de rango crítico"
        elif level == "warning":
            threshold_info = "Valor fuera de rango óptimo"
        
        alert_doc = {
            "type": alert_type,
            "level": level,
            "title": f"{alert_type.upper()} - {sensor_name}",
            "message": message,
            "location": location,
            "threshold_info": threshold_info,
            "sensor_id": sensor_id,
            "value": value,
            "created_at": datetime.now(timezone.utc),
            "is_resolved": False,
            "status": "active",
            "source": "sensor_monitor"
        }
        
        result = await self.alerts_collection.insert_one(alert_doc)
        logger.info(
            f"Alert created: {alert_type} ({level}) for {sensor_id} - "
            f"value: {value}, id: {result.inserted_id}"
        )


# Singleton instance
sensor_monitor = SensorMonitor()
