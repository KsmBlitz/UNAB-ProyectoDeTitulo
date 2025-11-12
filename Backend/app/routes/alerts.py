"""
Alerts routes  
Alert management, configuration, and history endpoints
Refactored to follow SOLID principles - delegates business logic to AlertService
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
import logging

# Import alert models
from app.models.alert_models import (
    AlertThresholds, ActiveAlert, AlertHistory, AlertSummary,
    AlertConfigUpdateRequest, DismissAlertRequest, AlertStatus
)

from app.config import (
    alert_history_collection,
    alert_thresholds_collection
)
from app.utils import get_current_user, get_current_admin_user
from app.services.alert_service import alert_service
from app.services.audit import log_audit_event
from app.models.audit_models import AuditAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Alertas"])


@router.get("/active")
async def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """
    Get all active (unresolved) alerts
    
    Returns:
        List of active alerts sorted by creation time (newest first)
    """
    try:
        # Delegate to alert service
        alerts_list = await alert_service.get_active_alerts(limit=100)
        
        # Convert to ActiveAlert models
        active_alerts = []
        for alert in alerts_list:
            try:
                # Use either _id or id field
                alert_id = alert.get("id", str(alert.get("_id")))
                alert["id"] = alert_id
                active_alerts.append(ActiveAlert(**alert))
            except Exception as model_error:
                logger.error(f"Error converting alert to model: {model_error}")
                continue
        
        logger.info(f"Returning {len(active_alerts)} active alerts")
        return active_alerts
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return []


@router.post("/dismiss")
async def dismiss_alert(
    fastapi_request: Request,
    request: DismissAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Dismiss/close an alert
    
    Marks alert as resolved and moves it to history.
    Available to operators and admins.
    """
    user_email = current_user.get("email")
    user_role = current_user.get("role", "operario")
    
    try:
        logger.info(
            f"Attempting to dismiss alert ID: {request.alert_id} "
            f"by user: {user_email}"
        )
        
        # Get client IP and user agent for audit
        client_ip = fastapi_request.client.host if fastapi_request.client else None
        user_agent = fastapi_request.headers.get("user-agent", None)
        
        # Delegate to alert service (contains all business logic)
        result = await alert_service.dismiss_alert(
            alert_id=request.alert_id,
            user_email=user_email,
            user_role=user_role,
            reason=getattr(request, 'reason', None),
            ip_address=client_ip
        )
        
        # Log audit event
        await log_audit_event(
            action=AuditAction.ALERT_DISMISSED,
            description=f"Alert dismissed: {request.alert_id}",
            user_email=user_email,
            user_id=str(current_user.get('_id')) if current_user.get('_id') else None,
            resource_type="alert",
            resource_id=str(request.alert_id),
            details={
                "alert_id": str(request.alert_id)
            },
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(f"Alert {request.alert_id} dismissed by {user_email} ({user_role})")
        return result
        
    except ValueError as ve:
        # Business validation errors (alert not found, already resolved)
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(
            status_code=400 if "already resolved" in str(ve) else 404,
            detail=str(ve)
        )
    except RuntimeError as re:
        # Service errors (database failures, etc)
        logger.error(f"Runtime error dismissing alert: {re}")
        raise HTTPException(
            status_code=500,
            detail="Failed to dismiss alert"
        )
    except Exception as e:
        logger.error(f"Unexpected error dismissing alert: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/history")
async def get_alert_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    Get alert history
    
    Args:
        limit: Maximum number of records to return (1-200)
    """
    try:
        # Delegate to alert service
        history_list = await alert_service.get_alert_history(limit=limit)
        
        # Convert to AlertHistory models
        history_items = []
        for item in history_list:
            try:
                history_items.append(AlertHistory(**item))
            except Exception as model_error:
                logger.error(f"Error converting history item: {model_error}")
                continue
        
        return history_items
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return []


@router.delete("/history/clear")
async def clear_alert_history(admin_user: dict = Depends(get_current_admin_user)):
    """
    Clear all alert history (admin only)
    
    Permanently deletes all records from alert history.
    """
    try:
        # Eliminar todos los registros del historial
        result = await alert_history_collection.delete_many({})
        
        logger.info(f"Historial limpiado: {result.deleted_count} registros eliminados")
        
        return {
            "message": "Historial de alertas limpiado",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/summary")
async def get_alert_summary(current_user: dict = Depends(get_current_user)):
    """
    Get alert statistics summary
    
    Returns counts of active alerts by level and type.
    """
    try:
        # Delegate to alert service
        summary = await alert_service.get_alert_statistics()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting alert summary: {e}")
        return {
            "total_active": 0,
            "by_level": {},
            "by_type": {}
        }


@router.get("/config")
async def get_alert_config(current_user: dict = Depends(get_current_user)):
    """
    Get current alert thresholds configuration
    """
    try:
        config = await alert_thresholds_collection.find_one()
        
        if not config:
            # Return default configuration
            return {
                "ph_range": {"min": 6.5, "max": 8.5},
                "temperature_max": 25.0,
                "conductivity_max": 1500.0
            }
        
        # Eliminar el _id de MongoDB antes de retornar
        if "_id" in config:
            del config["_id"]
        
        return config
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        return {
            "ph_range": {"min": 6.5, "max": 8.5},
            "temperature_max": 25.0,
            "conductivity_max": 1500.0
        }


@router.put("/config")
async def update_alert_config(
    request: Request,
    config: AlertConfigUpdateRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Update alert thresholds configuration (admin only)
    """
    try:
        # Convertir el modelo a diccionario
        config_dict = config.model_dump()
        
        # Upsert configuration - guardar directamente los campos, no anidados
        await alert_thresholds_collection.update_one(
            {},
            {"$set": config_dict},
            upsert=True
        )
        
        logger.info(f"Configuración de alertas actualizada por {admin_user.get('email')}")
        
        # Extraer IP del cliente
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        # Registrar en auditoría
        await log_audit_event(
            action=AuditAction.ALERT_CONFIG_UPDATE,
            description="Umbrales de alertas actualizados",
            user_email=admin_user.get('email'),
            user_id=str(admin_user.get('_id')) if admin_user.get('_id') else None,
            resource_type="alert_config",
            details=config_dict,
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        return {
            "message": "Configuración actualizada exitosamente",
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error actualizando configuración: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/create")
async def create_sensor_alert(
    alert_data: dict,
    request: Request
):
    """
    Create a sensor alert with automatic validation
    
    Validates that measurement alerts (pH, temp, EC, water_level) are only created
    for connected sensors. This endpoint is typically called by external systems
    (ESP32, monitoring scripts, etc).
    
    Required fields in alert_data:
    - type: Alert type (ph, temperature, ec, water_level, sensor_disconnected, etc)
    - sensor_id: Sensor identifier
    - level: Severity level (info, warning, critical)
    - title: Alert title
    - message: Alert message
    - location: Sensor location
    - value: (optional) Sensor reading value
    
    Returns:
        201: Alert created successfully
        400: Alert creation skipped (sensor disconnected for measurement alerts)
        422: Invalid request data
    """
    try:
        # Validate required fields
        required_fields = ['type', 'sensor_id', 'level', 'title', 'message', 'location']
        missing_fields = [f for f in required_fields if f not in alert_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        alert_type = alert_data['type']
        sensor_id = alert_data['sensor_id']
        
        # Check if alert should be created based on sensor status
        should_create, skip_reason = await alert_service.should_create_sensor_alert(
            alert_type=alert_type,
            sensor_id=sensor_id
        )
        
        if not should_create:
            logger.info(f"Skipping alert creation: {skip_reason}")
            return {
                "status": "skipped",
                "reason": skip_reason,
                "alert_type": alert_type,
                "sensor_id": sensor_id
            }
        
        # Create the alert
        from app.config import alerts_collection
        current_time = datetime.now(timezone.utc)
        
        alert_doc = {
            "type": alert_data['type'],
            "level": alert_data['level'].lower(),
            "title": alert_data['title'],
            "message": alert_data['message'],
            "location": alert_data['location'],
            "sensor_id": sensor_id,
            "created_at": current_time,
            "is_resolved": False,
            "status": "active",
            "source": alert_data.get('source', 'external')
        }
        
        # Add optional fields
        if 'value' in alert_data:
            alert_doc['value'] = alert_data['value']
        
        result = await alerts_collection.insert_one(alert_doc)
        alert_doc['_id'] = result.inserted_id
        alert_doc['id'] = str(result.inserted_id)
        
        logger.info(
            f"Sensor alert created: {alert_type} for sensor {sensor_id} "
            f"(level: {alert_data['level']})"
        )
        
        return {
            "status": "created",
            "alert_id": str(result.inserted_id),
            "alert": alert_doc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sensor alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating alert: {str(e)}"
        )
