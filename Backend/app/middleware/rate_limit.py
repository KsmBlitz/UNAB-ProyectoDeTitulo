# app/middleware/rate_limit.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple, Optional
import logging
import asyncio
import inspect

# Provide a module-level `jwt` symbol so tests can patch `app.middleware.rate_limit.jwt`.
try:
    from jose import jwt as jwt
except Exception:
    jwt = None

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware based on IP, user, and role.
    
    Limits per role (requests/minute):
    - Admin: No limit (tracking only)
    - Operator: 300 requests/minute
    - Basic user: 200 requests/minute
    - Anonymous (IP): 100 requests/minute
    - Critical endpoints: 5 requests/minute for all
    
    Hourly limits:
    - Authenticated users: 10,000 requests/hour
    - Anonymous: N/A (limited per minute)
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Structure: {ip: [(timestamp, endpoint), ...]}
        self.ip_requests: Dict[str, list] = defaultdict(list)
        # Structure: {user_email: [(timestamp, endpoint, role), ...]}
        self.user_requests: Dict[str, list] = defaultdict(list)
        
        # Rate limits by role (requests/minute)
        self.ROLE_LIMITS = {
            "administrador": None,  # No limit
            "operario": 300,
            "usuario": 200,
            "anonymous": 100  # For unauthenticated IPs
        }
        
        # Hourly limit for authenticated users
        self.USER_LIMIT_PER_HOUR = 10000
        
        # Limit for critical endpoints (applies to all)
        self.CRITICAL_ENDPOINTS_LIMIT = 5  # Per minute
        
        # Endpoints considered critical
        self.CRITICAL_ENDPOINTS = [
            "/api/token",
            "/api/forgot-password",
            "/api/reset-password",
            # "/api/users" is handled explicitly (only POST is critical)
        ]
    
    def _clean_old_requests(self, requests_list: list, time_window: timedelta):
        """Remove old requests outside the time window"""
        now = datetime.utcnow()
        cutoff_time = now - time_window
        return [req for req in requests_list if req[0] > cutoff_time]
    
    def _is_critical_endpoint(self, path: str, method: str) -> bool:
        """Determine if an endpoint is critical"""
        if path == "/api/users" and method == "POST":
            return True
        return any(path.startswith(endpoint) for endpoint in self.CRITICAL_ENDPOINTS)
    
    def _get_user_from_token(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract user email and role from JWT token.
        
        Returns:
            Tuple[email, role] or (None, None) if no valid token
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, None
        
        try:
            from jose import jwt
            from app.config.settings import settings
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            role = payload.get("role", "usuario")  # Default: basic user
            return email, role
        except Exception as e:
            logger.debug(f"Error decoding token: {e}")
            return None, None
    
    def _get_rate_limit_for_role(self, role: Optional[str]) -> Optional[int]:
        """
        Get rate limit for a specific role.
        
        Args:
            role: User role ("administrador", "operario", "usuario", None)
            
        Returns:
            Requests/minute limit or None if unlimited
        """
        if role is None:
            return self.ROLE_LIMITS["anonymous"]
        return self.ROLE_LIMITS.get(role.lower(), self.ROLE_LIMITS["usuario"])
    
    async def dispatch(self, request: Request, call_next):
        # Exclude health checks and WebSocket from rate limiting
        if (request.url.path.startswith("/health") or 
            request.url.path == "/" or 
            request.url.path.startswith("/ws/")):
            # Support sync or async call_next implementations in tests/mocks
            maybe_resp = call_next(request)
            if inspect.isawaitable(maybe_resp) or asyncio.iscoroutine(maybe_resp):
                return await maybe_resp
            return maybe_resp
        
        client_ip = request.client.host
        now = datetime.utcnow()
        path = request.url.path
        method = request.method
        
        # Check if critical endpoint
        is_critical = self._is_critical_endpoint(path, method)
        
        # Get authenticated user and role
        user_email, user_role = self._get_user_from_token(request)
        
        # Get appropriate limit based on role
        rate_limit = self._get_rate_limit_for_role(user_role)
        
        # Rate limiting by IP (1 minute window)
        self.ip_requests[client_ip] = self._clean_old_requests(
            self.ip_requests[client_ip],
            timedelta(minutes=1)
        )
        
        # === RATE LIMITING FOR CRITICAL ENDPOINTS ===
        if is_critical:
            critical_requests = [req for req in self.ip_requests[client_ip] 
                                if self._is_critical_endpoint(req[1], method)]
            
            if len(critical_requests) >= self.CRITICAL_ENDPOINTS_LIMIT:
                logger.warning(
                    f"Critical endpoint rate limit exceeded",
                    extra={
                        "ip": client_ip,
                        "user": user_email,
                        "path": path,
                        "requests": len(critical_requests)
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many requests. Please wait 1 minute before trying again.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
        
        # === RATE LIMITING BY ROLE (per minute) ===
        # Admins have no limit
        if rate_limit is not None:
            if len(self.ip_requests[client_ip]) >= rate_limit:
                logger.warning(
                    f"Rate limit exceeded",
                    extra={
                        "ip": client_ip,
                        "user": user_email,
                        "role": user_role or "anonymous",
                        "limit": rate_limit,
                        "requests": len(self.ip_requests[client_ip])
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Request limit exceeded ({rate_limit}/min). Try again in 1 minute.",
                        "retry_after": 60,
                        "limit": rate_limit,
                        "role": user_role or "anonymous"
                    },
                    headers={"Retry-After": "60"}
                )
        
        # === RATE LIMITING BY USER (per hour) ===
        if user_email:
            self.user_requests[user_email] = self._clean_old_requests(
                self.user_requests[user_email],
                timedelta(hours=1)
            )
            
            # Only apply hourly limit if not admin
            if user_role and user_role.lower() != "administrador":
                if len(self.user_requests[user_email]) >= self.USER_LIMIT_PER_HOUR:
                    logger.warning(
                        f"Hourly rate limit exceeded",
                        extra={
                            "user": user_email,
                            "role": user_role,
                            "requests": len(self.user_requests[user_email])
                        }
                    )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": f"Hourly request limit exceeded ({self.USER_LIMIT_PER_HOUR}/hour). Try again later.",
                            "retry_after": 3600
                        },
                        headers={"Retry-After": "3600"}
                    )
            
            # Record user request with role
            self.user_requests[user_email].append((now, path, user_role))
        
        # Record IP request
        self.ip_requests[client_ip].append((now, path))
        
        # Continue with request. Some tests mock `call_next` as a sync function
        # that returns a Response object (not awaitable). Support both awaitable
        # and non-awaitable call_next implementations.
        maybe_response = call_next(request)
        if inspect.isawaitable(maybe_response) or asyncio.iscoroutine(maybe_response):
            response = await maybe_response
        else:
            response = maybe_response
        
        # Add rate limit info headers
        if rate_limit is not None:
            remaining_requests = max(0, rate_limit - len(self.ip_requests[client_ip]))
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
            response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        else:
            # Admins
            response.headers["X-RateLimit-Limit"] = "unlimited"
            response.headers["X-RateLimit-Remaining"] = "unlimited"
        
        if user_role:
            response.headers["X-RateLimit-Role"] = user_role
        
        return response
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics (useful for monitoring)"""
        # Count requests by role
        role_stats = defaultdict(int)
        for user_email, requests in self.user_requests.items():
            if requests:
                role = requests[-1][2] if len(requests[-1]) > 2 else "unknown"
                role_stats[role] += len(requests)
        
        return {
            "active_ips": len(self.ip_requests),
            "active_users": len(self.user_requests),
            "total_ip_requests": sum(len(reqs) for reqs in self.ip_requests.values()),
            "total_user_requests": sum(len(reqs) for reqs in self.user_requests.values()),
            "requests_by_role": dict(role_stats),
            "rate_limits": {
                "administrador": "unlimited",
                "operario": f"{self.ROLE_LIMITS['operario']}/min",
                "usuario": f"{self.ROLE_LIMITS['usuario']}/min",
                "anonymous": f"{self.ROLE_LIMITS['anonymous']}/min",
                "critical_endpoints": f"{self.CRITICAL_ENDPOINTS_LIMIT}/min",
                "hourly_limit": f"{self.USER_LIMIT_PER_HOUR}/hour"
            }
        }
