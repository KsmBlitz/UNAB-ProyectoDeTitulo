"""Configuration package"""

from .settings import settings, get_settings
from .database import (
    Database,
    users_collection,
    sensor_collection,
    alerts_collection,
    alert_history_collection,
    alert_thresholds_collection,
    reset_tokens_collection,
    notifications_sent_collection
)

__all__ = [
    "settings",
    "get_settings",
    "Database",
    "users_collection",
    "sensor_collection",
    "alerts_collection",
    "alert_history_collection",
    "alert_thresholds_collection",
    "reset_tokens_collection",
    "notifications_sent_collection"
]
