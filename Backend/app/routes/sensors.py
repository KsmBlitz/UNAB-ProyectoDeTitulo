"""
Sensors routes
Sensor data and metrics endpoints
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel
import logging

from app.config import sensor_collection
from app.utils import get_current_user, get_current_admin_user
from app.services import predict_sensor_values
from app.services.audit import log_audit_event
from app.services.cache import cache_service
from app.models.audit_models import AuditAction
from app.models.sensor_models import PredictionRequest, TimeRangeQuery
from app.models.alert_models import UpdateSensorAlertConfigRequest

logger = logging.getLogger(__name__)

# Timezone offset para Chile (UTC-3)
CHILE_OFFSET = timedelta(hours=-3)

router = APIRouter(prefix="/api", tags=["Datos de Sensores"])


def normalize_sensor_reading(reading: dict) -> dict:
    """
    Normaliza los nombres de campos de diferentes formatos de datos de sensores
    
    Usa SOLO el formato nuevo (minúsculas): temperature, ph, ec, water_level
    Esto es lo que Lambda guarda en MongoDB
    """
    # Usar formato nuevo (minúsculas) directamente
    temperature = reading.get("temperature", 0)
    ph = reading.get("ph", 0)
    ec = reading.get("ec", 0)
    water_level = reading.get("water_level", 0)
    
    # Timestamp puede venir como 'timestamp' o 'ReadTime'
    timestamp = reading.get("timestamp") or reading.get("ReadTime")
    
    return {
        "temperature": temperature,
        "ph": ph,
        "ec": ec,
        "water_level": water_level,
        "timestamp": timestamp
    }


# Removed PredictionConfigModel - now using models.sensor_models.PredictionRequest


@router.get("/sensors/individual")
async def get_individual_sensors_status(current_user: dict = Depends(get_current_user)):
    """
    Get detailed status of each individual sensor
    
    Returns sensor status based on last reading time:
    - online: < 15 minutes
    - warning: 15-30 minutes
    - offline: > 30 minutes
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Find unique sensors and their latest readings
        pipeline = [
            {"$sort": {"ReadTime": -1}},
            {"$group": {
                "_id": "$reservoirId",
                "lastReading": {"$first": "$$ROOT"}
            }},
            {"$limit": 20}
        ]
        
        db_sensors = await sensor_collection.aggregate(pipeline).to_list(length=None)
        sensors = []
        
        for sensor_group in db_sensors:
            reservoir_id = sensor_group["_id"]
            latest_reading = sensor_group["lastReading"]
            
            # Normalizar datos
            normalized = normalize_sensor_reading(latest_reading)
            
            # Ensure timezone aware datetime
            last_reading_time = normalized["timestamp"]
            if last_reading_time and last_reading_time.tzinfo is None:
                last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            # Calculate time difference
            if last_reading_time:
                time_diff = (current_time - last_reading_time).total_seconds()
                minutes_diff = time_diff / 60
            else:
                minutes_diff = 999999  # Sin timestamp
            
            # Determine status
            if minutes_diff < 15:
                status = "online"
            elif minutes_diff < 30:
                status = "warning"
            else:
                status = "offline"
            
            sensor_data = {
                "uid": reservoir_id,
                "last_values": {
                    "temperature": round(normalized["temperature"], 1) if normalized["temperature"] is not None and normalized["temperature"] != 0 else normalized["temperature"],
                    "ph": round(normalized["ph"], 2) if normalized["ph"] is not None and normalized["ph"] != 0 else normalized["ph"],
                    "ec": round(normalized["ec"], 1) if normalized["ec"] is not None and normalized["ec"] != 0 else normalized["ec"],
                    "water_level": round(normalized["water_level"], 1) if normalized["water_level"] is not None and normalized["water_level"] != 0 else normalized["water_level"]
                },
                "status": status,
                "location": f"Embalse {reservoir_id}",
                "last_reading": last_reading_time.isoformat() if last_reading_time else None,
                "minutes_since_reading": int(minutes_diff)
            }
            
            sensors.append(sensor_data)
        
        return sensors
        
    except Exception as e:
        logger.error(f"Error obteniendo sensores individuales: {e}")
        return []


