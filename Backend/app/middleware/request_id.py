# Backend/app/middleware/request_id.py
"""
Middleware for adding unique Request ID to each request
Useful for traceability and debugging
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logging import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique Request ID to each request
    The Request ID is propagated through:
    1. Response header: X-Request-ID
    2. Context variable for structured logging
    3. Logs automatically (via StructuredLogger)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Save in context var for logging
        token = request_id_var.set(request_id)
        
        try:
            # Process request
            response: Response = await call_next(request)
            
            # Add Request ID to response header
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            # Clean context var
            request_id_var.reset(token)
