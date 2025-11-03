"""
Audit log models
Data models for audit logging and tracking
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum


class AuditAction(str, Enum):
    """Enum for audit action types"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # User Management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    
    # Alert Management
    ALERT_THRESHOLD_CREATED = "alert_threshold_created"
    ALERT_THRESHOLD_UPDATED = "alert_threshold_updated"
    ALERT_THRESHOLD_DELETED = "alert_threshold_deleted"
    ALERT_DISMISSED = "alert_dismissed"
    
    # System
    SYSTEM_CONFIG_CHANGED = "system_config_changed"


class AuditLogEntry(BaseModel):
    """Audit log entry model"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True


class AuditLogResponse(BaseModel):
    """Response model for audit log queries"""
    total: int
    page: int
    page_size: int
    logs: list[Dict[str, Any]]


class AuditLogFilter(BaseModel):
    """Filter model for audit log queries"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None
    page: int = 1
    page_size: int = 50
