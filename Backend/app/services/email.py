"""
Email notification service
SMTP email sending for alerts and password reset
Professional alert emails for AquaStat monitoring system
"""

import smtplib
import secrets
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import logging

from app.config import settings
from app.utils.formatting import format_disconnect_duration, get_alert_display_config

logger = logging.getLogger(__name__)


async def send_critical_alert_email(
    to_email: str, 
    reservoir_name: str, 
    alert_type: str, 
    value: str,
    sensor_id: str = None
) -> bool:
    """
    Send a professional critical alert email notification.
    
    Args:
        to_email: Recipient email address
        reservoir_name: Name of the reservoir/sensor location
        alert_type: Type of alert (e.g., "ph_range", "temperature", "sensor_disconnection")
        value: Detected value that triggered the alert
        sensor_id: Optional sensor identifier
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Validate SMTP configuration
        if not all([
            settings.SMTP_SERVER, 
            settings.SMTP_PORT, 
            settings.SMTP_USERNAME, 
            settings.SMTP_PASSWORD, 
            settings.FROM_EMAIL
        ]):
            logger.warning("Incomplete SMTP configuration - cannot send email")
            return False

        # Get display configuration for alert type
        config = get_alert_display_config(alert_type)
        alert_name = config['name']
        alert_color = config['color']
        
        # Format value for disconnect alerts
        is_disconnect = alert_type == 'sensor_disconnection'
        if is_disconnect:
            display_value = format_disconnect_duration(value)
            value_label = "Tiempo desconectado"
        else:
            display_value = value
            value_label = "Valor detectado"
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Sensor ID section (only show if available)
        sensor_section = ""
        if sensor_id:
            sensor_section = f"""
                <tr>
                    <td style="padding: 12px 20px; border-bottom: 1px solid #e9ecef;">
                        <span style="color: #6c757d; font-size: 14px;">Sensor ID</span><br>
                        <span style="color: #212529; font-size: 16px; font-weight: 600; font-family: monospace;">{sensor_id}</span>
                    </td>
                </tr>
            """

        msg = MIMEMultipart('alternative')
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = to_email
        msg['Subject'] = f"🚨 ALERTA CRÍTICA AquaStat - {alert_name}"

        # Professional HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 40px 0;">
                        <table role="presentation" style="width: 100%; max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #1a365d 0%, #2d3748 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">
                                        AquaStat
                                    </h1>
                                    <p style="color: #a0aec0; margin: 8px 0 0 0; font-size: 14px;">
                                        Sistema de Monitoreo Inteligente
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Alert Banner -->
                            <tr>
                                <td style="background-color: {alert_color}; padding: 25px; text-align: center;">
                                    <h2 style="color: #ffffff; margin: 0 0 5px 0; font-size: 22px; font-weight: 600; text-transform: uppercase;">
                                        ALERTA CRÍTICA
                                    </h2>
                                    <p style="color: #ffffff; margin: 0; font-size: 18px; opacity: 0.95;">
                                        {alert_name}
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Alert Details -->
                            <tr>
                                <td style="padding: 0;">
                                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 12px 20px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa;">
                                                <span style="color: #6c757d; font-size: 14px;">Ubicación</span><br>
                                                <span style="color: #212529; font-size: 16px; font-weight: 600;">{reservoir_name}</span>
                                            </td>
                                        </tr>
                                        {sensor_section}
                                        <tr>
                                            <td style="padding: 12px 20px; border-bottom: 1px solid #e9ecef;">
                                                <span style="color: #6c757d; font-size: 14px;">{value_label}</span><br>
                                                <span style="color: {alert_color}; font-size: 20px; font-weight: 700;">{display_value}</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 12px 20px; border-bottom: 1px solid #e9ecef; background-color: #f8f9fa;">
                                                <span style="color: #6c757d; font-size: 14px;">Fecha y hora</span><br>
                                                <span style="color: #212529; font-size: 16px;">{timestamp}</span>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Action Required -->
                            <tr>
                                <td style="padding: 30px; text-align: center; background-color: #fff3cd; border-top: 3px solid #ffc107;">
                                    <p style="color: #856404; margin: 0; font-size: 16px; font-weight: 600;">
                                        ACCIÓN REQUERIDA
                                    </p>
                                    <p style="color: #856404; margin: 10px 0 0 0; font-size: 14px;">
                                        Por favor, revise el sistema y tome las acciones correctivas necesarias.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #1a365d; padding: 20px; text-align: center;">
                                    <p style="color: #a0aec0; margin: 0; font-size: 12px;">
                                        Este es un mensaje automático del sistema AquaStat.<br>
                                        Por favor, no responda a este correo.
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Plain text fallback
        plain_text = f"""
[ALERTA CRÍTICA] AquaStat

{alert_name}

Ubicación: {reservoir_name}
{"Sensor ID: " + sensor_id if sensor_id else ""}
{value_label}: {display_value}
Fecha y hora: {timestamp}

ACCIÓN REQUERIDA: Revise el sistema y tome las acciones correctivas necesarias.

---
Este es un mensaje automático del sistema AquaStat.
        """

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email via SMTP with timeout
        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587, timeout=30)
        server.starttls()
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        server.send_message(msg)
        server.quit()

        logger.info(f"Critical alert email sent to {to_email} for {reservoir_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False


async def send_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email.
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        if not all([
            settings.SMTP_SERVER, 
            settings.SMTP_PORT, 
            settings.SMTP_USERNAME, 
            settings.SMTP_PASSWORD, 
            settings.FROM_EMAIL
        ]):
            logger.warning("Incomplete SMTP configuration - cannot send email")
            return False

        reset_url = f"http://localhost:5173/reset-password?token={reset_token}"
        
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = email
        msg['Subject'] = "Recuperación de Contraseña"

        body = f"""
        <html>
        <body>
            <h2>Recuperación de Contraseña</h2>
            <p>Has solicitado restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
            <p><a href="{reset_url}">Restablecer contraseña</a></p>
            <p>Este enlace expirará en 1 hora.</p>
            <p>Si no solicitaste este cambio, ignora este correo.</p>
            <hr>
            <p style="font-size:0.9em;color:#666;">Este es un correo automático.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587, timeout=30)
        server.starttls()
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        server.send_message(msg)
        server.quit()

        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending reset email to {email}: {e}")
        return False


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        32-character random alphanumeric string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))
