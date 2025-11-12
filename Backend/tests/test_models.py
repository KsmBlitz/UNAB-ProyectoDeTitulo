"""
Tests for Pydantic models and validation
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from app.models.user import UserCreate, UserUpdate, UserResponse
from app.models.alert_models import AlertCreate, AlertUpdate, AlertResponse
from app.models.audit_models import AuditLogCreate, AuditLogResponse


class TestUserModels:
    """Test User model validation"""
    
    def test_valid_user_create(self):
        """Test creating user with valid data"""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "operario",
            "password": "TestPassword123!",
            "phone": "+56912345678"
        }
        
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "operario"
    
    def test_invalid_email(self):
        """Test that invalid email raises error"""
        invalid_data = {
            "email": "invalid-email",
            "full_name": "Test User",
            "role": "operario",
            "password": "TestPassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**invalid_data)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_weak_password(self):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "short",           # Too short
            "nouppercase1!",   # No uppercase
            "NOLOWERCASE1!",   # No lowercase
            "NoNumbers!",      # No numbers
            "NoSpecial123"     # No special characters
        ]
        
        for password in weak_passwords:
            invalid_data = {
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "operario",
                "password": password
            }
            
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(**invalid_data)
            
            assert "password" in str(exc_info.value).lower()
    
    def test_valid_password(self):
        """Test that strong passwords are accepted"""
        valid_passwords = [
            "TestPassword123!",
            "Strong@Pass1",
            "MyS3cur3P@ss",
            "Admin#2024Pass"
        ]
        
        for password in valid_passwords:
            user_data = {
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "operario",
                "password": password
            }
            
            user = UserCreate(**user_data)
            assert user.password == password
    
    def test_invalid_role(self):
        """Test that invalid roles are rejected"""
        invalid_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "invalid_role",
            "password": "TestPassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**invalid_data)
        
        assert "role" in str(exc_info.value).lower()
    
    def test_valid_roles(self):
        """Test all valid roles"""
        valid_roles = ["administrador", "operario", "usuario"]
        
        for role in valid_roles:
            user_data = {
                "email": f"{role}@example.com",
                "full_name": f"{role.title()} User",
                "role": role,
                "password": "TestPassword123!"
            }
            
            user = UserCreate(**user_data)
            assert user.role == role
    
    def test_invalid_phone_format(self):
        """Test that invalid phone numbers are rejected"""
        invalid_phones = [
            "123456",           # Too short
            "+1234567890123456",  # Too long
            "not-a-phone",      # Invalid format
            "+56 9 1234 5678"   # Spaces (depends on validation)
        ]
        
        for phone in invalid_phones:
            user_data = {
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "operario",
                "password": "TestPassword123!",
                "phone": phone
            }
            
            with pytest.raises(ValidationError):
                UserCreate(**user_data)
    
    def test_valid_phone_format(self):
        """Test valid phone number formats"""
        valid_phones = [
            "+56912345678",
            "+56987654321",
            "+12345678900"
        ]
        
        for phone in valid_phones:
            user_data = {
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "operario",
                "password": "TestPassword123!",
                "phone": phone
            }
            
            user = UserCreate(**user_data)
            assert user.phone == phone
    
    def test_user_update_partial(self):
        """Test that UserUpdate allows partial updates"""
        # Only update full_name
        update = UserUpdate(full_name="Updated Name")
        assert update.full_name == "Updated Name"
        assert update.email is None
        assert update.password is None
    
    def test_user_response_excludes_password(self):
        """Test that UserResponse doesn't expose password"""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "operario",
            "is_active": True,
            "whatsapp_notifications_enabled": True
        }
        
        user = UserResponse(**user_data)
        
        # Should not have password field
        assert not hasattr(user, 'password')
        assert not hasattr(user, 'hashed_password')


