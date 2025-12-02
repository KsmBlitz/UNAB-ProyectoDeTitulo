"""
Notification Service
Unified notification handling following Single Responsibility Principle
Orchestrates email and WhatsApp notifications with throttling
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.email import send_critical_alert_email
from app.services.twilio_whatsapp import send_critical_alert_twilio_whatsapp
from app.repositories.user_repository import user_repository
from app.config import notifications_sent_collection, embalses_collection, users_collection

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification channel types"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"


class NotificationService:
    """
    Service for managing multi-channel notifications
    Implements throttling to prevent spam
    """
    
    def __init__(self, throttle_minutes: int = 15):
        """
        Initialize notification service
        
        Args:
            throttle_minutes: Minimum minutes between notifications
        """
        self.throttle_minutes = throttle_minutes
    
    def _build_notification_key(
        self,
        channel: NotificationType,
        alert_type: str,
        sensor_id: str,
        user_id: str
    ) -> str:
        """
        Build unique notification key for throttling
        
        Args:
            channel: Notification channel
            alert_type: Type of alert
            sensor_id: Sensor identifier
            user_id: User identifier
            
        Returns:
            Unique notification key
        """
        return f"{channel}:{alert_type}:{sensor_id}:{user_id}"
    
    async def _should_send_notification(self, key: str) -> bool:
        """
        Check if enough time has passed since last notification
        
        Args:
            key: Notification key
            
        Returns:
            True if should send, False if throttled
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.throttle_minutes)
            
            recent = await notifications_sent_collection.find_one({
                "key": key,
                "sent_at": {"$gte": cutoff_time}
            })
            
            return recent is None
            
        except Exception as e:
            logger.error(f"Error checking notification throttle: {e}")
            return True  # On error, allow notification
    
    async def _mark_notification_sent(self, key: str) -> None:
        """
        Mark notification as sent for throttling
        
        Args:
            key: Notification key
        """
        try:
            await notifications_sent_collection.insert_one({
                "key": key,
                "sent_at": datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error marking notification sent: {e}")
    
    async def send_email(
        self,
        to_email: str,
        user_id: str,
        alert_type: str,
        sensor_id: str,
        location: str,
        title: str,
        value: str
    ) -> bool:
        """
        Send email notification with throttling
        
        Args:
            to_email: Recipient email
            user_id: User identifier
            alert_type: Alert type
            sensor_id: Sensor identifier
            location: Alert location
            title: Alert title
            value: Alert value
            
        Returns:
            True if sent successfully
        """
        try:
            key = self._build_notification_key(
                NotificationType.EMAIL,
                alert_type,
                sensor_id,
                user_id
            )
            
            if not await self._should_send_notification(key):
                logger.info(f"Email throttled for {to_email}")
                return False
            
            sent = await send_critical_alert_email(to_email, location, title, value, sensor_id=sensor_id)
            
            if sent:
                await self._mark_notification_sent(key)
                logger.info(f"Email sent to {to_email} for alert {alert_type}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_whatsapp(
        self,
        to_phone: str,
        user_id: str,
        alert_type: str,
        sensor_id: str,
        location: str,
        title: str,
        value: str
    ) -> bool:
        """
        Send WhatsApp notification with throttling
        
        Args:
            to_phone: Recipient phone (with country code)
            user_id: User identifier
            alert_type: Alert type
            sensor_id: Sensor identifier
            location: Alert location
            title: Alert title
            value: Alert value
            
        Returns:
            True if sent successfully
        """
        try:
            key = self._build_notification_key(
                NotificationType.WHATSAPP,
                alert_type,
                sensor_id,
                user_id
            )
            
            if not await self._should_send_notification(key):
                logger.info(f"WhatsApp throttled for {to_phone}")
                return False
            
            # Attempt send with retry/backoff for transient errors
            max_retries = 3
            backoff = 1
            attempt = 0
            last_result = None

            while attempt < max_retries:
                attempt += 1
                result = await send_critical_alert_twilio_whatsapp(
                    to_phone,
                    location,
                    alert_type,
                    value,
                    sensor_id=sensor_id
                )

                last_result = result

                # If Twilio returned structured dict
                if isinstance(result, dict) and result.get('ok'):
                    # Record notification and throttle key
                    try:
                        await notifications_sent_collection.insert_one({
                            'key': key,
                            'channel': 'whatsapp',
                            'to': to_phone,
                            'sid': result.get('sid'),
                            'status': result.get('status'),
                            'error_code': result.get('error_code'),
                            'attempts': attempt,
                            'created_at': datetime.utcnow(),
                        })
                    except Exception:
                        logger.exception('Failed to record notifications_sent entry')

                    await self._mark_notification_sent(key)
                    logger.info(f"WhatsApp sent to {to_phone} for alert {alert_type} (sid={result.get('sid')})")
                    return True

                # If result is dict with error code, decide whether to retry
                retryable_errors = {None, 'ETIMEDOUT', 500, 502, 503, 504, 63016}
                err = None
                if isinstance(result, dict):
                    err = result.get('error_code') or result.get('error_message')
                else:
                    err = str(result)

                # If this was last attempt, break
                if attempt >= max_retries:
                    break

                # If error seems retryable, wait and retry
                try:
                    if err in retryable_errors or isinstance(err, int) and err >= 500:
                        logger.info(f"Retrying WhatsApp send to {to_phone} (attempt {attempt}) due to error: {err}")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                except Exception:
                    pass

                # Non-retryable error -> stop
                break

            # After retries, record failed attempt
            try:
                await notifications_sent_collection.insert_one({
                    'key': key,
                    'channel': 'whatsapp',
                    'to': to_phone,
                    'sid': last_result.get('sid') if isinstance(last_result, dict) else None,
                    'status': last_result.get('status') if isinstance(last_result, dict) else 'failed',
                    'error_code': last_result.get('error_code') if isinstance(last_result, dict) else None,
                    'error_message': last_result.get('error_message') if isinstance(last_result, dict) else str(last_result),
                    'attempts': attempt,
                    'created_at': datetime.utcnow(),
                })
            except Exception:
                logger.exception('Failed to record failed notifications_sent entry')

            logger.error(f"WhatsApp not sent to {to_phone} for alert {alert_type} after {attempt} attempts: {last_result}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {to_phone}: {e}")
            return False
    
    async def notify_admins(
        self,
        alert_data: Dict[str, Any],
        channels: Optional[List[NotificationType]] = None
    ) -> Dict[str, int]:
        """
        Send notifications to all admin users
        
        Args:
            alert_data: Alert information dict
            channels: List of channels to use (default: all enabled)
            
        Returns:
            Dict with counts of notifications sent per channel
        """
        if channels is None:
            channels = [NotificationType.EMAIL, NotificationType.WHATSAPP]
        
        results = {"email": 0, "whatsapp": 0}
        
        sensor_id = alert_data.get("sensor_id", "unknown")
        alert_type = alert_data.get("type", "unknown")
        location = alert_data.get("location", "Sistema")
        title = alert_data.get("title", "Alerta")
        value = alert_data.get("value", "N/A")
        
        try:
            # Resolve embalse by sensor_id and prefer its admins when available
            admins = []
            try:
                embalse = await embalses_collection.find_one({"sensors": sensor_id})
                if embalse and embalse.get("admins"):
                    # Fetch user docs for embalse admins
                    admin_ids = embalse.get("admins", [])
                    admins = await users_collection.find({"_id": {"$in": admin_ids}}).to_list(length=100)
            except Exception:
                logger.exception("Failed to resolve embalse admins, falling back to global admins")

            # Fallback to global admins when no embalse-specific admins found
            if not admins:
                admins = await user_repository.get_admin_users()

            for admin in admins:
                user_id = str(admin.get("_id"))
                
                # Send email
                if NotificationType.EMAIL in channels:
                    email = admin.get("email")
                    if email:
                        if await self.send_email(
                            email, user_id, alert_type, sensor_id,
                            location, title, value
                        ):
                            results["email"] += 1
                
                # Send WhatsApp
                if NotificationType.WHATSAPP in channels:
                    phone = admin.get("phone")
                    whatsapp_enabled = admin.get("whatsapp_notifications_enabled", False)
                    
                    if phone and whatsapp_enabled:
                        if await self.send_whatsapp(
                            phone, user_id, alert_type, sensor_id,
                            location, title, value
                        ):
                            results["whatsapp"] += 1
            
            logger.info(f"Notifications sent: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")
            return results
    
    async def clear_throttle_for_alert(self, alert_id: str) -> None:
        """
        Clear notification throttle for specific alert
        Allows re-sending notifications if needed
        
        Args:
            alert_id: Alert identifier
        """
        try:
            await notifications_sent_collection.delete_many({
                "key": {"$regex": f".*:{alert_id}:.*"}
            })
            logger.info(f"Cleared notification throttle for alert {alert_id}")
        except Exception as e:
            logger.error(f"Error clearing throttle: {e}")


# Singleton instance
notification_service = NotificationService()
