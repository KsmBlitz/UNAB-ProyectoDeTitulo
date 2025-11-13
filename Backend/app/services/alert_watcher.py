"""
Alert Change Stream Watcher
MongoDB change stream monitoring for real-time alert notifications
Refactored to follow SOLID principles
"""

import asyncio
import logging
from typing import Dict, Any

from app.repositories.alert_repository import alert_repository
from app.services.notification_service import notification_service, NotificationType

logger = logging.getLogger(__name__)


async def alert_change_stream_watcher():
    """
    Watch for new alerts inserted into MongoDB and notify admins immediately
    
    Uses MongoDB change stream on the alerts collection to detect inserts in real-time.
    Sends notifications via email and WhatsApp to all admins with notifications enabled.
    Includes retry/backoff logic for resilience.
    """
    from app.config import alerts_collection
    backoff = 1
    
    while True:
        try:
            # Watch only insert operations on alerts collection
            async with alerts_collection.watch([{"$match": {"operationType": "insert"}}]) as stream:
                logger.info("Alert change-stream watcher started")
                
                async for change in stream:
                    try:
                        full_document = change.get("fullDocument")
                        if not full_document:
                            continue
                        
                        # Process only critical alerts
                        level = (full_document.get("level") or "").lower()
                        if level not in ("critical", "crítica", "crítico"):
                            continue
                        
                        # Notify all admins with notifications enabled
                        await notify_admins_of_alert(full_document)
                        
                    except Exception as process_error:
                        logger.error(f"Error procesando cambio de alerta: {process_error}")
            
            # If stream exits normally, reset backoff
            backoff = 1
            
        except Exception as watcher_error:
            logger.error(f"Error en alert_change_stream_watcher: {watcher_error}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)  # Exponential backoff, max 60 seconds


async def notify_admins_of_alert(alert_doc: Dict[str, Any]) -> None:
    """
    Send notifications to all admins for a critical alert using unified notification service
    
    Args:
        alert_doc: Alert document from MongoDB
    """
    try:
        alert_location = alert_doc.get("location") or alert_doc.get("sensor_id") or "Embalse"
        alert_title = alert_doc.get("title") or alert_doc.get("type")
        alert_value = str(alert_doc.get("value", "N/A"))
        alert_type = alert_doc.get("type")
        sensor_id = alert_doc.get("sensor_id")
        
        # Use unified notification service to handle all channels
        from app.services.notification_service import notification_service

        alert_payload = {
            "type": alert_type or "unknown",
            "sensor_id": sensor_id or "unknown",
            "location": alert_location,
            "title": alert_title,
            "value": alert_value
        }

        await notification_service.notify_admins(alert_payload)
                
    except Exception as notify_error:
        logger.error(f"Error notificando admins: {notify_error}")
