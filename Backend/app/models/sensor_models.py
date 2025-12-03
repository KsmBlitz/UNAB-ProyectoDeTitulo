# Backend/models/sensor_models.py
"""
Pydantic models for sensor data validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SensorReading(BaseModel):
    """Model for validating sensor readings"""
    temperature: float = Field(..., ge=-50, le=100, description="Temperature in °C")
    ph: float = Field(..., ge=0, le=14, description="pH level")
    ec: float = Field(..., ge=0, le=20, description="Electrical conductivity (dS/m)")
    water_level: float = Field(..., ge=0, le=100, description="Water level (%)")
    timestamp: Optional[datetime] = None
    reservoir_id: Optional[str] = Field(None, min_length=1, max_length=100)
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate reasonable temperature range"""
        if v < -10 or v > 50:
            raise ValueError(f'Temperature out of operational range: {v}°C (expected: -10 to 50°C)')
        return v
    
    @validator('ph')
    def validate_ph(cls, v):
        """Validate reasonable pH range"""
        if v < 3 or v > 10:
            raise ValueError(f'pH out of operational range: {v} (expected: 3 to 10)')
        return v
    
    @validator('ec')
    def validate_conductivity(cls, v):
        """Validate reasonable conductivity range"""
        if v < 0 or v > 10:
            raise ValueError(f'Conductivity out of operational range: {v} dS/m (expected: 0 to 10)')
        return v
    
    @validator('reservoir_id')
    def validate_reservoir_id(cls, v):
        """Clean and validate reservoir_id"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('reservoir_id cannot be empty')
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
    """Model for prediction requests"""
    sensor_type: str = Field(..., pattern="^(ph|temperature|conductivity|water_level)$")
    days: int = Field(..., ge=1, le=30, description="Days to predict (1-30)")
    lookback_days: int = Field(..., ge=1, le=90, description="Historical days for model (1-90)")
    
    @validator('days')
    def validate_prediction_days(cls, v):
        """Validate reasonable prediction days"""
        if v > 7:
            raise ValueError('Predictions beyond 7 days have low reliability')
        return v
    
    @validator('lookback_days')
    def validate_lookback_days(cls, v, values):
        """Validate sufficient lookback_days"""
        if v < 7:
            raise ValueError('At least 7 days of historical data required')
        if 'days' in values and v < values['days'] * 3:
            raise ValueError(f'Recommend at least {values["days"] * 3} historical days')
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
    """Model for updating sensor configuration"""
    reservoir_id: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = True
    
    @validator('reservoir_id')
    def clean_reservoir_id(cls, v):
        """Clean reservoir_id"""
        return v.strip().upper()
    
    @validator('location', 'description')
    def clean_text_fields(cls, v):
        """Clean text fields"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class TimeRangeQuery(BaseModel):
    """Model for time range queries"""
    hours: Optional[int] = Field(24, ge=1, le=8760, description="Hours of data to retrieve (max 1 year)")
    reservoir_id: Optional[str] = Field(None, max_length=100)
    
    @validator('hours')
    def validate_hours(cls, v):
        """Validate reasonable hours range"""
        if v > 720:  # 30 days
            raise ValueError('Not recommended to query more than 30 days (720 hours) of data')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "hours": 24,
                "reservoir_id": "EMBALSE_01"
            }
        }
