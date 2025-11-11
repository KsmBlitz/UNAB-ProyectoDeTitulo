# app/middleware/rate_limit.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para rate limiting basado en IP y usuario.
    
    Límites:
    - 100 requests/minuto por IP (anónimo)
    - 1000 requests/hora por usuario autenticado
    - 5 requests/minuto para endpoints críticos (reset password, login)
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Estructura: {ip: [(timestamp, endpoint), ...]}
        self.ip_requests: Dict[str, list] = defaultdict(list)
        # Estructura: {user_email: [(timestamp, endpoint), ...]}
        self.user_requests: Dict[str, list] = defaultdict(list)
        
        # Configuración de límites
        self.IP_LIMIT_PER_MINUTE = 300  # Aumentado de 100 a 300
        self.USER_LIMIT_PER_HOUR = 5000  # Aumentado de 1000 a 5000
        self.AUTHENTICATED_USER_LIMIT_PER_MINUTE = 200  # Nuevo límite por minuto para usuarios autenticados
        self.CRITICAL_ENDPOINTS_LIMIT = 5  # Por minuto
        
        # Endpoints considerados críticos
        self.CRITICAL_ENDPOINTS = [
            "/api/token",
            "/api/forgot-password",
            "/api/reset-password",
            "/api/users"  # Solo POST
        ]
    
    def _clean_old_requests(self, requests_list: list, time_window: timedelta):
        """Elimina requests antiguos fuera de la ventana de tiempo"""
        now = datetime.utcnow()
        cutoff_time = now - time_window
        return [req for req in requests_list if req[0] > cutoff_time]
    
    def _is_critical_endpoint(self, path: str, method: str) -> bool:
        """Determina si un endpoint es crítico"""
        if path == "/api/users" and method == "POST":
            return True
        return any(path.startswith(endpoint) for endpoint in self.CRITICAL_ENDPOINTS)
    
    def _get_user_from_token(self, request: Request) -> str | None:
        """Extrae el email del usuario del token JWT"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        try:
            from jose import jwt
            from app.config.settings import settings
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub")  # email del usuario
        except Exception:
            return None
    
    async def dispatch(self, request: Request, call_next):
        # Excluir health checks del rate limiting
        if request.url.path.startswith("/health") or request.url.path == "/":
            return await call_next(request)
        
        client_ip = request.client.host
        now = datetime.utcnow()
        path = request.url.path
        method = request.method
        
        # Verificar si es endpoint crítico
        is_critical = self._is_critical_endpoint(path, method)
        
        # Obtener usuario autenticado (si existe)
        user_email = self._get_user_from_token(request)
        
        # Rate limiting por IP (ventana de 1 minuto)
        self.ip_requests[client_ip] = self._clean_old_requests(
            self.ip_requests[client_ip],
            timedelta(minutes=1)
        )
        
        if is_critical:
            # Límite estricto para endpoints críticos
            critical_requests = [req for req in self.ip_requests[client_ip] 
                                if self._is_critical_endpoint(req[1], method)]
            
            if len(critical_requests) >= self.CRITICAL_ENDPOINTS_LIMIT:
                logger.warning(f"Rate limit exceeded for critical endpoint by IP: {client_ip} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Demasiadas solicitudes. Por favor, espera 1 minuto antes de intentar nuevamente.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
        else:
            # Para usuarios autenticados, usar límite más permisivo
            if user_email:
                ip_limit = self.AUTHENTICATED_USER_LIMIT_PER_MINUTE
            else:
                ip_limit = self.IP_LIMIT_PER_MINUTE
                
            if len(self.ip_requests[client_ip]) >= ip_limit:
                logger.warning(f"Rate limit exceeded by IP: {client_ip} (authenticated: {user_email is not None})")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Límite de solicitudes excedido. Intenta nuevamente en 1 minuto.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
        
        # Rate limiting por usuario autenticado (ventana de 1 hora)
        if user_email:
            self.user_requests[user_email] = self._clean_old_requests(
                self.user_requests[user_email],
                timedelta(hours=1)
            )
            
            if len(self.user_requests[user_email]) >= self.USER_LIMIT_PER_HOUR:
                logger.warning(f"Rate limit exceeded by user: {user_email}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Límite de solicitudes por hora excedido. Intenta nuevamente más tarde.",
                        "retry_after": 3600
                    },
                    headers={"Retry-After": "3600"}
                )
            
            # Registrar request del usuario
            self.user_requests[user_email].append((now, path))
        
        # Registrar request de la IP
        self.ip_requests[client_ip].append((now, path))
        
        # Continuar con la solicitud
        response = await call_next(request)
        
        # Agregar headers de rate limit info
        # Usar el límite apropiado según si está autenticado
        current_limit = self.AUTHENTICATED_USER_LIMIT_PER_MINUTE if user_email else self.IP_LIMIT_PER_MINUTE
        remaining_requests = current_limit - len(self.ip_requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(current_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining_requests))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        return response
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del rate limiting (útil para monitoring)"""
        return {
            "active_ips": len(self.ip_requests),
            "active_users": len(self.user_requests),
            "total_ip_requests": sum(len(reqs) for reqs in self.ip_requests.values()),
            "total_user_requests": sum(len(reqs) for reqs in self.user_requests.values())
        }
