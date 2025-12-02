"""
Sensor Monitor Service
Monitors sensor data and creates alerts when values exceed configured thresholds
Runs as a background task checking for threshold violations

Alert Logic:
- 5-6 min without data: WARNING level (no notification)
- 10+ min without data: CRITICAL level (send email + WhatsApp)
- Measurement alerts (pH, temp, EC): Only if sensor is CONNECTED
- Auto-resolve: When sensor reconnects or values return to normal range

False Positive Prevention:
- Measurement alerts require 2 CONSECUTIVE out-of-range readings
- This prevents false alerts from momentary cable disconnections
- If a value returns to normal, the violation counter is reset
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set

from app.config.database import db
from app.services.sensor_service import sensor_service
from app.repositories.alert_repository import alert_repository

logger = logging.getLogger(__name__)

# Alert timing configuration (in minutes)
WARNING_THRESHOLD_MINUTES = 6      # 5-6 min = warning
CRITICAL_THRESHOLD_MINUTES = 10    # 10+ min = critical

# Measurement alert types (require connected sensor)
MEASUREMENT_TYPES = ['ph', 'temperature', 'ec', 'water_level', 'conductivity']


class SensorMonitor:
    """
    Background service that monitors sensor readings and creates alerts
    
    Responsibilities:
    - Check sensor readings against configured thresholds
    - Create disconnection alerts (warning at 5-6 min, critical at 10 min)
    - Create measurement alerts ONLY for connected sensors
    - Auto-resolve alerts when conditions normalize
    - Prevent duplicate alerts
    - Validate consecutive readings to avoid false positives from cable disconnections
    """
    
    # Number of consecutive out-of-range readings required before creating an alert
    CONSECUTIVE_READINGS_REQUIRED = 2
    
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
        
        # Startup grace period to avoid false alerts on service restart
        self.startup_grace_seconds = 120
        self.started_at: Optional[datetime] = None
        
        # Track sensors currently in warning state (to escalate to critical)
        self.sensors_in_warning: Set[str] = set()
        
        # Track consecutive out-of-range readings per sensor/metric
        # Format: {sensor_id: {metric: {"count": int, "last_value": float, "last_level": str, "last_message": str}}}
        self.consecutive_violations: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    async def start(self):
        """Start the monitoring loop"""
        self.running = True
        self.started_at = datetime.now(timezone.utc)
        logger.info(f"Sensor monitor started (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self._check_all_sensors()
            except Exception as e:
                logger.error(f"Error in sensor monitor loop: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Sensor monitor stopped")
    
    def _in_startup_grace(self) -> bool:
        """Return True if within startup grace period (no alerts during startup)"""
        if not self.started_at:
            return False
        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return elapsed < self.startup_grace_seconds
    
    async def _check_all_sensors(self):
        """Check all sensors with alerts enabled"""
        try:
            sensors = await self.sensors_collection.find({
                "alert_config.enabled": True
            }).to_list(length=100)
            
            if not sensors:
                logger.debug("No sensors with alerts enabled")
                return
            
            logger.debug(f"Checking {len(sensors)} sensors")
            
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
        Check a single sensor for disconnection and threshold violations
        
        Flow:
        1. Get latest reading and check how old it is
        2. If no data in 5-6 min -> WARNING (no notification)
        3. If no data in 10+ min -> CRITICAL (send notifications)
        4. If connected -> auto-resolve disconnection alerts, check thresholds
        5. If values in range -> auto-resolve measurement alerts
        """
        sensor_id = sensor_config.get("sensor_id")
        if not sensor_id:
            return
        
        alert_config = sensor_config.get("alert_config", {})
        if not alert_config.get("enabled"):
            return
        
        # Get latest sensor reading
        latest_reading = await self._get_latest_reading(sensor_id)
        
        if not latest_reading:
            # No data ever - consider disconnected if not in startup grace
            if not self._in_startup_grace():
                await self._handle_disconnection(sensor_id, sensor_config, minutes_since_data=9999)
            return
        
        # Calculate time since last reading
        minutes_since_data = self._get_minutes_since_reading(latest_reading)
        
        # Handle connection status based on thresholds
        if minutes_since_data >= CRITICAL_THRESHOLD_MINUTES:
            # CRITICAL: 10+ minutes without data
            await self._handle_disconnection(sensor_id, sensor_config, minutes_since_data, level="critical")
        elif minutes_since_data >= WARNING_THRESHOLD_MINUTES:
            # WARNING: 5-6 minutes without data
            await self._handle_disconnection(sensor_id, sensor_config, minutes_since_data, level="warning")
        else:
            # CONNECTED: Sensor is sending data normally
            await self._handle_connection(sensor_id, sensor_config, latest_reading)
    
    async def _get_latest_reading(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent reading for a sensor"""
        # Try multiple ID formats to handle different naming conventions
        possible_ids = {sensor_id}
        if "_" in sensor_id:
            possible_ids.add(sensor_id.split("_", 1)[-1])
        if len(sensor_id) >= 12:
            possible_ids.add(sensor_id[-12:])
        
        or_clauses = []
        for pid in possible_ids:
            or_clauses.extend([
                {"reservoirId": pid},
                {"sensor_id": pid},
                {"reservoir_id": pid},
                {"reservoirId": {"$regex": pid, "$options": "i"}}
            ])
        
        return await self.sensor_data_collection.find_one(
            {"$or": or_clauses},
            sort=[("ReadTime", -1)]
        )
    
    def _get_minutes_since_reading(self, reading: Dict[str, Any]) -> float:
        """Calculate minutes since the reading was recorded"""
        current_time = datetime.now(timezone.utc)
        
        # Get timestamp from reading
        read_time = reading.get("ReadTime") or reading.get("timestamp") or reading.get("created_at")
        
        if not read_time:
            return 9999  # No timestamp = treat as very old
        
        # Parse string timestamps
        if isinstance(read_time, str):
            try:
                read_time = datetime.fromisoformat(read_time.replace('Z', '+00:00'))
            except Exception:
                return 9999
        
        # Ensure timezone aware
        if read_time.tzinfo is None:
            read_time = read_time.replace(tzinfo=timezone.utc)
        
        diff = (current_time - read_time).total_seconds() / 60
        return max(0, diff)
    
    async def _handle_disconnection(
        self,
        sensor_id: str,
        sensor_config: Dict[str, Any],
        minutes_since_data: float,
        level: str = "critical"
    ):
        """
        Handle sensor disconnection
        
        - Archive any existing measurement alerts (they're no longer valid)
        - Create/escalate disconnection alert
        """
        if self._in_startup_grace():
            logger.debug(f"Skipping disconnection alert for {sensor_id} during startup grace")
            return
        
        # Archive measurement alerts for this sensor (they're invalid when disconnected)
        try:
            await alert_repository.archive_measurement_alerts_for_sensor(sensor_id)
        except Exception:
            logger.exception(f"Failed to archive measurement alerts for {sensor_id}")
        
        # Check if disconnection alert already exists
        existing_alert = await self.alerts_collection.find_one({
            "sensor_id": sensor_id,
            "type": "sensor_disconnection",
            "is_resolved": False
        })
        
        if existing_alert:
            existing_level = existing_alert.get("level", "warning")
            
            # Escalate from warning to critical if needed
            if existing_level == "warning" and level == "critical":
                await self._escalate_to_critical(existing_alert, sensor_id, minutes_since_data)
                self.sensors_in_warning.discard(sensor_id)
            
            # Already has appropriate alert
            return
        
        # Create new disconnection alert
        location = sensor_config.get("location", f"Sensor {sensor_id}")
        
        if level == "warning":
            title = "Sensor sin datos recientes"
            message = f"Sensor {sensor_id} sin datos en los últimos {int(minutes_since_data)} minutos"
            self.sensors_in_warning.add(sensor_id)
        else:
            title = "Sensor Desconectado"
            message = f"Sensor {sensor_id} sin datos por más de {int(minutes_since_data)} minutos"
            self.sensors_in_warning.discard(sensor_id)
        
        alert_doc = {
            "type": "sensor_disconnection",
            "level": level,
            "title": title,
            "message": message,
            "location": location,
            "threshold_info": f"Sin datos: {int(minutes_since_data)} min",
            "sensor_id": sensor_id,
            "value": f"{int(minutes_since_data)} minutos",  # Disconnect duration for notifications
            "created_at": datetime.now(timezone.utc),
            "is_resolved": False,
            "status": "active",
            "source": "sensor_monitor"
        }
        
        try:
            # Insert directly for disconnection alerts (bypass measurement checks)
            await self.alerts_collection.insert_one(alert_doc)
            logger.info(f"Disconnection alert ({level}) created for sensor {sensor_id}")
        except Exception:
            logger.exception(f"Failed to create disconnection alert for {sensor_id}")
    
    async def _escalate_to_critical(
        self,
        existing_alert: Dict[str, Any],
        sensor_id: str,
        minutes_since_data: float
    ):
        """Escalate a warning disconnection alert to critical"""
        try:
            await self.alerts_collection.update_one(
                {"_id": existing_alert["_id"]},
                {
                    "$set": {
                        "level": "critical",
                        "title": "Sensor Desconectado",
                        "message": f"Sensor {sensor_id} sin datos por más de {int(minutes_since_data)} minutos",
                        "threshold_info": f"Sin datos: {int(minutes_since_data)} min",
                        "value": f"{int(minutes_since_data)} minutos",  # Disconnect duration for notifications
                        "escalated_at": datetime.now(timezone.utc)
                    }
                }
            )
            logger.info(f"Disconnection alert escalated to critical for sensor {sensor_id}")
        except Exception:
            logger.exception(f"Failed to escalate alert for {sensor_id}")
    
    async def _handle_connection(
        self,
        sensor_id: str,
        sensor_config: Dict[str, Any],
        latest_reading: Dict[str, Any]
    ):
        """
        Handle a connected sensor
        
        - Auto-resolve any disconnection alerts
        - Check measurement thresholds
        - Auto-resolve measurement alerts if values are back in range
        """
        # Auto-resolve disconnection alerts
        await self._auto_resolve_disconnection_alert(sensor_id)
        
        # Remove from warning tracking
        self.sensors_in_warning.discard(sensor_id)
        
        # Now check measurement thresholds
        normalized = sensor_service.normalize_sensor_reading(latest_reading)
        thresholds = sensor_config.get("alert_config", {}).get("thresholds") or \
                     sensor_config.get("alert_config", {}).get("parameters") or {}
        
        # Check each metric and auto-resolve if in range
        await self._check_ph(sensor_id, normalized, thresholds, sensor_config)
        await self._check_temperature(sensor_id, normalized, thresholds, sensor_config)
        await self._check_ec(sensor_id, normalized, thresholds, sensor_config)
        await self._check_water_level(sensor_id, normalized, thresholds, sensor_config)
    
    async def _auto_resolve_disconnection_alert(self, sensor_id: str):
        """Auto-resolve disconnection alert when sensor reconnects"""
        try:
            existing_alert = await self.alerts_collection.find_one({
                "sensor_id": sensor_id,
                "type": "sensor_disconnection",
                "is_resolved": False
            })
            
            if existing_alert:
                await alert_repository.dismiss_alert(
                    alert_id=str(existing_alert["_id"]),
                    dismissed_by="system_auto",
                    dismissed_at=datetime.now(timezone.utc),
                    reason="Sensor reconectado - auto-resuelto"
                )
                logger.info(f"Auto-resolved disconnection alert for sensor {sensor_id}")
        except Exception:
            logger.exception(f"Failed to auto-resolve disconnection alert for {sensor_id}")

    def _record_violation(
        self,
        sensor_id: str,
        metric: str,
        value: float,
        level: str,
        message: str
    ) -> bool:
        """
        Record an out-of-range reading and return True if alert should be created.
        
        Requires CONSECUTIVE_READINGS_REQUIRED consecutive violations before returning True.
        This prevents false positives from momentary cable disconnections.
        
        Args:
            sensor_id: Sensor identifier
            metric: Metric type (ph, temperature, ec, water_level)
            value: Current reading value
            level: Alert level (warning, critical)
            message: Alert message
            
        Returns:
            True if consecutive violations threshold reached, False otherwise
        """
        if sensor_id not in self.consecutive_violations:
            self.consecutive_violations[sensor_id] = {}
        
        sensor_violations = self.consecutive_violations[sensor_id]
        
        if metric not in sensor_violations:
            # First violation - record it but don't create alert yet
            sensor_violations[metric] = {
                "count": 1,
                "last_value": value,
                "last_level": level,
                "last_message": message
            }
            logger.debug(
                f"First violation for {sensor_id}/{metric}: {value} "
                f"(need {self.CONSECUTIVE_READINGS_REQUIRED} consecutive)"
            )
            return False
        
        # Increment consecutive violation count
        sensor_violations[metric]["count"] += 1
        sensor_violations[metric]["last_value"] = value
        sensor_violations[metric]["last_level"] = level
        sensor_violations[metric]["last_message"] = message
        
        count = sensor_violations[metric]["count"]
        logger.debug(
            f"Violation #{count} for {sensor_id}/{metric}: {value} "
            f"(need {self.CONSECUTIVE_READINGS_REQUIRED} consecutive)"
        )
        
        # Return True if we've reached the threshold
        return count >= self.CONSECUTIVE_READINGS_REQUIRED
    
    def _clear_violation(self, sensor_id: str, metric: str):
        """
        Clear the violation counter for a sensor/metric when value returns to normal.
        
        Args:
            sensor_id: Sensor identifier
            metric: Metric type (ph, temperature, ec, water_level)
        """
        if sensor_id in self.consecutive_violations:
            if metric in self.consecutive_violations[sensor_id]:
                del self.consecutive_violations[sensor_id][metric]
                logger.debug(f"Cleared violation counter for {sensor_id}/{metric}")
            
            # Clean up empty sensor entries
            if not self.consecutive_violations[sensor_id]:
                del self.consecutive_violations[sensor_id]

    
    async def _check_ph(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check pH value and create/resolve alerts"""
        value = reading.get("ph")
        if value is None or value == 0:
            return
        
        config = thresholds.get("ph", {})
        min_val = config.get("min")
        max_val = config.get("max")
        critical_min = config.get("critical_min")
        critical_max = config.get("critical_max")
        
        # Determine if value is out of range
        out_of_range = False
        level = None
        message = None
        
        if critical_min and value < critical_min:
            out_of_range = True
            level = "critical"
            message = f"pH crítico bajo: {value:.2f} (mínimo crítico: {critical_min})"
        elif critical_max and value > critical_max:
            out_of_range = True
            level = "critical"
            message = f"pH crítico alto: {value:.2f} (máximo crítico: {critical_max})"
        elif min_val and value < min_val:
            out_of_range = True
            level = "warning"
            message = f"pH bajo: {value:.2f} (rango óptimo: {min_val}-{max_val})"
        elif max_val and value > max_val:
            out_of_range = True
            level = "warning"
            message = f"pH alto: {value:.2f} (rango óptimo: {min_val}-{max_val})"
        
        if out_of_range:
            # Only create alert if we have consecutive violations
            if self._record_violation(sensor_id, "ph", value, level, message):
                await self._create_measurement_alert(sensor_id, "ph", level, value, message, sensor_config)
        else:
            # Value is in range - clear violation counter and auto-resolve any existing pH alert
            self._clear_violation(sensor_id, "ph")
            await self._auto_resolve_measurement_alert(sensor_id, "ph")
    
    async def _check_temperature(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check temperature value and create/resolve alerts"""
        value = reading.get("temperature")
        if value is None or value == 0:
            return
        
        config = thresholds.get("temperature", {})
        min_val = config.get("min")
        max_val = config.get("max")
        critical_min = config.get("critical_min")
        critical_max = config.get("critical_max")
        
        out_of_range = False
        level = None
        message = None
        
        if critical_min and value < critical_min:
            out_of_range = True
            level = "critical"
            message = f"Temperatura crítica baja: {value:.1f}°C (mínimo: {critical_min}°C)"
        elif critical_max and value > critical_max:
            out_of_range = True
            level = "critical"
            message = f"Temperatura crítica alta: {value:.1f}°C (máximo: {critical_max}°C)"
        elif min_val and value < min_val:
            out_of_range = True
            level = "warning"
            message = f"Temperatura baja: {value:.1f}°C (rango óptimo: {min_val}-{max_val}°C)"
        elif max_val and value > max_val:
            out_of_range = True
            level = "warning"
            message = f"Temperatura alta: {value:.1f}°C (rango óptimo: {min_val}-{max_val}°C)"
        
        if out_of_range:
            # Only create alert if we have consecutive violations
            if self._record_violation(sensor_id, "temperature", value, level, message):
                await self._create_measurement_alert(sensor_id, "temperature", level, value, message, sensor_config)
        else:
            # Value is in range - clear violation counter and auto-resolve any existing alert
            self._clear_violation(sensor_id, "temperature")
            await self._auto_resolve_measurement_alert(sensor_id, "temperature")
    
    async def _check_ec(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check EC (conductivity) value and create/resolve alerts"""
        value = reading.get("ec")
        if value is None:
            return
        
        config = thresholds.get("ec", {})
        min_val = config.get("min")
        max_val = config.get("max")
        critical_min = config.get("critical_min")
        critical_max = config.get("critical_max")
        
        out_of_range = False
        level = None
        message = None
        
        if critical_min and value < critical_min:
            out_of_range = True
            level = "critical"
            message = f"Conductividad crítica baja: {value:.1f} dS/m (mínimo: {critical_min})"
        elif critical_max and value > critical_max:
            out_of_range = True
            level = "critical"
            message = f"Conductividad crítica alta: {value:.1f} dS/m (máximo: {critical_max})"
        elif min_val and value < min_val:
            out_of_range = True
            level = "warning"
            message = f"Conductividad baja: {value:.1f} dS/m (rango óptimo: {min_val}-{max_val})"
        elif max_val and value > max_val:
            out_of_range = True
            level = "warning"
            message = f"Conductividad alta: {value:.1f} dS/m (rango óptimo: {min_val}-{max_val})"
        
        if out_of_range:
            # Only create alert if we have consecutive violations
            if self._record_violation(sensor_id, "ec", value, level, message):
                await self._create_measurement_alert(sensor_id, "ec", level, value, message, sensor_config)
        else:
            # Value is in range - clear violation counter and auto-resolve any existing alert
            self._clear_violation(sensor_id, "ec")
            await self._auto_resolve_measurement_alert(sensor_id, "ec")
    
    async def _check_water_level(
        self,
        sensor_id: str,
        reading: Dict[str, Any],
        thresholds: Dict[str, Any],
        sensor_config: Dict[str, Any]
    ):
        """Check water level value and create/resolve alerts"""
        value = reading.get("water_level")
        if value is None:
            return
        
        config = thresholds.get("water_level", {})
        min_val = config.get("min")
        max_val = config.get("max")
        critical_min = config.get("critical_min")
        critical_max = config.get("critical_max")
        
        out_of_range = False
        level = None
        message = None
        
        if critical_min is not None and value < critical_min:
            out_of_range = True
            level = "critical"
            message = f"Nivel de agua crítico: {value:.1f}% (mínimo: {critical_min}%)"
        elif critical_max is not None and value > critical_max:
            out_of_range = True
            level = "critical"
            message = f"Nivel de agua crítico: {value:.1f}% (máximo: {critical_max}%)"
        elif min_val is not None and value < min_val:
            out_of_range = True
            level = "warning"
            message = f"Nivel de agua bajo: {value:.1f}% (rango óptimo: {min_val}-{max_val}%)"
        elif max_val is not None and value > max_val:
            out_of_range = True
            level = "warning"
            message = f"Nivel de agua alto: {value:.1f}% (rango óptimo: {min_val}-{max_val}%)"
        
        if out_of_range:
            # Only create alert if we have consecutive violations
            if self._record_violation(sensor_id, "water_level", value, level, message):
                await self._create_measurement_alert(sensor_id, "water_level", level, value, message, sensor_config)
        else:
            # Value is in range - clear violation counter and auto-resolve any existing alert
            self._clear_violation(sensor_id, "water_level")
            await self._auto_resolve_measurement_alert(sensor_id, "water_level")
    
    async def _create_measurement_alert(
        self,
        sensor_id: str,
        alert_type: str,
        level: str,
        value: float,
        message: str,
        sensor_config: Dict[str, Any]
    ):
        """
        Create a measurement alert (pH, temp, EC, water_level)
        
        IMPORTANT: Only creates if sensor is connected (validated by alert_repository)
        """
        if self._in_startup_grace():
            logger.debug(f"Skipping {alert_type} alert for {sensor_id} during startup grace")
            return
        
        # Check if similar alert already exists
        existing = await self.alerts_collection.find_one({
            "sensor_id": sensor_id,
            "type": alert_type,
            "is_resolved": False
        })
        
        if existing:
            logger.debug(f"Alert already exists: {alert_type} for {sensor_id}")
            return
        
        location = sensor_config.get("location", f"Sensor {sensor_id}")
        sensor_name = sensor_config.get("name", f"Sensor {sensor_id}")
        
        alert_doc = {
            "type": alert_type,
            "level": level,
            "title": f"{alert_type.upper()} - {sensor_name}",
            "message": message,
            "location": location,
            "threshold_info": "Valor fuera de rango crítico" if level == "critical" else "Valor fuera de rango óptimo",
            "sensor_id": sensor_id,
            "value": value,
            "created_at": datetime.now(timezone.utc),
            "is_resolved": False,
            "status": "active",
            "source": "sensor_monitor"
        }
        
        try:
            # Use repository which validates sensor connection
            inserted_id = await alert_repository.create_alert(alert_doc)
            if inserted_id:
                logger.info(f"Alert created: {alert_type} ({level}) for {sensor_id}, value: {value}")
            else:
                logger.debug(f"Alert skipped (sensor disconnected or duplicate): {alert_type} for {sensor_id}")
        except Exception:
            logger.exception(f"Failed to create {alert_type} alert for {sensor_id}")
    
    async def _auto_resolve_measurement_alert(self, sensor_id: str, alert_type: str):
        """Auto-resolve a measurement alert when value returns to normal range"""
        try:
            existing = await self.alerts_collection.find_one({
                "sensor_id": sensor_id,
                "type": alert_type,
                "is_resolved": False
            })
            
            if existing:
                await alert_repository.dismiss_alert(
                    alert_id=str(existing["_id"]),
                    dismissed_by="system_auto",
                    dismissed_at=datetime.now(timezone.utc),
                    reason=f"Valor de {alert_type} normalizado - auto-resuelto"
                )
                logger.info(f"Auto-resolved {alert_type} alert for sensor {sensor_id}")
        except Exception:
            logger.exception(f"Failed to auto-resolve {alert_type} alert for {sensor_id}")


# Singleton instance
sensor_monitor = SensorMonitor()
