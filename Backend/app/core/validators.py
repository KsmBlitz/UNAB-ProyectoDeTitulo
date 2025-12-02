"""
Validators Module
Centralized validation logic following Single Responsibility Principle
Each validator class handles validation for a specific domain
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import logging

from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class BaseValidator:
    """Base validator with common validation methods"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """Validate that a value is not None or empty"""
        if value is None:
            raise ValidationException(
                message=f"{field_name} is required",
                field=field_name
            )
        if isinstance(value, str) and not value.strip():
            raise ValidationException(
                message=f"{field_name} cannot be empty",
                field=field_name
            )
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format and return normalized email"""
        if not email:
            raise ValidationException(
                message="Email is required",
                field="email"
            )
        
        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationException(
                message="Invalid email format",
                field="email"
            )
        
        return email
    
    @staticmethod
    def validate_phone(phone: str, required: bool = False) -> Optional[str]:
        """Validate phone number format"""
        if not phone:
            if required:
                raise ValidationException(
                    message="Phone number is required",
                    field="phone"
                )
            return None
        
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', phone)
        
        # Must start with + and contain only digits after
        if not re.match(r'^\+\d{10,15}$', phone):
            raise ValidationException(
                message="Phone must be in international format (e.g., +56912345678)",
                field="phone"
            )
        
        return phone
    
    @staticmethod
    def validate_range(
        value: float,
        min_val: Optional[float],
        max_val: Optional[float],
        field_name: str
    ) -> None:
        """Validate that a value is within a range"""
        if min_val is not None and value < min_val:
            raise ValidationException(
                message=f"{field_name} must be at least {min_val}",
                field=field_name
            )
        if max_val is not None and value > max_val:
            raise ValidationException(
                message=f"{field_name} must be at most {max_val}",
                field=field_name
            )


