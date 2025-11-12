# Backend/models/alert_models.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
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
    """Configuración de umbrales para un parámetro específico"""
    optimal_min: Optional[float] = None
    optimal_max: Optional[float] = None
    warning_min: Optional[float] = None
    warning_max: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    
    @validator('optimal_max')
    def optimal_max_greater_than_min(cls, v, values):
        """Validar que optimal_max > optimal_min"""
        if v is not None and 'optimal_min' in values and values['optimal_min'] is not None:
            if v <= values['optimal_min']:
                raise ValueError('optimal_max debe ser mayor que optimal_min')
        return v
    
    @validator('warning_max')
    def warning_max_greater_than_min(cls, v, values):
        """Validar que warning_max > warning_min"""
        if v is not None and 'warning_min' in values and values['warning_min'] is not None:
            if v <= values['warning_min']:
                raise ValueError('warning_max debe ser mayor que warning_min')
        return v
    
    @validator('critical_max')
    def critical_max_greater_than_min(cls, v, values):
        """Validar que critical_max > critical_min"""
        if v is not None and 'critical_min' in values and values['critical_min'] is not None:
            if v <= values['critical_min']:
                raise ValueError('critical_max debe ser mayor que critical_min')
        return v

class AlertThresholds(BaseModel):
    """Configuración completa de umbrales - Específica para Arándanos en Chile"""
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
        warning_min=40.0, warning_max=95.0,
        critical_min=20.0, critical_max=98.0
    )
    # Configuración para sensores desconectados (en minutos)
    sensor_timeout_warning: int = 6  # minutos sin datos = advertencia
    sensor_timeout_critical: int = 15  # minutos sin datos = crítico

class ActiveAlert(BaseModel):
    """Alerta activa en el sistema"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    value: Optional[float] = None
    threshold_info: str
    location: str = "Sistema de Riego"
    sensor_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: AlertStatus = AlertStatus.ACTIVE
    is_resolved: bool = False
    
    # Información de resolución/cierre
    resolved_at: Optional[datetime] = None
    dismissed_by: Optional[str] = None  # Email del usuario que cerró la alerta
    dismissed_at: Optional[datetime] = None
    resolution_type: Optional[str] = None  # "manual", "auto_resolved"
    
class AlertHistory(BaseModel):
    """Historial completo de alertas para administradores"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    alert_id: str  # Referencia a la alerta original
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    value: Optional[float] = None
    threshold_info: str
    location: str
    sensor_id: Optional[str] = None
    
    # Timestamps del ciclo de vida
    created_at: datetime
    resolved_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    
    # Información de quién manejó la alerta
    dismissed_by: Optional[str] = None
    dismissed_by_role: Optional[str] = None  # "admin" o "operario"
    resolution_type: str  # "manual_dismiss", "auto_resolved", "threshold_change"
    
    # Contexto adicional
    duration_minutes: Optional[int] = None
    threshold_config_at_time: Optional[Dict[str, Any]] = None

class AlertSummary(BaseModel):
    """Resumen de alertas para dashboard"""
    total_active: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    sensors_offline: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AlertConfigUpdateRequest(BaseModel):
    """Request para actualizar configuración de umbrales - Solo Admin"""
    thresholds: AlertThresholds
    updated_by: str  # Email del admin
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('updated_by')
    def validate_email(cls, v):
        """Validar formato de email"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Email inválido')
        return v.lower()

class DismissAlertRequest(BaseModel):
    """Request para cerrar una alerta - Operario o Admin"""
    alert_id: str
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('alert_id')
    def validate_alert_id(cls, v):
        """Validar que alert_id no esté vacío"""
        if not v or not v.strip():
            raise ValueError('alert_id no puede estar vacío')
        return v.strip()
    # dismissed_by se obtiene automáticamente del usuario autenticado

# Configuración predefinida para Arándanos en Chile
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
        warning_min=40.0, warning_max=95.0,
        critical_min=20.0, critical_max=98.0
    ),
    sensor_timeout_warning=6,
    sensor_timeout_critical=15
)