"""
Tests for notification services
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.services.notifications import (
    should_send_notification,
    mark_notification_sent,
    clear_notifications_sent_for_alert,
    build_notification_key
)


class TestNotificationKey:
    """Test notification key building"""
    
    def test_build_notification_key(self):
        """Test building notification key"""
        key = build_notification_key("email", "temperature", "sensor1", "user@example.com")
        assert key == "email:temperature:sensor1:user@example.com"
    
    def test_build_notification_key_whatsapp(self):
        """Test building WhatsApp notification key"""
        key = build_notification_key("whatsapp", "ph_range", "sensor2", "+56912345678")
        assert key == "whatsapp:ph_range:sensor2:+56912345678"


class TestThrottling:
    """Test notification throttling logic"""
    
    @pytest.mark.asyncio
    async def test_should_send_notification_first_time(self, mocker):
        """Test that notification should be sent the first time"""
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = None
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        result = await should_send_notification("test:key")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_send_notification_within_throttle(self, mocker):
        """Test that notification should not be sent within throttle period"""
        # Mock a recent notification
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = {
            "_id": "test:key",
            "last_sent": recent_time
        }
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        result = await should_send_notification("test:key")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_send_notification_after_throttle(self, mocker):
        """Test that notification should be sent after throttle period"""
        # Mock an old notification (>60 minutes ago)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=90)
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = {
            "_id": "test:key",
            "last_sent": old_time
        }
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        result = await should_send_notification("test:key")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mark_notification_sent(self, mocker):
        """Test marking notification as sent"""
        mock_collection = mocker.AsyncMock()
        mock_collection.update_one.return_value = None
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        await mark_notification_sent("test:key")
        
        # Verify update_one was called with correct parameters
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"_id": "test:key"}
        assert "$set" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_clear_notifications_for_alert(self, mocker):
        """Test clearing notification throttling for an alert"""
        mock_collection = mocker.AsyncMock()
        mock_result = mocker.Mock()
        mock_result.deleted_count = 3
        mock_collection.delete_many.return_value = mock_result
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        await clear_notifications_sent_for_alert("temperature", "sensor1")
        
        # Verify delete_many was called
        mock_collection.delete_many.assert_called_once()
        call_args = mock_collection.delete_many.call_args[0][0]
        assert "_id" in call_args
        assert "$regex" in call_args["_id"]


class TestThrottlingEdgeCases:
    """Test edge cases in throttling logic"""
    
    @pytest.mark.asyncio
    async def test_should_send_with_string_last_sent(self, mocker):
        """Test handling string format for last_sent"""
        # Some alerts may have string format timestamps
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = {
            "_id": "test:key",
            "last_sent": "2025-01-01T00:00:00+00:00"
        }
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        result = await should_send_notification("test:key")
        # Should handle string format and return True (old timestamp)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_send_on_error(self, mocker):
        """Test that notification is allowed on error"""
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.side_effect = Exception("Database error")
        
        mocker.patch("app.services.notifications.notifications_sent_collection", mock_collection)
        
        # Should default to True on error
        result = await should_send_notification("test:key")
        assert result is True
