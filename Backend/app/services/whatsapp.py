"""
WhatsApp notification service
WhatsApp Business API integration for critical alerts
"""

import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def send_critical_alert_whatsapp(
    to_phone: str,
    reservoir_name: str,
    alert_type: str,
    value: str
) -> bool:
    """
    Send a critical alert via WhatsApp Business API
    
    Args:
        to_phone: Recipient phone number in international format (e.g., +56912345678)
        reservoir_name: Name of the reservoir/sensor
        alert_type: Type of alert (e.g., "ph_range", "temperature")
        value: Detected value that triggered the alert
        
    Returns:
        True if WhatsApp message sent successfully, False otherwise
        
    Note:
        WhatsApp Business API in production mode requires approved message templates.
        Free text messages only work in sandbox mode or with active conversations.
    """
    try:
        # Check if WhatsApp is enabled
        if not settings.WHATSAPP_ENABLED:
            logger.debug("WhatsApp notifications disabled in settings")
            return False
        
        # Validate configuration
        if not all([
            settings.WHATSAPP_ACCESS_TOKEN,
            settings.WHATSAPP_PHONE_NUMBER_ID
        ]):
            logger.warning("Configuración WhatsApp incompleta")
            return False
        
        if not to_phone:
            logger.warning("Número de teléfono no proporcionado")
            return False
            
        # Validate phone format (must start with +)
        if not to_phone.startswith('+'):
            logger.warning(f"Número de teléfono inválido (debe incluir código país con +): {to_phone}")
            return False
        
        # Remove + for WhatsApp API
        phone_wa = to_phone.lstrip('+')
        
        # Human-readable alert names mapping
        alert_names = {
            'ph_range': 'pH fuera de rango',
            'conductivity': 'Conductividad anormal',
            'temperature': 'Temperatura crítica',
            'sensor_disconnection': 'Sensor desconectado'
        }
        
        alert_name = alert_names.get(alert_type, alert_type)
        
        # WhatsApp Cloud API endpoint
        url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # IMPORTANT: WhatsApp Business API in production requires approved templates
        # TODO: Once Meta approves the 'alerta_critica_embalse' template,
        # switch to using templates instead of free text (see commented code below)
        
        # Option 1: Template (when approved) - RECOMMENDED FOR PRODUCTION
        # payload = {
        #     "messaging_product": "whatsapp",
        #     "to": phone_wa,
        #     "type": "template",
        #     "template": {
        #         "name": "alerta_critica_embalse",
        #         "language": {"code": "es"},
        #         "components": [{
        #             "type": "body",
        #             "parameters": [
        #                 {"type": "text", "text": reservoir_name},
        #                 {"type": "text", "text": alert_name},
        #                 {"type": "text", "text": str(value)}
        #             ]
        #         }]
        #     }
        # }
        
        # Option 2: Free text (only works in sandbox or with active conversation)
        message = f"""🚨 ALERTA CRÍTICA

Embalse: {reservoir_name}
Tipo: {alert_name}
Valor: {value}

Por favor revise el sistema lo antes posible."""
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_wa,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        # Send HTTP request to WhatsApp API
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                logger.info(
                    f"WhatsApp enviado a {to_phone} para {reservoir_name} "
                    f"(MessageId: {message_id})"
                )
                return True
            else:
                error_data = response.text
                logger.error(
                    f"Error API WhatsApp ({response.status_code}): {error_data}"
                )
                return False
                
    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {to_phone}: {e}")
        return False
