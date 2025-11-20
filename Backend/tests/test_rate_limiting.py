# Backend/tests/test_rate_limiting.py
"""
Tests for rate limiting middleware
Tests role-based limits, critical endpoints, and rate limit headers
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.middleware.rate_limit import RateLimitMiddleware


# ============================================
# RATE LIMIT CONFIGURATION TESTS
# ============================================

class TestRateLimitConfiguration:
    """Tests para configuración de rate limiting"""
    
    def test_rate_limit_initialization(self):
        """Test: middleware se inicializa con límites correctos"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Verificar límites por rol
        assert middleware.ROLE_LIMITS["administrador"] is None  # Sin límite
        assert middleware.ROLE_LIMITS["operario"] == 300
        assert middleware.ROLE_LIMITS["usuario"] == 200
        assert middleware.ROLE_LIMITS["anonymous"] == 100
        
        # Verificar límites especiales
        assert middleware.CRITICAL_ENDPOINTS_LIMIT == 5
        assert middleware.USER_LIMIT_PER_HOUR == 10000
    
    def test_critical_endpoints_list(self):
        """Test: endpoints críticos están definidos"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert "/api/token" in middleware.CRITICAL_ENDPOINTS
        assert "/api/forgot-password" in middleware.CRITICAL_ENDPOINTS
        assert "/api/reset-password" in middleware.CRITICAL_ENDPOINTS
        assert "/api/users" in middleware.CRITICAL_ENDPOINTS
    
    def test_get_rate_limit_for_roles(self):
        """Test: obtener límite según rol"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._get_rate_limit_for_role("administrador") is None
        assert middleware._get_rate_limit_for_role("operario") == 300
        assert middleware._get_rate_limit_for_role("usuario") == 200
        assert middleware._get_rate_limit_for_role(None) == 100  # Anonymous
    
    def test_get_rate_limit_case_insensitive(self):
        """Test: rol case-insensitive"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Debe funcionar con mayúsculas/minúsculas
        assert middleware._get_rate_limit_for_role("OPERARIO") == 300
        assert middleware._get_rate_limit_for_role("Usuario") == 200
    
    def test_unknown_role_defaults_to_usuario(self):
        """Test: rol desconocido usa límite de usuario"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._get_rate_limit_for_role("unknown_role") == 200


# ============================================
# CRITICAL ENDPOINT DETECTION TESTS
# ============================================

class TestCriticalEndpointDetection:
    """Tests para detección de endpoints críticos"""
    
    def test_is_critical_endpoint_login(self):
        """Test: /api/token es crítico"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._is_critical_endpoint("/api/token", "POST") is True
    
    def test_is_critical_endpoint_forgot_password(self):
        """Test: forgot-password es crítico"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._is_critical_endpoint("/api/forgot-password", "POST") is True
    
    def test_is_critical_endpoint_reset_password(self):
        """Test: reset-password es crítico"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._is_critical_endpoint("/api/reset-password", "POST") is True
    
    def test_is_critical_endpoint_users_post(self):
        """Test: POST /api/users es crítico (crear usuario)"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._is_critical_endpoint("/api/users", "POST") is True
    
    def test_is_not_critical_endpoint_users_get(self):
        """Test: GET /api/users NO es crítico"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Solo POST de users es crítico
        assert middleware._is_critical_endpoint("/api/users", "GET") is False
    
    def test_is_not_critical_endpoint_sensors(self):
        """Test: /api/sensors NO es crítico"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        assert middleware._is_critical_endpoint("/api/sensors", "GET") is False
        assert middleware._is_critical_endpoint("/api/sensors/status", "GET") is False


# ============================================
# REQUEST CLEANING TESTS
# ============================================

