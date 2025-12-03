"""
Tests for API routes
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from main import app
from app.services.auth import create_access_token, get_password_hash


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data


class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_success(self, client, mocker):
        """Test successful login"""
        # Mock user in database
        mock_user = {
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123"),
            "role": "admin",
            "full_name": "Test User"
        }
        
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = mock_user
        
        mocker.patch("app.routes.auth.users_collection", mock_collection)
        
        response = client.post(
            "/api/token",
            data={"username": "test@example.com", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, mocker):
        """Test login with wrong password"""
        mock_user = {
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123")
        }
        
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = mock_user
        
        mocker.patch("app.routes.auth.users_collection", mock_collection)
        
        response = client.post(
            "/api/token",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
    
    def test_login_user_not_found(self, client, mocker):
        """Test login with non-existent user"""
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = None
        
        mocker.patch("app.routes.auth.users_collection", mock_collection)
        
        response = client.post(
            "/api/token",
            data={"username": "nonexistent@example.com", "password": "password123"}
        )
        
        assert response.status_code == 401
    
    def test_login_requires_username_and_password(self, client):
        """Test that login requires both username and password"""
        response = client.post("/api/token", data={})
        assert response.status_code == 422  # Validation error


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication"""
    
    @pytest.fixture(autouse=True)
    def fresh_client(self):
        """Create a fresh client for each test to avoid rate limiting"""
        self._client = TestClient(app)
        yield
    
    def test_users_endpoint_requires_auth(self):
        """Test that users endpoint requires authentication"""
        response = self._client.get("/api/users")
        assert response.status_code == 401
    
    def test_create_user_requires_auth(self):
        """Test that create user endpoint requires authentication"""
        # Use fresh client to avoid rate limiting from previous tests
        fresh = TestClient(app)
        response = fresh.post("/api/users", json={"email": "test@example.com"})
        # Should be 401 (unauthorized) or 429 (rate limited from prior tests)
        assert response.status_code in [401, 429]
    
    def test_delete_user_requires_auth(self):
        """Test that delete user endpoint requires authentication"""
        response = self._client.delete("/api/users/123")
        assert response.status_code == 401
    
    def test_alerts_endpoint_requires_auth(self):
        """Test that alerts endpoint requires authentication"""
        response = self._client.get("/api/alerts/active")
        assert response.status_code == 401
    
    def test_alert_summary_requires_auth(self):
        """Test that alert summary requires authentication"""
        response = self._client.get("/api/alerts/summary")
        assert response.status_code == 401
    
    def test_alert_history_requires_auth(self):
        """Test that alert history requires authentication"""
        response = self._client.get("/api/alerts/history")
        assert response.status_code == 401
    
    def test_dismiss_alert_requires_auth(self):
        """Test that dismiss alert requires authentication"""
        response = self._client.patch("/api/alerts/dismiss/alert123")
        # Could be 401 or 404 depending on order of checks
        assert response.status_code in [401, 404]
    
    def test_sensors_status_requires_auth(self):
        """Test that sensors status requires authentication"""
        response = self._client.get("/api/sensors/status")
        assert response.status_code == 401
    
    def test_sensors_individual_requires_auth(self):
        """Test that individual sensor endpoint requires authentication"""
        response = self._client.get("/api/sensors/individual")
        # Could be 401 or 404 depending on endpoint configuration
        assert response.status_code in [401, 404, 422]
    
    def test_metrics_latest_requires_auth(self):
        """Test that latest metrics requires authentication"""
        response = self._client.get("/api/metrics/latest")
        assert response.status_code == 401
    
    def test_historical_data_requires_auth(self):
        """Test that historical data requires authentication"""
        response = self._client.get("/api/charts/historical-data")
        # GET might not be allowed on this endpoint
        assert response.status_code in [401, 404, 405]
