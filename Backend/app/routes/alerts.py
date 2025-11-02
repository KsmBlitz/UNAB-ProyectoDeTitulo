"""
Alerts routes  
Alert management, configuration, and history endpoints
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging

# Import alert models from existing models directory
import sys
sys.path.append('/app')
from models.alert_models import (
    AlertThresholds, ActiveAlert, AlertHistory, AlertSummary,
    AlertConfigUpdateRequest, DismissAlertRequest, AlertStatus
)

from app.config import (
    alerts_collection,
    alert_history_collection,
    alert_thresholds_collection
)
from app.utils import get_current_user, get_current_admin_user
from app.services import clear_notifications_sent_for_alert

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
        # Query for unresolved alerts
        cursor = alerts_collection.find({"is_resolved": False})
        cursor = cursor.sort("created_at", -1)
        
        alerts_list = await cursor.to_list(length=100)
        
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
        
        logger.info(f"Retornando {len(active_alerts)} alertas activas")
        return active_alerts
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas activas: {e}")
        return []


@router.post("/dismiss")
async def dismiss_alert(
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
            f"Intentando cerrar alerta con ID: {request.alert_id} "
            f"(tipo: {type(request.alert_id).__name__})"
        )
        
        # Alerts may have ID in different fields:
        # - System alerts: "id" field
        # - Manual alerts: only "_id" field
        # Search by both fields
        alert_doc = await alerts_collection.find_one({
            "$or": [
                {"_id": request.alert_id},
                {"id": request.alert_id}
            ]
        })
        
        if not alert_doc:
            # Debug: show example IDs
            all_alerts = await alerts_collection.find(
                {"is_resolved": False}
            ).limit(5).to_list(length=5)
            logger.warning(
                f"Alerta no encontrada. Ejemplos de IDs en BD: "
                f"{[str(a.get('_id', a.get('id', 'sin-id'))) for a in all_alerts]}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Alerta no encontrada con ID: {request.alert_id}"
            )
        
        # Check if already resolved
        if alert_doc.get("is_resolved", False):
            raise HTTPException(
                status_code=400,
                detail="La alerta ya está resuelta"
            )
        
        current_time = datetime.now(timezone.utc)
        
        # Mark as resolved using real _id from document
        alert_identifier = alert_doc.get("_id")
        update_result = await alerts_collection.update_one(
            {"_id": alert_identifier},
            {
                "$set": {
                    "is_resolved": True,
                    "status": AlertStatus.DISMISSED,
                    "dismissed_by": user_email,
                    "dismissed_at": current_time,
                    "resolution_type": "manual_dismiss"
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No se pudo cerrar la alerta"
            )
        
        # Ensure created_at is timezone-aware for calculations
        created_at = alert_doc["created_at"]
        
        # If created_at is a string (manual alerts), convert to datetime
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
                created_at = created_at.replace(tzinfo=timezone.utc)
        elif hasattr(created_at, 'tzinfo') and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        # Add to history
        try:
            history_dict = {
                "alert_id": request.alert_id,
                "type": alert_doc["type"],
                "level": alert_doc["level"],
                "title": alert_doc["title"],
                "message": alert_doc["message"],
                "value": alert_doc.get("value"),
                "threshold_info": alert_doc["threshold_info"],
                "location": alert_doc["location"],
                "sensor_id": alert_doc.get("sensor_id"),
                "created_at": created_at,
                "dismissed_at": current_time,
                "dismissed_by": user_email,
                "dismissed_by_role": user_role,
                "resolution_type": "manual_dismiss",
                "duration_minutes": int((current_time - created_at).total_seconds() / 60)
            }
            
            await alert_history_collection.insert_one(history_dict)
            
        except Exception as history_error:
            logger.error(f"Error insertando en historial: {history_error}")
            # Don't fail dismiss due to history error
        
        # Clear notification throttling for this alert
        await clear_notifications_for_alert(request.alert_id)
        
        logger.info(f"Alerta {request.alert_id} cerrada por {user_email} ({user_role})")
        
        return {
            "message": "Alerta cerrada exitosamente",
            "dismissed_at": current_time.isoformat(),
            "dismissed_by": user_email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cerrando alerta: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
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
        cursor = alert_history_collection.find().sort("dismissed_at", -1).limit(limit)
        history_list = await cursor.to_list(length=limit)
        
        # Convert to AlertHistory models
        history_items = []
        for item in history_list:
            try:
                # Convert ObjectId to string if present
                if "_id" in item:
                    item["_id"] = str(item["_id"])
                history_items.append(AlertHistory(**item))
            except Exception as model_error:
                logger.error(f"Error converting history item: {model_error}")
                continue
        
        return history_items
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []


@router.delete("/history/clear")
async def clear_alert_history(admin_user: dict = Depends(get_current_admin_user)):
    """
    Clear all alert history (admin only)
    
    Permanently deletes all records from alert history.
    """
    try:
        result = await alert_history_collection.delete_many({})
        
        # Eliminar registros del historial
        result = await alerts_collection.delete_many(query)
        
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
        # Count active alerts by level
        pipeline = [
            {"$match": {"is_resolved": False}},
            {"$group": {
                "_id": "$level",
                "count": {"$sum": 1}
            }}
        ]
        
        level_counts = await alerts_collection.aggregate(pipeline).to_list(length=None)
        
        # Count by type
        pipeline_type = [
            {"$match": {"is_resolved": False}},
            {"$group": {
                "_id": "$type",
                "count": {"$sum": 1}
            }}
        ]
        
        type_counts = await alerts_collection.aggregate(pipeline_type).to_list(length=None)
        
        # Format results
        by_level = {item["_id"]: item["count"] for item in level_counts}
        by_type = {item["_id"]: item["count"] for item in type_counts}
        
        total = sum(by_level.values())
        
        return {
            "total_active": total,
            "by_level": by_level,
            "by_type": by_type
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de alertas: {e}")
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
    config: AlertConfigUpdateRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Update alert thresholds configuration (admin only)
    """
    try:
        # Upsert configuration
        await alert_thresholds_collection.update_one(
            {},
            {"$set": {"config": config.model_dump()}},
            upsert=True
        )
        
        logger.info(f"Configuración de alertas actualizada por {admin_user.get('email')}")
        
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
