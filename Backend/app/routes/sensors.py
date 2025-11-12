"""
Sensors routes
Sensor data and metrics endpoints
Refactored to use SensorService for business logic
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel
import logging

from app.utils import get_current_user, get_current_admin_user
from app.services.sensor_service import sensor_service
from app.services.audit import log_audit_event
from app.services.cache import cache_service
from app.models.audit_models import AuditAction
from app.models.sensor_models import PredictionRequest, TimeRangeQuery
from app.models.alert_models import UpdateSensorAlertConfigRequest

logger = logging.getLogger(__name__)

# Timezone offset for Chile (UTC-3)
CHILE_OFFSET = timedelta(hours=-3)

router = APIRouter(prefix="/api", tags=["Datos de Sensores"])


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
        sensors = await sensor_service.get_sensor_status()
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
    try:
        result = await sensor_service.get_latest_metrics(reservoir_id=reservoir_id)
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
        result = await sensor_service.get_historical_data(
            reservoir_id=reservoir_id,
            hours=hours
        )
        return result
        
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
        # Use sensor_service to get all sensor statuses
        sensors = await sensor_service.get_sensor_status()
        
        # Count statuses
        online_count = sum(1 for s in sensors if s.get("status") == "online")
        warning_count = sum(1 for s in sensors if s.get("status") == "warning")
        offline_count = sum(1 for s in sensors if s.get("status") == "offline")
        
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
        
        # Get predictions using sensor_service
        result = await sensor_service.predict_sensor_value(
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
    Update alert configuration for a specific sensor (admin only)
    """
    try:
        sensor_id = config_request.sensor_id
        alert_config = config_request.alert_config.model_dump()
        
        # Delegate to sensor service
        updated_sensor = await sensor_service.update_sensor_alert_config(
            sensor_id=sensor_id,
            alert_config=alert_config,
            updated_by=admin_user.get('email')
        )
        
        # Log audit event
        await log_audit_event(
            action=AuditAction.ALERT_CONFIG_UPDATE,
            description=f"Alert configuration updated for sensor {sensor_id}",
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
            f"Alert configuration updated by {admin_user.get('email')} "
            f"for sensor {sensor_id}"
        )
        
        return {
            "success": True,
            "message": f"Alert configuration updated for {sensor_id}",
            "sensor_id": sensor_id,
            "alert_config": alert_config
        }
        
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except RuntimeError as re:
        logger.error(f"Runtime error: {re}")
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        logger.error(f"Error updating sensor alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/{sensor_id}/alert-config")
async def get_sensor_alert_config(
    sensor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get alert configuration for a specific sensor
    """
    try:
        # Delegate to sensor service
        config_data = await sensor_service.get_sensor_alert_config(sensor_id)
        
        return {
            "sensor_id": sensor_id,
            "alert_config": config_data["alert_config"]
        }
        
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting sensor alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
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
