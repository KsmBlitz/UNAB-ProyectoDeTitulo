"""
Twilio WhatsApp notification service
WhatsApp integration using Twilio API for AquaStat monitoring system
"""

import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.utils.formatting import format_disconnect_duration, get_alert_display_config

logger = logging.getLogger(__name__)


async def send_critical_alert_twilio_whatsapp(
    to_phone: str,
    reservoir_name: str,
    alert_type: str,
    value: str,
    sensor_id: str = None
) -> dict:
    """
    Send a professional critical alert via Twilio WhatsApp.
    
    Args:
        to_phone: Recipient phone number in international format (e.g., +56912345678)
        reservoir_name: Name of the reservoir/sensor location
        alert_type: Type of alert (e.g., "ph_range", "temperature", "sensor_disconnection")
        value: Detected value that triggered the alert
        sensor_id: Optional sensor identifier
        
    Returns:
        dict with 'ok', 'sid', 'status', 'error_code', 'error_message'
    """
    try:
        logger.info(f"Attempting WhatsApp send to {to_phone} - type: {alert_type}")
        
        # Check if Twilio WhatsApp is enabled
        if not getattr(settings, 'TWILIO_WHATSAPP_ENABLED', False):
            logger.warning("Twilio WhatsApp notifications DISABLED in settings")
            return {'ok': False, 'sid': None, 'status': None, 'error_code': None, 'error_message': 'WhatsApp disabled'}
        
        # Validate configuration
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        
        if not all([twilio_sid, twilio_token, twilio_from]):
            logger.warning(f"Incomplete Twilio WhatsApp config - SID: {bool(twilio_sid)}, Token: {bool(twilio_token)}, From: {twilio_from}")
            return {'ok': False, 'sid': None, 'status': None, 'error_code': None, 'error_message': 'Incomplete configuration'}
        
        if not to_phone:
            logger.warning("Phone number not provided")
            return {'ok': False, 'sid': None, 'status': None, 'error_code': None, 'error_message': 'No phone number'}
            
        # Validate phone format (must start with +)
        if not to_phone.startswith('+'):
            logger.warning(f"Invalid phone number (must include country code with +): {to_phone}")
            return {'ok': False, 'sid': None, 'status': None, 'error_code': None, 'error_message': 'Invalid phone format'}
        
        logger.info(f"Twilio config OK - Sending from {twilio_from} to {to_phone}")
        
        # Get display configuration for alert type
        config = get_alert_display_config(alert_type)
        alert_name = config['name']
        
        # Format value for disconnect alerts
        is_disconnect = alert_type == 'sensor_disconnection'
        if is_disconnect:
            display_value = format_disconnect_duration(value)
            value_label = "Tiempo desconectado"
        else:
            display_value = value
            value_label = "Valor detectado"
        
        # Build sensor ID line if available
        sensor_line = f"\n*Sensor:* {sensor_id}" if sensor_id else ""
        
        # Create professional message body
        message_body = (
            f"*[ALERTA CRÍTICA] AquaStat*\n"
            f"------------------------\n\n"
            f"*{alert_name}*\n\n"
            f"*Ubicación:* {reservoir_name}"
            f"{sensor_line}\n"
            f"*{value_label}:* {display_value}\n\n"
            f"------------------------\n"
            f"Acción requerida: Revise el sistema inmediatamente.\n\n"
            f"_Sistema AquaStat_"
        )
        
        # Initialize Twilio client
        client = Client(twilio_sid, twilio_token)
        
        # Format WhatsApp numbers (Twilio requires 'whatsapp:' prefix)
        from_whatsapp = f"whatsapp:{twilio_from}"
        to_whatsapp = f"whatsapp:{to_phone}"
        
        # Optional status callback URL
        status_callback_url = getattr(settings, 'TWILIO_STATUS_CALLBACK_URL', None)

        # Send message
        if status_callback_url:
            message = client.messages.create(
                body=message_body,
                from_=from_whatsapp,
                to=to_whatsapp,
                status_callback=status_callback_url
            )
        else:
            message = client.messages.create(
                body=message_body,
                from_=from_whatsapp,
                to=to_whatsapp
            )

        # Log response details
        logger.info(f"Twilio WhatsApp sent (sid={getattr(message, 'sid', None)}, status={getattr(message, 'status', None)})")

        return {
            'ok': True,
            'sid': getattr(message, 'sid', None),
            'status': getattr(message, 'status', None),
            'error_code': None,
            'error_message': None
        }
        
    except TwilioRestException as e:
        logger.error(f"Twilio API error: code={getattr(e, 'code', None)} msg={getattr(e, 'msg', None)}")
        return {
            'ok': False,
            'sid': None,
            'status': None,
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'msg', str(e))
        }
        
    except Exception as e:
        logger.error(f"Error sending Twilio WhatsApp to {to_phone}: {e}")
        return {
            'ok': False,
            'sid': None,
            'status': None,
            'error_code': None,
            'error_message': str(e)
        }