class AlertConfigValidator(BaseValidator):
    """Validator for alert configuration"""
    
    # Valid alert levels
    VALID_LEVELS = ['info', 'warning', 'critical']
    
    # Valid alert types
    VALID_TYPES = [
        'ph', 'temperature', 'ec', 'conductivity', 
        'water_level', 'sensor_disconnection', 'system'
    ]
    
    @classmethod
    def validate_threshold_config(cls, config: Dict[str, Any]) -> None:
        """
        Validate threshold configuration structure
        
        Args:
            config: Threshold configuration dictionary
            
        Raises:
            ValidationException: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValidationException(
                message="Threshold configuration must be a dictionary",
                field="thresholds"
            )
        
        # Validate each metric threshold
        metric_validators = {
            'ph': cls._validate_ph_threshold,
            'temperature': cls._validate_temperature_threshold,
            'conductivity': cls._validate_conductivity_threshold,
            'water_level': cls._validate_water_level_threshold
        }
        
        for metric, threshold in config.items():
            if metric in metric_validators:
                metric_validators[metric](threshold)
    
    @classmethod
    def _validate_ph_threshold(cls, threshold: Dict[str, Any]) -> None:
        """Validate pH threshold values"""
        if not isinstance(threshold, dict):
            return
        
        min_val = threshold.get('min') or threshold.get('warning_min')
        max_val = threshold.get('max') or threshold.get('warning_max')
        
        if min_val is not None:
            cls.validate_range(min_val, 0, 14, 'pH min')
        if max_val is not None:
            cls.validate_range(max_val, 0, 14, 'pH max')
        if min_val is not None and max_val is not None and min_val >= max_val:
            raise ValidationException(
                message="pH min must be less than max",
                field="ph"
            )
    
    @classmethod
    def _validate_temperature_threshold(cls, threshold: Dict[str, Any]) -> None:
        """Validate temperature threshold values"""
        if not isinstance(threshold, dict):
            return
        
        min_val = threshold.get('min') or threshold.get('warning_min')
        max_val = threshold.get('max') or threshold.get('warning_max')
        
        if min_val is not None:
            cls.validate_range(min_val, -50, 100, 'Temperature min')
        if max_val is not None:
            cls.validate_range(max_val, -50, 100, 'Temperature max')
        if min_val is not None and max_val is not None and min_val >= max_val:
            raise ValidationException(
                message="Temperature min must be less than max",
                field="temperature"
            )
    
    @classmethod
    def _validate_conductivity_threshold(cls, threshold: Dict[str, Any]) -> None:
        """Validate conductivity threshold values"""
        if not isinstance(threshold, dict):
            return
        
        max_val = threshold.get('max') or threshold.get('warning_max')
        
        if max_val is not None:
            cls.validate_range(max_val, 0, 10, 'Conductivity max')
    
    @classmethod
    def _validate_water_level_threshold(cls, threshold: Dict[str, Any]) -> None:
        """Validate water level threshold values"""
        if not isinstance(threshold, dict):
            return
        
        min_val = threshold.get('min') or threshold.get('warning_min')
        max_val = threshold.get('max') or threshold.get('warning_max')
        
        if min_val is not None:
            cls.validate_range(min_val, 0, 100, 'Water level min')
        if max_val is not None:
            cls.validate_range(max_val, 0, 100, 'Water level max')
    
    @classmethod
    def validate_alert_level(cls, level: str) -> str:
        """Validate and normalize alert level"""
        if not level:
            raise ValidationException(
                message="Alert level is required",
                field="level"
            )
        
        normalized = level.lower().strip()
        if normalized not in cls.VALID_LEVELS:
            raise ValidationException(
                message=f"Invalid alert level. Must be one of: {', '.join(cls.VALID_LEVELS)}",
                field="level"
            )
        
        return normalized
    
    @classmethod
    def validate_alert_type(cls, alert_type: str) -> str:
        """Validate and normalize alert type"""
        if not alert_type:
            raise ValidationException(
                message="Alert type is required",
                field="type"
            )
        
        normalized = alert_type.lower().strip()
        if normalized not in cls.VALID_TYPES:
            raise ValidationException(
                message=f"Invalid alert type. Must be one of: {', '.join(cls.VALID_TYPES)}",
                field="type"
            )
        
        return normalized


class SensorValidator(BaseValidator):
    """Validator for sensor data"""
    
    @classmethod
    def validate_sensor_id(cls, sensor_id: str) -> str:
        """Validate sensor ID format"""
        if not sensor_id:
            raise ValidationException(
                message="Sensor ID is required",
                field="sensor_id"
            )
        
        sensor_id = sensor_id.strip()
        
        # Sensor ID should be alphanumeric with optional underscores
        if not re.match(r'^[A-Za-z0-9_-]+$', sensor_id):
            raise ValidationException(
                message="Sensor ID can only contain letters, numbers, underscores, and hyphens",
                field="sensor_id"
            )
        
        if len(sensor_id) < 3 or len(sensor_id) > 50:
            raise ValidationException(
                message="Sensor ID must be between 3 and 50 characters",
                field="sensor_id"
            )
        
        return sensor_id
    
    @classmethod
    def validate_sensor_reading(cls, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sensor reading data
        
        Args:
            reading: Raw sensor reading dictionary
            
        Returns:
            Validated reading dictionary
            
        Raises:
            ValidationException: If reading is invalid
        """
        if not isinstance(reading, dict):
            raise ValidationException(
                message="Sensor reading must be a dictionary",
                field="reading"
            )
        
        validated = {}
        
        # Validate pH if present
        if 'ph' in reading and reading['ph'] is not None:
            ph = float(reading['ph'])
            cls.validate_range(ph, 0, 14, 'pH')
            validated['ph'] = ph
        
        # Validate temperature if present
        if 'temperature' in reading and reading['temperature'] is not None:
            temp = float(reading['temperature'])
            cls.validate_range(temp, -50, 100, 'Temperature')
            validated['temperature'] = temp
        
        # Validate EC if present
        if 'ec' in reading and reading['ec'] is not None:
            ec = float(reading['ec'])
            cls.validate_range(ec, 0, 20, 'EC')
            validated['ec'] = ec
        
        # Validate water level if present
        if 'water_level' in reading and reading['water_level'] is not None:
            level = float(reading['water_level'])
            cls.validate_range(level, 0, 100, 'Water level')
            validated['water_level'] = level
        
        return validated


class UserValidator(BaseValidator):
    """Validator for user data"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Validated password
            
        Raises:
            ValidationException: If password doesn't meet requirements
        """
        if not password:
            raise ValidationException(
                message="Password is required",
                field="password"
            )
        
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            raise ValidationException(
                message=f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters",
                field="password"
            )
        
        # Check for at least one uppercase, one lowercase, one digit
        if not re.search(r'[A-Z]', password):
            raise ValidationException(
                message="Password must contain at least one uppercase letter",
                field="password"
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationException(
                message="Password must contain at least one lowercase letter",
                field="password"
            )
        
        if not re.search(r'\d', password):
            raise ValidationException(
                message="Password must contain at least one digit",
                field="password"
            )
        
        return password
    
    @classmethod
    def validate_role(cls, role: str) -> str:
        """Validate user role"""
        valid_roles = ['admin', 'operario', 'viewer']
        
        if not role:
            raise ValidationException(
                message="Role is required",
                field="role"
            )
        
        role = role.lower().strip()
        if role not in valid_roles:
            raise ValidationException(
                message=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
                field="role"
            )
        
        return role
    
    @classmethod
    def validate_user_create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user creation data
        
        Args:
            data: User creation data
            
        Returns:
            Validated data
        """
        validated = {}
        
        validated['email'] = cls.validate_email(data.get('email', ''))
        validated['password'] = cls.validate_password(data.get('password', ''))
        
        if data.get('name'):
            validated['name'] = data['name'].strip()
        
        if data.get('phone'):
            validated['phone'] = cls.validate_phone(data['phone'])
        
        if data.get('role'):
            validated['role'] = cls.validate_role(data['role'])
        else:
            validated['role'] = 'operario'  # Default role
        
        return validated
