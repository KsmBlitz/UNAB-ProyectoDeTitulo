"""
Tests for Rate Limiting middleware
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def app_with_rate_limit():
    """Create test app with rate limiting"""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/api/token")
    async def login_endpoint():
        return {"access_token": "test_token"}
    
    @app.post("/api/users")
    async def create_user_endpoint():
        return {"message": "user created"}
    
    return app


@pytest.fixture
def client(app_with_rate_limit):
    """Create test client"""
    return TestClient(app_with_rate_limit)


class TestAnonymousRateLimit:
    """Test rate limiting for anonymous users"""
    
    def test_anonymous_within_limit(self, client):
        """Test that anonymous users can make requests within limit"""
        for i in range(50):
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    def test_anonymous_exceeds_limit(self, client):
        """Test that anonymous users are blocked after exceeding limit"""
        # Make 101 requests (limit is 100/min for anonymous)
        for i in range(101):
            response = client.get("/test")
            
            if i < 100:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                data = response.json()
                assert "detail" in data
                assert "retry_after" in data
                assert response.headers.get("Retry-After") == "60"


class TestAuthenticatedUserRateLimit:
    """Test rate limiting for authenticated users"""
    
    def test_usuario_role_within_limit(self, client, mock_jwt_token):
        """Test that basic users can make requests within their limit (200/min)"""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        for i in range(150):
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
            assert response.headers.get("X-RateLimit-Role") == "operario"
    
    def test_usuario_role_exceeds_limit(self, client):
        """Test that basic users are blocked after exceeding 200/min"""
        from jose import jwt
        
        # Create token for 'usuario' role (200/min limit)
        payload = {
            "sub": "usuario@example.com",
            "role": "usuario",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        from app.config.settings import settings
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make 205 requests
        for i in range(205):
            response = client.get("/test", headers=headers)
            
            if i < 200:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                data = response.json()
                assert data["limit"] == 200
                assert data["role"] == "usuario"
    
    def test_operario_role_higher_limit(self, client, mock_jwt_token):
        """Test that operarios have higher limit (300/min)"""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Make 250 requests (should all succeed)
        for i in range(250):
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
            assert response.headers.get("X-RateLimit-Limit") == "300"


class TestAdminRateLimit:
    """Test rate limiting for administrators"""
    
    def test_admin_unlimited_requests(self, client, mock_admin_token):
        """Test that admins have no rate limit"""
        headers = {"Authorization": f"Bearer {mock_admin_token}"}
        
        # Make 500 requests (should all succeed)
        for i in range(500):
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
            assert response.headers.get("X-RateLimit-Limit") == "unlimited"
            assert response.headers.get("X-RateLimit-Remaining") == "unlimited"
            assert response.headers.get("X-RateLimit-Role") == "administrador"


class TestCriticalEndpointsRateLimit:
    """Test rate limiting for critical endpoints"""
    
    def test_login_endpoint_limited(self, client):
        """Test that login endpoint has strict limit (5/min)"""
        for i in range(6):
            response = client.get("/api/token")
            
            if i < 5:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                data = response.json()
                assert "Demasiadas solicitudes" in data["detail"]
    
    def test_create_user_limited(self, client):
        """Test that user creation has strict limit (5/min)"""
        for i in range(6):
            response = client.post("/api/users")
            
            if i < 5:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
    
    def test_critical_endpoint_applies_to_admins(self, client, mock_admin_token):
        """Test that critical endpoint limits apply even to admins"""
        headers = {"Authorization": f"Bearer {mock_admin_token}"}
        
        for i in range(6):
            response = client.get("/api/token", headers=headers)
            
            if i < 5:
                assert response.status_code == 200
            else:
                # Even admins are rate limited on critical endpoints
                assert response.status_code == 429


class TestRateLimitHeaders:
    """Test rate limit response headers"""
    
    def test_headers_present(self, client):
        """Test that rate limit headers are present in responses"""
        response = client.get("/test")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_remaining_decreases(self, client):
        """Test that X-RateLimit-Remaining decreases with each request"""
        first_response = client.get("/test")
        first_remaining = int(first_response.headers["X-RateLimit-Remaining"])
        
        second_response = client.get("/test")
        second_remaining = int(second_response.headers["X-RateLimit-Remaining"])
        
        assert second_remaining < first_remaining
    
    def test_reset_timestamp_valid(self, client):
        """Test that X-RateLimit-Reset is a valid future timestamp"""
        response = client.get("/test")
        reset_timestamp = int(response.headers["X-RateLimit-Reset"])
        now_timestamp = int(datetime.utcnow().timestamp())
        
        assert reset_timestamp > now_timestamp
        assert reset_timestamp <= now_timestamp + 60  # Within 1 minute


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware methods"""
    
    def test_clean_old_requests(self):
        """Test that old requests are cleaned up"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        now = datetime.utcnow()
        old_request = (now - timedelta(minutes=2), "/test")
        recent_request = (now - timedelta(seconds=30), "/test")
        
        requests = [old_request, recent_request]
        cleaned = middleware._clean_old_requests(requests, timedelta(minutes=1))
        
        assert len(cleaned) == 1
        assert cleaned[0] == recent_request
    
    def test_is_critical_endpoint(self):
        """Test critical endpoint detection"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        assert middleware._is_critical_endpoint("/api/token", "POST") == True
        assert middleware._is_critical_endpoint("/api/users", "POST") == True
        assert middleware._is_critical_endpoint("/api/users", "GET") == False
        assert middleware._is_critical_endpoint("/api/sensors", "GET") == False
    
    def test_get_rate_limit_for_role(self):
        """Test rate limit retrieval by role"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        assert middleware._get_rate_limit_for_role("administrador") is None  # Unlimited
        assert middleware._get_rate_limit_for_role("operario") == 300
        assert middleware._get_rate_limit_for_role("usuario") == 200
        assert middleware._get_rate_limit_for_role(None) == 100  # Anonymous
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        # Add some test data
        now = datetime.utcnow()
        middleware.ip_requests["192.168.1.1"] = [(now, "/test")]
        middleware.user_requests["test@example.com"] = [(now, "/test", "operario")]
        
        stats = middleware.get_stats()
        
        assert stats["active_ips"] == 1
        assert stats["active_users"] == 1
        assert "rate_limits" in stats
        assert stats["rate_limits"]["operario"] == "300/min"


class TestExcludedRoutes:
    """Test that certain routes are excluded from rate limiting"""
    
    def test_health_check_excluded(self, app_with_rate_limit):
        """Test that health checks are not rate limited"""
        app = app_with_rate_limit
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        client = TestClient(app)
        
        # Make 200 requests to health endpoint
        for i in range(200):
            response = client.get("/health")
            assert response.status_code == 200
            # Health endpoints don't get rate limit headers
    
    def test_websocket_excluded(self, app_with_rate_limit):
        """Test that WebSocket routes are not rate limited"""
        app = app_with_rate_limit
        
        @app.get("/ws/test")
        async def websocket_route():
            return {"message": "websocket"}
        
        client = TestClient(app)
        
        # Make many requests
        for i in range(200):
            response = client.get("/ws/test")
            assert response.status_code == 200


class TestHourlyLimit:
    """Test hourly rate limiting for authenticated users"""
    
    @pytest.mark.asyncio
    async def test_hourly_limit_not_exceeded(self, client, mock_jwt_token):
        """Test that users can make requests within hourly limit"""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Make 100 requests (far below 10,000/hour limit)
        for i in range(100):
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
    
    def test_admin_no_hourly_limit(self, client, mock_admin_token):
        """Test that admins don't have hourly limit"""
        headers = {"Authorization": f"Bearer {mock_admin_token}"}
        
        # Make many requests
        for i in range(500):
            response = client.get("/test", headers=headers)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
