import logging
import asyncio
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import Database, settings
from app.routes import auth_router, users_router, sensors_router, alerts_router, audit_router
from app.routes.analytics import router as analytics_router
from app.routes.health import router as health_router
from app.routes.websocket import router as websocket_router
from app.services import alert_change_stream_watcher
from app.services.cache import cache_service
from app.middleware import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.utils.dependencies import get_current_user

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Monitoreo de Embalses IoT",
    description="API para monitoreo en tiempo real de sensores IoT en embalses",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware (debe ir antes que otros middlewares)
app.add_middleware(RequestIDMiddleware)

# Rate limiting middleware
rate_limit_middleware = None
for middleware in app.user_middleware:
    if middleware.cls == RateLimitMiddleware:
        rate_limit_middleware = middleware
        break

# Si no se encontró, agregarlo
if not rate_limit_middleware:
    app.add_middleware(RateLimitMiddleware)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando aplicación...")
    logger.info(f"Conectado a base de datos: {settings.DATABASE_NAME}")
    
    # Conectar Redis cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    await cache_service.connect(redis_url)
    
    # Iniciar el watcher de alertas en background
    asyncio.create_task(alert_change_stream_watcher())
    logger.info("Alert watcher iniciado")
    
    logger.info("Aplicación lista")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando aplicación...")
    await cache_service.disconnect()
    await Database.close()
    logger.info("Aplicación cerrada correctamente")

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "Sistema de Monitoreo de Embalses IoT API",
        "version": "2.0.0"
    }

@app.get("/api/rate-limit/stats", tags=["Monitoring"])
async def get_rate_limit_stats(current_user: dict = Depends(get_current_user)):
    """
    Obtiene estadísticas del rate limiting (solo para administradores).
    
    Requiere autenticación y rol de administrador.
    """
    from fastapi import HTTPException, status
    
    # Verificar que sea administrador
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver estadísticas de rate limiting"
        )
    
    # Obtener el middleware de rate limiting
    rate_limit_instance = None
    for middleware in app.user_middleware:
        if middleware.cls == RateLimitMiddleware:
            # El middleware es una instancia envuelta, necesitamos acceder al app original
            rate_limit_instance = middleware.kwargs.get("app")
            break
    
    if rate_limit_instance:
        # Buscar la instancia real del middleware en la cadena
        for mw in app.middleware_stack.__self__.middleware:
            if isinstance(mw, RateLimitMiddleware):
                return mw.get_stats()
    
    # Fallback: crear respuesta básica
    return {
        "message": "Rate limiting activo pero sin estadísticas disponibles",
        "active_ips": 0,
        "active_users": 0
    }

# Register routers
app.include_router(health_router, tags=["Health"])
app.include_router(websocket_router)  # WebSocket routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sensors_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
