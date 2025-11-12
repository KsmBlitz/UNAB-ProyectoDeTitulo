# Backend/models/sensor_models.py
"""
Modelos Pydantic para validación de datos de sensores
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SensorReading(BaseModel):
    """Modelo para validar lecturas de sensores"""
    temperature: float = Field(..., ge=-50, le=100, description="Temperatura en °C")
    ph: float = Field(..., ge=0, le=14, description="Nivel de pH")
    ec: float = Field(..., ge=0, le=20, description="Conductividad eléctrica (dS/m)")
    water_level: float = Field(..., ge=0, le=100, description="Nivel de agua (%)")
    timestamp: Optional[datetime] = None
    reservoir_id: Optional[str] = Field(None, min_length=1, max_length=100)
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validar rango razonable de temperatura"""
        if v < -10 or v > 50:
            raise ValueError(f'Temperatura fuera de rango operativo: {v}°C (esperado: -10 a 50°C)')
        return v
    
    @validator('ph')
    def validate_ph(cls, v):
        """Validar rango razonable de pH"""
        if v < 3 or v > 10:
            raise ValueError(f'pH fuera de rango operativo: {v} (esperado: 3 a 10)')
        return v
    
    @validator('ec')
    def validate_conductivity(cls, v):
        """Validar rango razonable de conductividad"""
        if v < 0 or v > 10:
            raise ValueError(f'Conductividad fuera de rango operativo: {v} dS/m (esperado: 0 a 10)')
        return v
    
    @validator('reservoir_id')
    def validate_reservoir_id(cls, v):
        """Limpiar y validar reservoir_id"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('reservoir_id no puede estar vacío')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 22.5,
                "ph": 5.3,
                "ec": 0.8,
                "water_level": 75.0,
                "reservoir_id": "EMBALSE_01"
            }
        }


class PredictionRequest(BaseModel):
    """Modelo para solicitudes de predicción"""
    sensor_type: str = Field(..., pattern="^(ph|temperature|conductivity|water_level)$")
    days: int = Field(..., ge=1, le=30, description="Días a predecir (1-30)")
    lookback_days: int = Field(..., ge=1, le=90, description="Días históricos para el modelo (1-90)")
    
    @validator('days')
    def validate_prediction_days(cls, v):
        """Validar días de predicción razonables"""
        if v > 7:
            raise ValueError('Predicciones a más de 7 días tienen baja confiabilidad')
        return v
    
    @validator('lookback_days')
    def validate_lookback_days(cls, v, values):
        """Validar que lookback_days sea suficiente"""
        if v < 7:
            raise ValueError('Se requieren al menos 7 días de datos históricos')
        if 'days' in values and v < values['days'] * 3:
            raise ValueError(f'Se recomienda al menos {values["days"] * 3} días históricos')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_type": "ph",
                "days": 3,
                "lookback_days": 14
            }
        }


class SensorConfigUpdate(BaseModel):
    """Modelo para actualizar configuración de sensor"""
    reservoir_id: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = True
    
    @validator('reservoir_id')
    def clean_reservoir_id(cls, v):
        """Limpiar reservoir_id"""
        return v.strip().upper()
    
    @validator('location', 'description')
    def clean_text_fields(cls, v):
        """Limpiar campos de texto"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class TimeRangeQuery(BaseModel):
    """Modelo para consultas con rango de tiempo"""
    hours: Optional[int] = Field(24, ge=1, le=8760, description="Horas de datos a recuperar (max 1 año)")
    reservoir_id: Optional[str] = Field(None, max_length=100)
    
    @validator('hours')
    def validate_hours(cls, v):
        """Validar rango de horas razonable"""
        if v > 720:  # 30 días
            raise ValueError('No se recomienda consultar más de 30 días (720 horas) de datos')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "hours": 24,
                "reservoir_id": "EMBALSE_01"
            }
        }