@router.get("/metrics/latest")
async def get_latest_metrics(
    reservoir_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get latest sensor metrics
    
    Args:
        reservoir_id: Optional filter by reservoir ID
    """
    # Intentar obtener desde caché
    cache_key = f"metrics_latest_{reservoir_id or 'all'}"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        query = {}
        if reservoir_id:
            query["reservoirId"] = reservoir_id
        
        # Get latest reading
        latest_reading = await sensor_collection.find_one(
            query,
            sort=[("ReadTime", -1)]
        )
        
        if not latest_reading:
            result = {
                "temperature": 0,
                "ph": 0,
                "conductivity": 0,
                "water_level": 0,
                "timestamp": None,
                "reservoir_id": reservoir_id
            }
        else:
            # Normalizar campos usando la función helper
            normalized = normalize_sensor_reading(latest_reading)
            
            result = {
                "temperature": normalized["temperature"],
                "ph": normalized["ph"],
                "conductivity": normalized["ec"],
                "water_level": normalized["water_level"],
                "timestamp": normalized["timestamp"],
                "reservoir_id": latest_reading.get("reservoirId")
            }
        
        # Guardar en caché por 30 segundos
        await cache_service.set(cache_key, result, ttl=30)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return {
            "temperature": 0,
            "ph": 0,
            "conductivity": 0,
            "water_level": 0,
            "timestamp": None,
            "reservoir_id": reservoir_id
        }


@router.get("/charts/historical-data")
async def get_historical_data(
    reservoir_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=0, le=8760),
    current_user: dict = Depends(get_current_user)
):
    """
    Get historical sensor data for charts
    
    Args:
        reservoir_id: Optional filter by reservoir ID
        hours: Number of hours to retrieve (0 = all data, max 8760 = 1 year)
    """
    try:
        query: Dict[str, Any] = {}
        if reservoir_id:
            query["reservoirId"] = reservoir_id
        
        # Get data from last N hours (0 = all data)
        if hours > 0:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query["ReadTime"] = {"$gte": start_time}
        
        # Fetch data
        cursor = sensor_collection.find(query).sort("ReadTime", 1).limit(1000)
        readings = await cursor.to_list(length=1000)
        
        # Format data for charts - separate arrays for each sensor type
        labels = []
        temperatura_data = []
        ph_data = []
        conductividad_data = []
        nivel_agua_data = []
        
        for reading in readings:
            # Normalizar datos
            normalized = normalize_sensor_reading(reading)
            
            # Format timestamp - convertir UTC a hora de Chile (UTC-3)
            timestamp = normalized["timestamp"]
            if timestamp:
                # Si es datetime, convertir a hora de Chile
                if hasattr(timestamp, 'isoformat'):
                    # Si el timestamp no tiene timezone, asumimos UTC
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    # Convertir a hora de Chile (UTC-3)
                    chile_time = timestamp.astimezone(timezone(CHILE_OFFSET))
                    # Enviar como ISO string sin timezone info para que el frontend no lo reconvierta
                    labels.append(chile_time.strftime('%Y-%m-%dT%H:%M:%S'))
                # Si ya es string, intentar parsearlo y convertirlo
                elif isinstance(timestamp, str):
                    try:
                        # Parse ISO string
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
            
            # Extract values using normalized fields - usar solo formato nuevo
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
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        return {
            "labels": [],
            "temperatura": [],
            "ph": [],
            "conductividad": [],
            "nivel_agua": [],
            "count": 0,
            "period_hours": hours
        }


@router.get("/sensors/status")
async def get_sensors_status(current_user: dict = Depends(get_current_user)):
    """
    Get current status of all sensors
    
    Returns summary of online/offline sensors
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Get unique sensors
        pipeline = [
            {"$sort": {"ReadTime": -1}},
            {"$group": {
                "_id": "$reservoirId",
                "lastReading": {"$first": "$$ROOT"}
            }}
        ]
        
        db_sensors = await sensor_collection.aggregate(pipeline).to_list(length=None)
        
        online_count = 0
        offline_count = 0
        warning_count = 0
        
        for sensor_group in db_sensors:
            latest_reading = sensor_group["lastReading"]
            last_reading_time = latest_reading["ReadTime"]
            
            if last_reading_time.tzinfo is None:
                last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            minutes_diff = (current_time - last_reading_time).total_seconds() / 60
            
            if minutes_diff < 15:
                online_count += 1
            elif minutes_diff < 30:
                warning_count += 1
            else:
                offline_count += 1
        
        return {
            "online": online_count,
            "warning": warning_count,
            "offline": offline_count,
            "total": online_count + warning_count + offline_count
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de sensores: {e}")
        return {
            "online": 0,
            "warning": 0,
            "offline": 0,
            "total": 0
        }


@router.get("/sensors/predict/{sensor_type}")
async def get_sensor_prediction(
    sensor_type: str,
    days: int = Query(5, ge=1, le=30, description="Number of days to predict"),
    lookback_days: int = Query(7, ge=1, le=90, description="Days of historical data to use"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get prediction for pH or conductivity values for next N days
    
    Uses linear regression on historical data to predict future values.
    
    Args:
        sensor_type: Type of sensor ('ph' or 'conductivity')
        days: Number of days to predict (1-30, default: 5)
        lookback_days: Days of historical data to use for training (1-90, default: 7)
        
    Returns:
        Predictions with timestamps, values, and model statistics
        
    Example response:
        {
            "success": true,
            "sensor_type": "ph",
            "predictions": [
                {"timestamp": "2025-11-04T...", "value": 6.8, "day_ahead": 1},
                ...
            ],
            "model_stats": {
                "r2_score": 0.95,
                "training_samples": 144,
                "lookback_days": 7
            },
            "last_reading": {
                "timestamp": "2025-11-03T...",
                "value": 6.7
            }
        }
    """
    try:
        # Validate sensor type
        valid_types = ['ph', 'conductivity']
        if sensor_type not in valid_types:
            return {
                "success": False,
                "message": f"Tipo de sensor inválido. Debe ser: {', '.join(valid_types)}",
                "predictions": []
            }
        
        # Get predictions
        result = await predict_sensor_values(
            sensor_collection=sensor_collection,
            sensor_type=sensor_type,
            days_to_predict=days,
            lookback_days=lookback_days
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en endpoint de predicción: {e}")
        return {
            "success": False,
            "message": f"Error generando predicción: {str(e)}",
            "predictions": []
        }


@router.post("/sensors/prediction-config")
async def save_prediction_config(
    config: PredictionRequest,
    request: Request,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Save prediction model configuration and log to audit
    
    This endpoint saves the prediction model parameters and creates an audit log entry.
    Uses validated PredictionRequest model with built-in range checks.
    """
    try:
        # Validation is automatic via PredictionRequest model
        
        # Log to audit
        await log_audit_event(
            action=AuditAction.PREDICTION_CONFIG_UPDATED,
            description=f"Configuración del modelo de predicción actualizada para {config.sensor_type}",
            user_id=current_user.get("user_id"),
            user_email=current_user.get("email"),
            resource_type="prediction_model",
            resource_id=config.sensor_type,
            details={
                "sensor_type": config.sensor_type,
                "days_to_predict": config.days,
                "lookback_days": config.lookback_days,
                "previous_days": 5,  # Default value
                "previous_lookback": 7  # Default value
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        logger.info(f"Prediction config updated by {current_user.get('email')}: {config.sensor_type} - days={config.days}, lookback={config.lookback_days}")
        
        return {
            "success": True,
            "message": "Configuración guardada exitosamente",
            "config": {
                "sensor_type": config.sensor_type,
                "days": config.days,
                "lookback_days": config.lookback_days
            }
        }
        
    except Exception as e:
        logger.error(f"Error saving prediction config: {e}")
        return {
            "success": False,
            "message": f"Error al guardar configuración: {str(e)}"
        }


@router.get("/sensors/list")
async def get_sensors_list(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener lista de sensores con su configuración de alertas
    """
    try:
        from app.config import db
        sensors_collection = db["sensors"]
        
        # Obtener todos los sensores
        sensors_cursor = sensors_collection.find({})
        sensors = await sensors_cursor.to_list(length=100)
        
        # Formatear respuesta
        sensors_list = []
        for sensor in sensors:
            sensor_data = {
                "sensor_id": sensor.get("sensor_id"),
                "name": sensor.get("name", sensor.get("sensor_id")),
                "location": sensor.get("location", "N/A"),
                "type": sensor.get("type", "IoT_Monitoring"),
                "status": sensor.get("status", "active"),
                "alert_config": sensor.get("alert_config", {
                    "enabled": False,
                    "parameters": {},
                    "notification_enabled": False,
                    "whatsapp_enabled": False,
                    "email_enabled": False
                })
            }
            sensors_list.append(sensor_data)
        
        return {
            "success": True,
            "sensors": sensors_list,
            "total": len(sensors_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting sensors list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sensors/alert-config")
async def update_sensor_alert_config(
    request: Request,
    config_request: UpdateSensorAlertConfigRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Actualizar configuración de alertas para un sensor específico (solo admin)
    """
    try:
        from app.config import db
        sensors_collection = db["sensors"]
        
        sensor_id = config_request.sensor_id
        alert_config = config_request.alert_config.model_dump()
        
        # Verificar que el sensor existe
        sensor = await sensors_collection.find_one({"sensor_id": sensor_id})
        if not sensor:
            raise HTTPException(
                status_code=404,
                detail=f"Sensor {sensor_id} no encontrado"
            )
        
        # Actualizar configuración
        result = await sensors_collection.update_one(
            {"sensor_id": sensor_id},
            {
                "$set": {
                    "alert_config": alert_config,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"No se modificó la configuración del sensor {sensor_id}")
        
        # Log de auditoría
        await log_audit_event(
            action=AuditAction.ALERT_CONFIG_UPDATE,
            description=f"Configuración de alertas actualizada para sensor {sensor_id}",
            user_email=admin_user.get('email'),
            user_id=str(admin_user.get('_id')) if admin_user.get('_id') else None,
            resource_type="sensor_alert_config",
            resource_id=sensor_id,
            details=alert_config,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        logger.info(
            f"Configuración de alertas actualizada por {admin_user.get('email')} "
            f"para sensor {sensor_id}"
        )
        
        return {
            "success": True,
            "message": f"Configuración de alertas actualizada para {sensor_id}",
            "sensor_id": sensor_id,
            "alert_config": alert_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sensor alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/{sensor_id}/alert-config")
async def get_sensor_alert_config(
    sensor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener configuración de alertas de un sensor específico
    """
    try:
        from app.config import db
        sensors_collection = db["sensors"]
        
        sensor = await sensors_collection.find_one({"sensor_id": sensor_id})
        
        if not sensor:
            raise HTTPException(
                status_code=404,
                detail=f"Sensor {sensor_id} no encontrado"
            )
        
        alert_config = sensor.get("alert_config", {
            "enabled": False,
            "parameters": {},
            "notification_enabled": False,
            "whatsapp_enabled": False,
            "email_enabled": False
        })
        
        return {
            "success": True,
            "sensor_id": sensor_id,
            "name": sensor.get("name", sensor_id),
            "alert_config": alert_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sensor alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
