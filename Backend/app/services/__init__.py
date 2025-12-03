"""
Services package
Business logic and external integrations following SOLID principles
"""

from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_user_from_token,
    authenticate_user,
    validate_admin_role
)

from .email import (
    send_critical_alert_email,
    send_reset_email,
    generate_reset_token
)

from .alert_watcher import alert_change_stream_watcher

from .audit import (
    log_audit_event,
    log_audit_from_request,
    get_audit_logs,
    get_user_activity,
    get_audit_statistics
)

from .prediction import predict_sensor_values

# SOLID-compliant service instances
from .alert_service import alert_service
from .notification_service import notification_service
from .user_service import user_service
from .sensor_service import sensor_service

__all__ = [
    # Auth
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "get_user_from_token",
    "authenticate_user",
    "validate_admin_role",
    # Email
    "send_critical_alert_email",
    "send_reset_email",
    "generate_reset_token",
    # Alert Watcher
    "alert_change_stream_watcher",
    # Audit
    "log_audit_event",
    "log_audit_from_request",
    "get_audit_logs",
    "get_user_activity",
    "get_audit_statistics",
    # Prediction
    "predict_sensor_values",
    # Services (SOLID compliant)
    "alert_service",
    "notification_service",
    "user_service",
    "sensor_service"
]
