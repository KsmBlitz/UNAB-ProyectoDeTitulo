# Backend/models/alert_models.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from bson import ObjectId

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(str, Enum):
    PH_RANGE = "ph_range"
    CONDUCTIVITY = "conductivity"
    TEMPERATURE = "temperature"
    SENSOR_DISCONNECTION = "sensor_disconnection"
    WATER_LEVEL = "water_level"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    AUTO_RESOLVED = "auto_resolved"

class ThresholdConfig(BaseModel):
    """Threshold configuration for a specific parameter"""
    optimal_min: Optional[float] = None
    optimal_max: Optional[float] = None
    warning_min: Optional[float] = None
    warning_max: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    
    @validator('optimal_max')
    def optimal_max_greater_than_min(cls, v, values):
        """Validate that optimal_max > optimal_min"""
        if v is not None and 'optimal_min' in values and values['optimal_min'] is not None:
            if v <= values['optimal_min']:
                raise ValueError('optimal_max must be greater than optimal_min')
        return v
    
    @validator('warning_max')
    def warning_max_greater_than_min(cls, v, values):
        """Validate that warning_max > warning_min"""
        if v is not None and 'warning_min' in values and values['warning_min'] is not None:
            if v <= values['warning_min']:
                raise ValueError('warning_max must be greater than warning_min')
        return v
    
    @validator('critical_max')
    def critical_max_greater_than_min(cls, v, values):
        """Validate that critical_max > critical_min"""
        if v is not None and 'critical_min' in values and values['critical_min'] is not None:
            if v <= values['critical_min']:
                raise ValueError('critical_max must be greater than critical_min')
        return v

class AlertThresholds(BaseModel):
    """Complete threshold configuration - Specific for Blueberry cultivation in Chile"""
    ph: ThresholdConfig = ThresholdConfig(
        optimal_min=5.0, optimal_max=5.5,
        warning_min=4.5, warning_max=6.0,
        critical_min=4.0, critical_max=6.5
    )
    conductivity: ThresholdConfig = ThresholdConfig(
        optimal_min=0.0, optimal_max=1.0,
        warning_min=0.0, warning_max=1.5,
        critical_min=0.0, critical_max=2.0
    )
    temperature: ThresholdConfig = ThresholdConfig(
        optimal_min=15.0, optimal_max=30.0,
        warning_min=10.0, warning_max=35.0,
        critical_min=5.0, critical_max=40.0
    )
    water_level: ThresholdConfig = ThresholdConfig(
        optimal_min=60.0, optimal_max=90.0,
        # Allow lower warning/critical defaults so administrators may set values below 20%
        warning_min=0.0, warning_max=95.0,
        critical_min=0.0, critical_max=98.0
    )
    # Disconnected sensor configuration (in minutes)
    sensor_timeout_warning: int = 6  # minutes without data = warning
    sensor_timeout_critical: int = 15  # minutes without data = critical

class ActiveAlert(BaseModel):
    """Active alert in the system"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    # Use plain strings for `type` and `level` to accept legacy/varied values
    type: str
    level: str
    title: str
    message: str
    value: Optional[Any] = None  # Can be float (measurements) or str (disconnect duration)
    threshold_info: str
    location: str = "Irrigation System"
    sensor_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AlertStatus = AlertStatus.ACTIVE
    is_resolved: bool = False
    
    # Resolution/close information
    resolved_at: Optional[datetime] = None
    dismissed_by: Optional[str] = None  # Email of user who closed the alert
    dismissed_at: Optional[datetime] = None
    resolution_type: Optional[str] = None  # "manual", "auto_resolved"
    
class AlertHistory(BaseModel):
    """Complete alert history for administrators"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    alert_id: str  # Reference to original alert
    type: str
    level: str
    title: str
    message: str
    value: Optional[Any] = None  # Can be float (measurements) or str (disconnect duration)
    threshold_info: str
    location: str
    sensor_id: Optional[str] = None
    
    # Lifecycle timestamps
    created_at: datetime
    resolved_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    
    # Information about who handled the alert
    dismissed_by: Optional[str] = None
    dismissed_by_role: Optional[str] = None  # "admin" or "operario"
    resolution_type: str  # "manual_dismiss", "auto_resolved", "threshold_change"
    
    # Additional context
    duration_minutes: Optional[int] = None
    threshold_config_at_time: Optional[Dict[str, Any]] = None

class AlertSummary(BaseModel):
    """Alert summary for dashboard"""
    total_active: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    sensors_offline: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlertConfigUpdateRequest(BaseModel):
    """Request to update threshold configuration - Admin only"""
    thresholds: AlertThresholds
    updated_by: str  # Admin email
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('updated_by')
    def validate_email(cls, v):
        """Validate email format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class DismissAlertRequest(BaseModel):
    """Request to close an alert - Operator or Admin"""
    alert_id: str
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('alert_id')
    def validate_alert_id(cls, v):
        """Validate that alert_id is not empty"""
        if not v or not v.strip():
            raise ValueError('alert_id cannot be empty')
        return v.strip()
    # dismissed_by is automatically obtained from authenticated user

# Predefined configuration for Blueberry cultivation in Chile
BLUEBERRY_CHILE_THRESHOLDS = AlertThresholds(
    ph=ThresholdConfig(
        optimal_min=5.0, optimal_max=5.5,
        warning_min=4.5, warning_max=6.0,
        critical_min=4.0, critical_max=6.5
    ),
    conductivity=ThresholdConfig(
        optimal_min=0.0, optimal_max=1.0,
        warning_min=0.0, warning_max=1.5,
        critical_min=0.0, critical_max=2.0
    ),
    temperature=ThresholdConfig(
        optimal_min=15.0, optimal_max=30.0,
        warning_min=10.0, warning_max=35.0,
        critical_min=5.0, critical_max=40.0
    ),
    water_level=ThresholdConfig(
        optimal_min=60.0, optimal_max=90.0,
        # Default thresholds adjusted to allow very low water level settings
        warning_min=0.0, warning_max=95.0,
        critical_min=0.0, critical_max=98.0
    ),
    sensor_timeout_warning=6,
    sensor_timeout_critical=15
)

class ParameterThreshold(BaseModel):
    """Threshold for an individual parameter"""
    min: float
    max: float
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None

class SensorAlertConfig(BaseModel):
    """Alert configuration for an individual sensor"""
    enabled: bool = True
    parameters: Dict[str, ParameterThreshold]
    notification_enabled: bool = True
    whatsapp_enabled: bool = True
    email_enabled: bool = True

class UpdateSensorAlertConfigRequest(BaseModel):
    """Request to update sensor alert configuration"""
    sensor_id: str
    alert_config: SensorAlertConfig
    
    @validator('sensor_id')
    def validate_sensor_id(cls, v):
        if not v or not v.strip():
            raise ValueError('sensor_id cannot be empty')
        return v.strip()