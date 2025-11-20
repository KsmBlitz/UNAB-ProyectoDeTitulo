"""
Tests configuration and fixtures
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock

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
async def clean_db(test_db):
    """Clean database before each test"""
    collections = await test_db.list_collection_names()
    for collection in collections:
        await test_db[collection].delete_many({})
    yield test_db


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
        "role": "administrador",
        "password": "AdminPassword123!",
        "phone": "+56987654321",
        "whatsapp_notifications_enabled": True
    }


@pytest.fixture
def test_usuario_data():
    """Sample basic user data for testing"""
    return {
        "email": "usuario@example.com",
        "full_name": "Basic User",
        "role": "usuario",
        "password": "UserPassword123!",
        "phone": "+56911111111",
        "whatsapp_notifications_enabled": False
    }


@pytest.fixture
def test_alert_data():
    """Sample alert data for testing"""
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
def test_sensor_data():
    """Sample sensor data for testing"""
    return {
        "_id": "TEST_SENSOR_001",
        "location": "Test Reservoir",
        "temperature": 22.5,
        "pressure": 101.3,
        "water_level": 75.0,
        "flow_rate": 10.5,
        "battery": 95.0,
        "timestamp": datetime.now(timezone.utc),
        "status": "active"
    }


@pytest.fixture
def test_audit_data():
    """Sample audit log data for testing"""
    return {
        "action": "login",
        "user_email": "test@example.com",
        "details": {"ip": "192.168.1.100", "user_agent": "Test Browser"},
        "timestamp": datetime.now(timezone.utc),
        "status": "success"
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


@pytest.fixture
def mock_jwt_token():
    """Generate mock JWT token"""
    from jose import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "sub": "test@example.com",
        "role": "operario",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def mock_admin_token():
    """Generate mock admin JWT token"""
    from jose import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "sub": "admin@example.com",
        "role": "administrador",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Generate authorization headers"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def admin_auth_headers(mock_admin_token):
    """Generate admin authorization headers"""
    return {"Authorization": f"Bearer {mock_admin_token}"}


@pytest.fixture
def mock_redis():
    """Mock Redis cache"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock email service"""
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("app.services.email.send_email", mock_send)
    return mock_send


@pytest.fixture
def mock_whatsapp_service(monkeypatch):
    """Mock WhatsApp service"""
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("app.services.twilio_whatsapp.send_whatsapp_message", mock_send)
    return mock_send