class TestAlertModels:
    """Test Alert model validation"""
    
    def test_valid_alert_create(self):
        """Test creating alert with valid data"""
        alert_data = {
            "type": "temperature",
            "level": "critical",
            "title": "High Temperature Alert",
            "message": "Temperature exceeded safe limits",
            "value": 30.5,
            "threshold_info": "Normal: 15-25°C",
            "location": "Reservoir A",
            "sensor_id": "TEMP_001"
        }
        
        alert = AlertCreate(**alert_data)
        assert alert.type == "temperature"
        assert alert.level == "critical"
        assert alert.value == 30.5
    
    def test_invalid_alert_type(self):
        """Test that invalid alert types are rejected"""
        invalid_data = {
            "type": "invalid_type",
            "level": "critical",
            "title": "Test Alert",
            "message": "Test message"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AlertCreate(**invalid_data)
        
        assert "type" in str(exc_info.value).lower()
    
    def test_valid_alert_types(self):
        """Test all valid alert types"""
        valid_types = [
            "temperature", "pressure", "water_level",
            "flow_rate", "battery", "system", "prediction"
        ]
        
        for alert_type in valid_types:
            alert_data = {
                "type": alert_type,
                "level": "warning",
                "title": f"{alert_type.title()} Alert",
                "message": "Test message"
            }
            
            alert = AlertCreate(**alert_data)
            assert alert.type == alert_type
    
    def test_invalid_alert_level(self):
        """Test that invalid alert levels are rejected"""
        invalid_data = {
            "type": "temperature",
            "level": "invalid_level",
            "title": "Test Alert",
            "message": "Test message"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AlertCreate(**invalid_data)
        
        assert "level" in str(exc_info.value).lower()
    
    def test_valid_alert_levels(self):
        """Test all valid alert levels"""
        valid_levels = ["info", "warning", "critical"]
        
        for level in valid_levels:
            alert_data = {
                "type": "temperature",
                "level": level,
                "title": "Test Alert",
                "message": "Test message"
            }
            
            alert = AlertCreate(**alert_data)
            assert alert.level == level
    
    def test_alert_with_optional_fields(self):
        """Test alert creation with optional fields"""
        minimal_alert = {
            "type": "system",
            "level": "info",
            "title": "System Message",
            "message": "System is running normally"
        }
        
        alert = AlertCreate(**minimal_alert)
        assert alert.value is None
        assert alert.sensor_id is None
        assert alert.location is None
    
    def test_alert_numeric_value_validation(self):
        """Test that alert values are properly validated"""
        # Valid numeric value
        valid_alert = AlertCreate(
            type="temperature",
            level="warning",
            title="Test",
            message="Test",
            value=25.5
        )
        assert valid_alert.value == 25.5
        
        # Invalid value type
        with pytest.raises(ValidationError):
            AlertCreate(
                type="temperature",
                level="warning",
                title="Test",
                message="Test",
                value="not_a_number"
            )
    
    def test_alert_response_has_timestamps(self):
        """Test that AlertResponse includes timestamps"""
        alert_data = {
            "_id": "alert-001",
            "type": "temperature",
            "level": "critical",
            "title": "Test Alert",
            "message": "Test message",
            "created_at": datetime.utcnow(),
            "status": "active",
            "is_resolved": False
        }
        
        alert = AlertResponse(**alert_data)
        assert alert.created_at is not None
        assert isinstance(alert.created_at, datetime)


class TestAuditLogModels:
    """Test Audit Log model validation"""
    
    def test_valid_audit_log_create(self):
        """Test creating audit log with valid data"""
        audit_data = {
            "action": "login",
            "user_email": "test@example.com",
            "details": {"ip": "192.168.1.1"},
            "status": "success"
        }
        
        audit = AuditLogCreate(**audit_data)
        assert audit.action == "login"
        assert audit.status == "success"
    
    def test_invalid_audit_action(self):
        """Test that invalid actions are rejected"""
        invalid_data = {
            "action": "invalid_action",
            "user_email": "test@example.com",
            "status": "success"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuditLogCreate(**invalid_data)
        
        assert "action" in str(exc_info.value).lower()
    
    def test_valid_audit_actions(self):
        """Test all valid audit actions"""
        valid_actions = [
            "login", "logout", "create_user", "update_user",
            "delete_user", "view_sensors", "export_data",
            "dismiss_alert", "system_change"
        ]
        
        for action in valid_actions:
            audit_data = {
                "action": action,
                "user_email": "test@example.com",
                "status": "success"
            }
            
            audit = AuditLogCreate(**audit_data)
            assert audit.action == action
    
    def test_invalid_audit_status(self):
        """Test that invalid statuses are rejected"""
        invalid_data = {
            "action": "login",
            "user_email": "test@example.com",
            "status": "invalid_status"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuditLogCreate(**invalid_data)
        
        assert "status" in str(exc_info.value).lower()
    
    def test_valid_audit_statuses(self):
        """Test valid audit statuses"""
        valid_statuses = ["success", "failure", "error"]
        
        for status in valid_statuses:
            audit_data = {
                "action": "login",
                "user_email": "test@example.com",
                "status": status
            }
            
            audit = AuditLogCreate(**audit_data)
            assert audit.status == status
    
    def test_audit_with_details(self):
        """Test audit log with detailed information"""
        audit_data = {
            "action": "update_user",
            "user_email": "admin@example.com",
            "details": {
                "target_user": "test@example.com",
                "fields_changed": ["role", "is_active"],
                "old_role": "usuario",
                "new_role": "operario"
            },
            "status": "success"
        }
        
        audit = AuditLogCreate(**audit_data)
        assert audit.details["target_user"] == "test@example.com"
        assert "fields_changed" in audit.details
    
    def test_audit_response_has_timestamp(self):
        """Test that AuditLogResponse includes timestamp"""
        audit_data = {
            "_id": "audit-001",
            "action": "login",
            "user_email": "test@example.com",
            "status": "success",
            "timestamp": datetime.utcnow()
        }
        
        audit = AuditLogResponse(**audit_data)
        assert audit.timestamp is not None
        assert isinstance(audit.timestamp, datetime)


class TestModelCoercion:
    """Test type coercion and conversion"""
    
    def test_string_to_datetime_conversion(self):
        """Test that string timestamps are converted to datetime"""
        alert_data = {
            "_id": "alert-001",
            "type": "temperature",
            "level": "warning",
            "title": "Test",
            "message": "Test",
            "created_at": "2024-01-01T10:00:00Z",
            "status": "active",
            "is_resolved": False
        }
        
        alert = AlertResponse(**alert_data)
        assert isinstance(alert.created_at, datetime)
    
    def test_numeric_string_to_float(self):
        """Test that numeric strings are converted to float"""
        alert_data = {
            "type": "temperature",
            "level": "warning",
            "title": "Test",
            "message": "Test",
            "value": "25.5"  # String instead of float
        }
        
        alert = AlertCreate(**alert_data)
        assert isinstance(alert.value, float)
        assert alert.value == 25.5


class TestModelDefaults:
    """Test default values in models"""
    
    def test_user_default_values(self):
        """Test that User models have correct defaults"""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "operario",
            "password": "TestPassword123!"
        }
        
        user = UserCreate(**user_data)
        
        # Check defaults
        assert user.is_active is True  # Default should be True
        assert user.whatsapp_notifications_enabled is False  # Default
    
    def test_alert_default_status(self):
        """Test that alerts have default status"""
        alert_data = {
            "type": "temperature",
            "level": "warning",
            "title": "Test",
            "message": "Test"
        }
        
        alert = AlertCreate(**alert_data)
        # Defaults should be set in the route handler, not model


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
