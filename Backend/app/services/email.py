"""
Email notification service
SMTP email sending for alerts and password reset
"""

import smtplib
import secrets
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_critical_alert_email(
    to_email: str, 
    reservoir_name: str, 
    alert_type: str, 
    value: str
) -> bool:
    """
    Send a critical alert email notification
    
    Args:
        to_email: Recipient email address
        reservoir_name: Name of the reservoir/sensor
        alert_type: Type of alert (e.g., "Temperatura Alta")
        value: Detected value that triggered the alert
        
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
            logger.warning("Configuración SMTP incompleta - no se puede enviar email")
            return False

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = to_email
        msg['Subject'] = f"[ALERTA CRÍTICA] {reservoir_name} - {alert_type}"

        # HTML email body
        body = f"""
        <html>
        <body>
            <h2>🚨 Alerta Crítica</h2>
            <p><strong>Embalse:</strong> {reservoir_name}</p>
            <p><strong>Tipo de alerta:</strong> {alert_type}</p>
            <p><strong>Valor detectado:</strong> {value}</p>
            <hr>
            <p>Revisa el dashboard para más detalles.</p>
            <p style="font-size:0.9em;color:#666;">Este es un correo automático.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Send email via SMTP
        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587)
        server.starttls()
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        server.send_message(msg)
        server.quit()

        logger.info(f"Email de alerta crítica enviado a {to_email} para {reservoir_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email a {to_email}: {e}")
        return False


async def send_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
        
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
            logger.warning("Configuración SMTP incompleta - no se puede enviar email")
            return False

        # Build reset URL (adjust FRONTEND_URL if you have it in settings)
        reset_url = f"http://localhost:5173/reset-password?token={reset_token}"
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = email
        msg['Subject'] = "Recuperación de Contraseña"

        # HTML email body
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

        # Send email via SMTP
        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587)
        server.starttls()
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        server.send_message(msg)
        server.quit()

        logger.info(f"Email de recuperación enviado a {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de recuperación a {email}: {e}")
        return False


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset
    
    Returns:
        32-character random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))
