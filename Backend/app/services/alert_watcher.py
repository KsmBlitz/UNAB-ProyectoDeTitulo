"""
Alert Change Stream Watcher
MongoDB change stream monitoring for real-time alert notifications
"""

import asyncio
import logging
import socket
import traceback
from typing import Dict, Any
from datetime import datetime, timezone

from app.repositories.alert_repository import alert_repository

logger = logging.getLogger(__name__)


async def alert_change_stream_watcher():
    """Watch for new alerts inserted into MongoDB and notify admins immediately."""
    from app.config import alerts_collection

    backoff = 1

    while True:
        try:
            async with alerts_collection.watch([
                {"$match": {"operationType": "insert"}}
            ]) as stream:
                logger.info("Alert change-stream watcher started")

                async for change in stream:
                    try:
                        full_document = change.get("fullDocument")
                        if not full_document:
                            continue

                        # Safety guard for measurement alerts inserted externally
                        alert_type = (full_document.get("type") or "").lower()
                        sensor_id = full_document.get("sensor_id")
                        measurement_types = [
                            "ph",
                            "ph_range",
                            "temperature",
                            "ec",
                            "water_level",
                            "conductivity",
                        ]

                        if alert_type in measurement_types and sensor_id:
                            try:
                                from app.services.sensor_service import sensor_service
                                from app.services.alert_service import alert_service

                                is_connected = await sensor_service.is_sensor_connected(sensor_id)
                                if not is_connected:
                                    alert_id = str(full_document.get("_id"))
                                    logger.info(
                                        f"Auto-archiving measurement alert {alert_id} for disconnected sensor {sensor_id}"
                                    )

                                    try:
                                        from app.config.database import db

                                        audit_coll = db.get_collection("alert_audit")
                                        task = asyncio.current_task()
                                        task_name = getattr(task, "get_name", lambda: None)()
                                        stack_frag = "".join(traceback.format_stack(limit=6))

                                        audit_doc = {
                                            "alert_id": alert_id,
                                            "detected_at": datetime.now(timezone.utc),
                                            "sensor_id": sensor_id,
                                            "alert_type": alert_type,
                                            "full_document": full_document,
                                            "is_connected": False,
                                            "action": "auto_dismiss_attempt",
                                            "hostname": socket.gethostname(),
                                            "task_name": task_name,
                                            "stack_fragment": stack_frag,
                                            "origin_source": full_document.get("source")
                                            if isinstance(full_document, dict)
                                            else None,
                                        }

                                        await audit_coll.insert_one(audit_doc)
                                    except Exception:
                                        logger.exception("Failed to write alert audit record")

                                    try:
                                        await alert_service.dismiss_alert(
                                            alert_id=alert_id,
                                            user_email="system@auto",
                                            user_role="system",
                                            reason=(
                                                "Auto-archived: sensor disconnected (change-stream safeguard)"
                                            ),
                                        )

                                        try:
                                            await audit_coll.update_one(
                                                {"alert_id": alert_id},
                                                {
                                                    "$set": {
                                                        "action": "auto_dismissed",
                                                        "action_at": datetime.now(timezone.utc),
                                                    }
                                                },
                                            )
                                        except Exception:
                                            logger.exception(
                                                "Failed to update audit record after dismiss"
                                            )
                                    except Exception:
                                        logger.exception(f"Failed to auto-dismiss alert {alert_id}")

                                    continue
                            except Exception:
                                logger.exception("Error running change-stream safety guard")

                        level = (full_document.get("level") or "").lower()
                        if level not in ("critical", "crítica", "crítico"):
                            continue

                        await notify_admins_of_alert(full_document)

                    except Exception as process_error:
                        logger.error(f"Error procesando cambio de alerta: {process_error}")

            backoff = 1

        except Exception as watcher_error:
            logger.error(f"Error en alert_change_stream_watcher: {watcher_error}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def notify_admins_of_alert(alert_doc: Dict[str, Any]) -> None:
    """Send notifications to all admins for a critical alert."""
    try:
        alert_location = alert_doc.get("location") or alert_doc.get("sensor_id") or "Embalse"
        alert_title = alert_doc.get("title") or alert_doc.get("type")
        alert_value = str(alert_doc.get("value", "N/A"))
        alert_type = alert_doc.get("type")
        sensor_id = alert_doc.get("sensor_id")

        from app.services.notification_service import notification_service

        alert_payload = {
            "type": alert_type or "unknown",
            "sensor_id": sensor_id or "unknown",
            "location": alert_location,
            "title": alert_title,
            "value": alert_value,
        }

        await notification_service.notify_admins(alert_payload)

    except Exception as notify_error:
        logger.error(f"Error notificando admins: {notify_error}")


async def send_email_notification(
    email: str,
    user_id: str,
    alert_type: str,
    sensor_id: str,
    location: str,
    title: str,
    value: str
) -> None:
    """Send email notification with throttling"""
    try:
        notification_key = build_notification_key("email", alert_type, sensor_id, user_id)
        
        if await should_send_notification(notification_key):
            sent = await send_critical_alert_email(email, location, title, value)
            if sent:
                await mark_notification_sent(notification_key)
                logger.info(f"Email enviado a {email} para alerta {alert_type}")
                
    except Exception as e:
        logger.error(f"Error enviando email a {email}: {e}")


async def send_whatsapp_notification(
    phone: str,
    user_id: str,
    alert_type: str,
    sensor_id: str,
    location: str,
    title: str,
    value: str
) -> None:
    """Send WhatsApp notification with throttling"""
    try:
        notification_key = build_notification_key("whatsapp", alert_type, sensor_id, user_id)
        
        if await should_send_notification(notification_key):
            sent = await send_critical_alert_whatsapp(phone, location, alert_type, value)
            if sent:
                await mark_notification_sent(notification_key)
                logger.info(f"WhatsApp enviado a {phone} para alerta {alert_type}")
                
    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {phone}: {e}")
