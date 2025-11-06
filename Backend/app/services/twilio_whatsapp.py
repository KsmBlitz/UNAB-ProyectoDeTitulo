"""
Twilio WhatsApp notification service
WhatsApp integration using Twilio API
"""

import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings

logger = logging.getLogger(__name__)


async def send_critical_alert_twilio_whatsapp(
    to_phone: str,
    reservoir_name: str,
    alert_type: str,
    value: str
) -> bool:
    """
    Send a critical alert via Twilio WhatsApp
    
    Args:
        to_phone: Recipient phone number in international format (e.g., +56912345678)
        reservoir_name: Name of the reservoir/sensor
        alert_type: Type of alert (e.g., "ph_range", "temperature")
        value: Detected value that triggered the alert
        
    Returns:
        True if WhatsApp message sent successfully, False otherwise
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
        
        # Human-readable alert names mapping
        alert_names = {
            'ph_range': 'pH fuera de rango',
            'conductivity': 'Conductividad anormal',
            'temperature': 'Temperatura crítica',
            'sensor_disconnection': 'Sensor desconectado'
        }
        
        alert_name = alert_names.get(alert_type, alert_type)
        
        # Create message body
        message_body = (
            f"*Alerta Crítica - Sistema de Monitoreo de Embalses*\n\n"
            f"Embalse: {reservoir_name}\n"
            f"Tipo de alerta: {alert_name}\n"
            f"Valor detectado: {value}\n\n"
            f"Por favor, revise el sistema inmediatamente."
        )
        
        # Initialize Twilio client
        client = Client(twilio_sid, twilio_token)
        
        # Format WhatsApp numbers (Twilio requires 'whatsapp:' prefix)
        from_whatsapp = f"whatsapp:{twilio_from}"
        to_whatsapp = f"whatsapp:{to_phone}"
        
        # Send message
        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        logger.info(
            f"Twilio WhatsApp enviado a {to_phone} para {reservoir_name} "
            f"(MessageSID: {message.sid})"
        )
        return True
        
    except TwilioRestException as e:
        logger.error(f"Error Twilio API: {e.code} - {e.msg}")
        return False
        
    except Exception as e:
        logger.error(f"Error enviando Twilio WhatsApp a {to_phone}: {e}")
        return False
