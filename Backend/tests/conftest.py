"""
Tests configuration and fixtures
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_client():
    """Create test database client"""
    client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
    yield client
    client.close()


@pytest.fixture(scope="session")
async def test_db(test_db_client):
    """Get test database"""
    db = test_db_client[f"{settings.DATABASE_NAME}_test"]
    yield db
    # Cleanup after all tests
    await test_db_client.drop_database(f"{settings.DATABASE_NAME}_test")


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "operario",
        "password": "TestPassword123!",
        "phone": "+56912345678",
        "whatsapp_notifications_enabled": True
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing"""
    return {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "password": "AdminPassword123!",
        "phone": "+56987654321",
        "whatsapp_notifications_enabled": True
    }


@pytest.fixture
def test_alert_data():
    """Sample alert data for testing"""
    from datetime import datetime, timezone
    return {
        "_id": "test-alert-001",
        "type": "temperature",
        "level": "critical",
        "title": "Test Alert",
        "message": "This is a test alert",
        "value": 30.5,
        "threshold_info": "Normal range: 15-25°C",
        "location": "Test Reservoir",
        "sensor_id": "TEST_SENSOR_001",
        "created_at": datetime.now(timezone.utc),
        "is_resolved": False,
        "status": "active"
    }


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing"""
    monkeypatch.setattr("app.config.settings.SMTP_SERVER", "smtp.test.com")
    monkeypatch.setattr("app.config.settings.SMTP_PORT", 587)
    monkeypatch.setattr("app.config.settings.SMTP_USERNAME", "test@test.com")
    monkeypatch.setattr("app.config.settings.SMTP_PASSWORD", "testpass")
    monkeypatch.setattr("app.config.settings.FROM_EMAIL", "test@test.com")
    monkeypatch.setattr("app.config.settings.WHATSAPP_ENABLED", False)
