"""
Twilio WhatsApp notification service
WhatsApp integration using Twilio API for AquaStat monitoring system
"""

import logging
import re
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings

logger = logging.getLogger(__name__)


def _format_disconnect_duration(value: str) -> str:
    """
    Format disconnect duration from minutes to human-readable format.
    
    Args:
        value: String containing minutes (e.g., "15 minutos" or "15")
        
    Returns:
        Formatted duration string (e.g., "15 minutos", "1 hora 30 minutos")
    """
    try:
        # Extract number from string
        match = re.search(r'(\d+)', str(value))
        if not match:
            return value
        
        minutes = int(match.group(1))
        
        if minutes < 60:
            return f"{minutes} minuto{'s' if minutes != 1 else ''}"
        
        hours = minutes // 60
        remaining_mins = minutes % 60
        
        if remaining_mins == 0:
            return f"{hours} hora{'s' if hours != 1 else ''}"
        
        return f"{hours} hora{'s' if hours != 1 else ''} {remaining_mins} minuto{'s' if remaining_mins != 1 else ''}"
    except:
        return value


async def send_critical_alert_twilio_whatsapp(
    to_phone: str,
    reservoir_name: str,
    alert_type: str,
    value: str,
    sensor_id: str = None
) -> dict:
    """
    Send a professional critical alert via Twilio WhatsApp
    
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
        # Check if Twilio WhatsApp is enabled
        if not getattr(settings, 'TWILIO_WHATSAPP_ENABLED', False):
            logger.debug("Twilio WhatsApp notifications disabled in settings")
            return False
        
        # Validate configuration
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        
        if not all([twilio_sid, twilio_token, twilio_from]):
            logger.warning("Configuración Twilio WhatsApp incompleta")
            return False
        
        if not to_phone:
            logger.warning("Número de teléfono no proporcionado")
            return False
            
        # Validate phone format (must start with +)
        if not to_phone.startswith('+'):
            logger.warning(f"Número de teléfono inválido (debe incluir código país con +): {to_phone}")
            return False
        
        # Human-readable alert names and emojis
        alert_config = {
            'ph_range': {'name': 'pH Fuera de Rango', 'icon': '⚗️'},
            'ph': {'name': 'pH Fuera de Rango', 'icon': '⚗️'},
            'conductivity': {'name': 'Conductividad Anormal', 'icon': '⚡'},
            'ec': {'name': 'Conductividad Eléctrica Anormal', 'icon': '⚡'},
            'temperature': {'name': 'Temperatura Crítica', 'icon': '🌡️'},
            'water_level': {'name': 'Nivel de Agua Crítico', 'icon': '💧'},
            'sensor_disconnection': {'name': 'Sensor Desconectado', 'icon': '🔌'}
        }
        
        config = alert_config.get(alert_type, {'name': alert_type, 'icon': '⚠️'})
        alert_name = config['name']
        alert_icon = config['icon']
        
        # Format value for disconnect alerts
        is_disconnect = alert_type == 'sensor_disconnection'
        if is_disconnect:
            display_value = _format_disconnect_duration(value)
            value_label = "Tiempo desconectado"
        else:
            display_value = value
            value_label = "Valor detectado"
        
        # Build sensor ID line if available
        sensor_line = f"\n📟 *Sensor ID:* `{sensor_id}`" if sensor_id else ""
        
        # Create professional message body
        message_body = (
            f"🚨 *ALERTA CRÍTICA - AquaStat* 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{alert_icon} *{alert_name}*\n\n"
            f"📍 *Ubicación:* {reservoir_name}"
            f"{sensor_line}\n"
            f"📊 *{value_label}:* {display_value}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Acción requerida:* Revise el sistema inmediatamente.\n\n"
            f"💧 _Sistema AquaStat_"
        )
        
        # Initialize Twilio client
        client = Client(twilio_sid, twilio_token)
        
        # Format WhatsApp numbers (Twilio requires 'whatsapp:' prefix)
        from_whatsapp = f"whatsapp:{twilio_from}"
        to_whatsapp = f"whatsapp:{to_phone}"
        
        # Optionally include a per-message status callback URL (if configured)
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

        # Log full response details for diagnostics
        try:
            msg_info = {
                'sid': getattr(message, 'sid', None),
                'status': getattr(message, 'status', None),
                'to': getattr(message, 'to', None),
                'from': getattr(message, 'from_', None),
                'date_created': getattr(message, 'date_created', None),
                'date_sent': getattr(message, 'date_sent', None),
                'date_updated': getattr(message, 'date_updated', None),
            }
            logger.info(f"Twilio WhatsApp send response: {msg_info}")
        except Exception:
            logger.info(f"Twilio WhatsApp sent (sid={getattr(message,'sid',None)})")

        return {
            'ok': True,
            'sid': getattr(message, 'sid', None),
            'status': getattr(message, 'status', None),
            'error_code': None,
            'error_message': None
        }
        
    except TwilioRestException as e:
        # Log Twilio exception details (error code/message and response body if available)
        try:
            logger.error(
                f"Twilio API error: code={getattr(e,'code',None)} msg={getattr(e,'msg',None)} resp={getattr(e,'resp',None)}"
            )
        except Exception:
            logger.exception("Twilio API error (exception) while logging details")
        # Return structured error info so callers can decide to retry
        return {
            'ok': False,
            'sid': None,
            'status': None,
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'msg', str(e))
        }
        
    except Exception as e:
        logger.error(f"Error enviando Twilio WhatsApp a {to_phone}: {e}")
        return False