class TestRequestCleaning:
    """Tests para limpieza de requests antiguos"""
    
    def test_clean_old_requests(self):
        """Test: eliminar requests fuera de ventana de tiempo"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        now = datetime.utcnow()
        old_time = now - timedelta(minutes=5)
        recent_time = now - timedelta(seconds=30)
        
        requests_list = [
            (old_time, "/api/test1"),
            (recent_time, "/api/test2"),
            (now, "/api/test3")
        ]
        
        # Limpiar requests más antiguos de 1 minuto
        cleaned = middleware._clean_old_requests(requests_list, timedelta(minutes=1))
        
        # Solo deben quedar los requests recientes
        assert len(cleaned) == 2
        assert cleaned[0][1] == "/api/test2"
        assert cleaned[1][1] == "/api/test3"
    
    def test_clean_all_old_requests(self):
        """Test: todos los requests son antiguos"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        old_time = datetime.utcnow() - timedelta(hours=2)
        requests_list = [
            (old_time, "/api/test1"),
            (old_time, "/api/test2")
        ]
        
        cleaned = middleware._clean_old_requests(requests_list, timedelta(minutes=1))
        
        assert len(cleaned) == 0
    
    def test_clean_no_old_requests(self):
        """Test: ningún request es antiguo"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        now = datetime.utcnow()
        requests_list = [
            (now, "/api/test1"),
            (now, "/api/test2")
        ]
        
        cleaned = middleware._clean_old_requests(requests_list, timedelta(minutes=1))
        
        assert len(cleaned) == 2


# ============================================
# USER TOKEN EXTRACTION TESTS
# ============================================

class TestUserTokenExtraction:
    """Tests para extracción de usuario del token JWT"""
    
    @patch('app.middleware.rate_limit.jwt.decode')
    def test_get_user_from_valid_token(self, mock_jwt_decode):
        """Test: extraer usuario de token válido"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Mock del token JWT decodificado
        mock_jwt_decode.return_value = {
            "sub": "test@example.com",
            "role": "usuario"
        }
        
        request_mock = Mock()
        request_mock.headers.get.return_value = "Bearer valid_token_here"
        
        email, role = middleware._get_user_from_token(request_mock)
        
        assert email == "test@example.com"
        assert role == "usuario"
    
    def test_get_user_from_request_without_auth_header(self):
        """Test: request sin header de autorización"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        request_mock = Mock()
        request_mock.headers.get.return_value = None
        
        email, role = middleware._get_user_from_token(request_mock)
        
        assert email is None
        assert role is None
    
    def test_get_user_from_invalid_auth_header(self):
        """Test: header de autorización sin 'Bearer'"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        request_mock = Mock()
        request_mock.headers.get.return_value = "InvalidTokenFormat"
        
        email, role = middleware._get_user_from_token(request_mock)
        
        assert email is None
        assert role is None
    
    @patch('app.middleware.rate_limit.jwt.decode')
    def test_get_user_from_expired_token(self, mock_jwt_decode):
        """Test: token expirado retorna None"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Simular token expirado
        mock_jwt_decode.side_effect = Exception("Token expired")
        
        request_mock = Mock()
        request_mock.headers.get.return_value = "Bearer expired_token"
        
        email, role = middleware._get_user_from_token(request_mock)
        
        assert email is None
        assert role is None


# ============================================
# STATISTICS TESTS
# ============================================

class TestRateLimitStatistics:
    """Tests para estadísticas de rate limiting"""
    
    def test_get_stats_empty(self):
        """Test: estadísticas con cero requests"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        stats = middleware.get_stats()
        
        assert stats["active_ips"] == 0
        assert stats["active_users"] == 0
        assert stats["total_ip_requests"] == 0
        assert stats["total_user_requests"] == 0
        assert "rate_limits" in stats
    
    def test_get_stats_with_data(self):
        """Test: estadísticas con datos"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Simular algunos requests
        now = datetime.utcnow()
        middleware.ip_requests["192.168.1.1"] = [(now, "/api/test")]
        middleware.ip_requests["192.168.1.2"] = [(now, "/api/test2")]
        middleware.user_requests["user@test.com"] = [(now, "/api/test", "usuario")]
        
        stats = middleware.get_stats()
        
        assert stats["active_ips"] == 2
        assert stats["active_users"] == 1
        assert stats["total_ip_requests"] == 2
        assert stats["total_user_requests"] == 1
    
    def test_get_stats_rate_limits_info(self):
        """Test: estadísticas incluyen info de límites"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        stats = middleware.get_stats()
        
        assert stats["rate_limits"]["administrador"] == "unlimited"
        assert stats["rate_limits"]["operario"] == "300/min"
        assert stats["rate_limits"]["usuario"] == "200/min"
        assert stats["rate_limits"]["anonymous"] == "100/min"
        assert stats["rate_limits"]["critical_endpoints"] == "5/min"
        assert stats["rate_limits"]["hourly_limit"] == "10000/hour"


# ============================================
# EXCLUDED PATHS TESTS
# ============================================

class TestExcludedPaths:
    """Tests para rutas excluidas del rate limiting"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_excluded(self):
        """Test: /health excluido de rate limiting"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        request_mock = Mock(spec=Request)
        request_mock.url.path = "/health"
        request_mock.client.host = "127.0.0.1"
        
        call_next_mock = Mock()
        call_next_mock.return_value = Response(content="OK", status_code=200)
        
        # No debe aplicar rate limiting
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        # call_next debe ser llamado directamente
        call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_root_endpoint_excluded(self):
        """Test: / excluido de rate limiting"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        request_mock = Mock(spec=Request)
        request_mock.url.path = "/"
        request_mock.client.host = "127.0.0.1"
        
        call_next_mock = Mock()
        call_next_mock.return_value = Response(content="OK", status_code=200)
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_excluded(self):
        """Test: /ws/* excluido de rate limiting"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        request_mock = Mock(spec=Request)
        request_mock.url.path = "/ws/alerts"
        request_mock.client.host = "127.0.0.1"
        
        call_next_mock = Mock()
        call_next_mock.return_value = Response(content="OK", status_code=200)
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        call_next_mock.assert_called_once()


# ============================================
# INTEGRATION TESTS
# ============================================

class TestRateLimitIntegration:
    """Tests de integración del rate limiting"""
    
    def test_role_based_limits_hierarchy(self):
        """Test: jerarquía de límites por rol"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        admin_limit = middleware._get_rate_limit_for_role("administrador")
        operario_limit = middleware._get_rate_limit_for_role("operario")
        usuario_limit = middleware._get_rate_limit_for_role("usuario")
        anon_limit = middleware._get_rate_limit_for_role(None)
        
        # Administrador sin límite
        assert admin_limit is None
        
        # Operario > Usuario > Anónimo
        assert operario_limit > usuario_limit
        assert usuario_limit > anon_limit
    
    def test_critical_endpoints_have_strict_limit(self):
        """Test: endpoints críticos tienen límite estricto"""
        app_mock = Mock()
        middleware = RateLimitMiddleware(app_mock)
        
        # Límite crítico debe ser mucho menor que otros límites
        critical_limit = middleware.CRITICAL_ENDPOINTS_LIMIT
        anon_limit = middleware.ROLE_LIMITS["anonymous"]
        
        assert critical_limit < anon_limit
        assert critical_limit == 5  # Muy restrictivo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
