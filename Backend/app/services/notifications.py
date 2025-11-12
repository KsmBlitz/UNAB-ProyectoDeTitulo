"""
Alert notification service
Alert throttling and notification management
"""

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import settings, notifications_sent_collection

logger = logging.getLogger(__name__)


async def should_send_notification(key: str) -> bool:
    """
    Check if a notification should be sent based on throttling rules
    
    Uses the notifications_sent collection to track when notifications
    were last sent and enforce a cooldown period.
    
    Args:
        key: Unique notification key (e.g., "email:temperature:sensor1:user@example.com")
        
    Returns:
        True if notification should be sent, False if throttled
    """
    try:
        rec = await notifications_sent_collection.find_one({"_id": key})
        
        if not rec:
            return True
        
        last_sent = rec.get("last_sent")
        if not last_sent:
            return True
        
        # Handle both string and datetime formats
        if isinstance(last_sent, str):
            try:
                last_dt = datetime.fromisoformat(last_sent)
            except Exception:
                return True
        elif isinstance(last_sent, datetime):
            last_dt = last_sent
        else:
            return True

        # Ensure last_dt is timezone-aware for comparison
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)

        # Check if enough time has passed (default 60 minutes)
        throttle_minutes = getattr(settings, "ALERT_EMAIL_THROTTLE_MINUTES", 60) or 60
        time_since_last = datetime.now(timezone.utc) - last_dt
        
        return time_since_last > timedelta(minutes=throttle_minutes)
        
    except Exception as e:
        logger.error(f"Error comprobando throttle de notificación: {e}")
        return True  # On error, allow sending


async def mark_notification_sent(key: str) -> None:
    """
    Mark a notification as sent (updates throttling timestamp)
    
    Args:
        key: Unique notification key to mark as sent
    """
    try:
        await notifications_sent_collection.update_one(
            {"_id": key},
            {"$set": {"last_sent": datetime.now(timezone.utc)}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error marcando notificación enviada: {e}")


async def clear_notifications_sent_for_alert(
    alert_type: str,
    sensor_id: Optional[str] = None
) -> None:
    """
    Clear notification throttling records when an alert is resolved
    
    This removes all throttling entries for a specific alert type and sensor,
    allowing notifications to be sent immediately if the alert reoccurs.
    
    Args:
        alert_type: Type of alert (e.g., "temperature", "ph_range")
        sensor_id: Optional sensor identifier
    """
    try:
        # Build regex pattern to match all notification keys for this alert
        if sensor_id:
            pattern = f"^{re.escape(str(alert_type))}:{re.escape(str(sensor_id))}:"
        else:
            pattern = f"^{re.escape(str(alert_type))}:"
        
        result = await notifications_sent_collection.delete_many(
            {"_id": {"$regex": pattern}}
        )
        
        logger.info(
            f"Throttle cleared for alert {alert_type} sensor {sensor_id} "
            f"({result.deleted_count} records)"
        )
        
    except Exception as e:
        logger.error(
            f"Error limpiando notifications_sent para alerta "
            f"{alert_type}/{sensor_id}: {e}"
        )


def build_notification_key(
    channel: str,
    alert_type: str,
    sensor_id: str,
    recipient: str
) -> str:
    """
    Build a unique notification key for throttling
    
    Args:
        channel: Notification channel ("email", "sms", "whatsapp")
        alert_type: Type of alert
        sensor_id: Sensor identifier
        recipient: Recipient identifier (email/phone)
        
    Returns:
        Unique key string for throttling
        
    Example:
        >>> build_notification_key("email", "temperature", "sensor1", "user@example.com")
        "email:temperature:sensor1:user@example.com"
    """
    return f"{channel}:{alert_type}:{sensor_id}:{recipient}"
