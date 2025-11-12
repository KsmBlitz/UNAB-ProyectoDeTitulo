# Backend/app/middleware/request_id.py
"""
Middleware para agregar Request ID único a cada request
Útil para trazabilidad y debugging
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logging import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade un Request ID único a cada petición
    El Request ID se propaga a través de:
    1. Header de respuesta: X-Request-ID
    2. Context variable para logging estructurado
    3. Logs automáticamente (via StructuredLogger)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generar o extraer Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Guardar en context var para logging
        token = request_id_var.set(request_id)
        
        try:
            # Procesar request
            response: Response = await call_next(request)
            
            # Añadir Request ID al header de respuesta
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            # Limpiar context var
            request_id_var.reset(token)
