"""
Alert Change Stream Watcher
MongoDB change stream monitoring for real-time alert notifications
"""

import asyncio
import logging
from typing import Dict, Any

from app.config import alerts_collection, users_collection
from app.services import (
    send_critical_alert_email,
    should_send_notification,
    mark_notification_sent,
    build_notification_key
)
from app.services.twilio_whatsapp import send_critical_alert_twilio_whatsapp

logger = logging.getLogger(__name__)


async def alert_change_stream_watcher():
    """
    Watch for new alerts inserted into MongoDB and notify admins immediately
    
    Uses MongoDB change stream on the alerts collection to detect inserts in real-time.
    Sends notifications via email and WhatsApp to all admins with notifications enabled.
    Includes retry/backoff logic for resilience.
    """
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
    Send notifications to all admins for a critical alert
    
    Respects user notification preferences and throttling rules.
    Sends via email and WhatsApp (if configured).
    
    Args:
        alert_doc: Alert document from MongoDB
    """
    try:
        # Get all active admins
        admins = await users_collection.find({
            "role": "admin",
            "disabled": {"$ne": True}
        }).to_list(1000)
        
        alert_location = alert_doc.get("location") or alert_doc.get("sensor_id") or "Embalse"
        alert_title = alert_doc.get("title") or alert_doc.get("type")
        alert_value = str(alert_doc.get("value", "N/A"))
        alert_type = alert_doc.get("type")
        sensor_id = alert_doc.get("sensor_id")
        
        for admin in admins:
            email = admin.get("email")
            if not email:
                continue
            
            # Check if notifications are enabled for this user
            if admin.get("notifications_enabled", True) is False:
                continue
            
            user_id = str(admin.get("_id"))
            
            # Send EMAIL notification
            await send_email_notification(
                email=email,
                user_id=user_id,
                alert_type=alert_type,
                sensor_id=sensor_id,
                location=alert_location,
                title=alert_title,
                value=alert_value
            )
            
            # Send WhatsApp notification (if configured)
            phone = admin.get("phone")
            whatsapp_enabled = admin.get("whatsapp_notifications_enabled", False)
            
            if phone and whatsapp_enabled:
                await send_whatsapp_notification(
                    phone=phone,
                    user_id=user_id,
                    alert_type=alert_type,
                    sensor_id=sensor_id,
                    location=alert_location,
                    title=alert_title,
                    value=alert_value
                )
                
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
    """Send WhatsApp notification via Twilio with throttling"""
    try:
        notification_key = build_notification_key("whatsapp", alert_type, sensor_id, user_id)
        
        if await should_send_notification(notification_key):
            sent = await send_critical_alert_twilio_whatsapp(phone, location, alert_type, value)
            if sent:
                await mark_notification_sent(notification_key)
                logger.info(f"WhatsApp (Twilio) enviado a {phone} para alerta {alert_type}")
                
    except Exception as e:
        logger.error(f"Error enviando WhatsApp (Twilio) a {phone}: {e}")
