"""
Tests for NotificationService
Tests throttling and notification key building following the refactored SOLID architecture
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification_service import NotificationService, NotificationType


class TestNotificationKey:
    """Test notification key building"""
    
    def test_build_notification_key_email(self):
        """Test building email notification key"""
        service = NotificationService()
        key = service._build_notification_key(
            NotificationType.EMAIL, 
            "temperature", 
            "sensor1", 
            "user@example.com"
        )
        assert key == "email:temperature:sensor1:user@example.com"
    
    def test_build_notification_key_whatsapp(self):
        """Test building WhatsApp notification key"""
        service = NotificationService()
        key = service._build_notification_key(
            NotificationType.WHATSAPP, 
            "ph_range", 
            "sensor2", 
            "+56912345678"
        )
        assert key == "whatsapp:ph_range:sensor2:+56912345678"


class TestThrottling:
    """Test notification throttling logic"""
    
    @pytest.mark.asyncio
    async def test_should_send_notification_first_time(self):
        """Test that notification should be sent the first time (no recent record)"""
        service = NotificationService(throttle_minutes=60)
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            
            result = await service._should_send_notification("test:key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_send_notification_within_throttle(self):
        """Test that notification should not be sent within throttle period"""
        service = NotificationService(throttle_minutes=60)
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            # Return a recent record indicating throttle is active
            mock_collection.find_one = AsyncMock(return_value={
                "key": "test:key",
                "sent_at": datetime.utcnow()
            })
            
            result = await service._should_send_notification("test:key")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_should_send_notification_after_throttle(self):
        """Test that notification should be sent after throttle period expired"""
        service = NotificationService(throttle_minutes=60)
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            # No recent records found (simulates expired throttle)
            mock_collection.find_one = AsyncMock(return_value=None)
            
            result = await service._should_send_notification("test:key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_mark_notification_sent(self):
        """Test marking notification as sent"""
        service = NotificationService()
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            mock_collection.insert_one = AsyncMock(return_value=None)
            
            await service._mark_notification_sent("test:key")
            
            # Verify insert_one was called with correct key
            mock_collection.insert_one.assert_called_once()
            call_args = mock_collection.insert_one.call_args[0][0]
            assert call_args["key"] == "test:key"
            assert "sent_at" in call_args
    
    @pytest.mark.asyncio
    async def test_clear_throttle_for_alert(self):
        """Test clearing notification throttling for an alert"""
        service = NotificationService()
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            mock_result = MagicMock()
            mock_result.deleted_count = 3
            mock_collection.delete_many = AsyncMock(return_value=mock_result)
            
            await service.clear_throttle_for_alert("sensor1")
            
            # Verify delete_many was called with regex pattern
            mock_collection.delete_many.assert_called_once()
            call_args = mock_collection.delete_many.call_args[0][0]
            assert "key" in call_args
            assert "$regex" in call_args["key"]


class TestThrottlingEdgeCases:
    """Test edge cases in throttling logic"""
    
    @pytest.mark.asyncio
    async def test_should_send_on_database_error(self):
        """Test that notification is allowed on database error (fail-open)"""
        service = NotificationService()
        
        with patch("app.services.notification_service.notifications_sent_collection") as mock_collection:
            mock_collection.find_one = AsyncMock(side_effect=Exception("Database error"))
            
            # Should default to True on error (fail-open for critical notifications)
            result = await service._should_send_notification("test:key")
            assert result is True


class TestNotificationTypes:
    """Test notification type enum"""
    
    def test_notification_type_values(self):
        """Test that notification types have correct string values"""
        assert NotificationType.EMAIL.value == "email"
        assert NotificationType.WHATSAPP.value == "whatsapp"
        assert NotificationType.SMS.value == "sms"
    
    def test_notification_type_comparison(self):
        """Test notification type can be compared as strings"""
        assert NotificationType.EMAIL == "email"
        assert NotificationType.WHATSAPP == "whatsapp"
