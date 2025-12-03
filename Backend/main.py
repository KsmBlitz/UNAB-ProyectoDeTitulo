import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import Database, settings
from app.routes import auth_router, users_router, sensors_router, alerts_router, audit_router
from app.routes.analytics import router as analytics_router
from app.routes.health import router as health_router
from app.routes.websocket import router as websocket_router
from app.services import alert_change_stream_watcher
from app.services.alert_reconciler import start_reconciler
from app.services.sensor_monitor import sensor_monitor
from app.services.cache import cache_service
from app.middleware import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.utils.dependencies import get_current_user
from app.core import register_exception_handlers, get_container, configure_container

# Configure logging level based on environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting application...")
    
    # Configure dependency injection container
    container = get_container()
    configure_container(container)
    logger.info("Dependency container configured")
    
    logger.info(f"Connected to database: {settings.DATABASE_NAME}")
    
    # Connect Redis cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    await cache_service.connect(redis_url)
    
    # Start alert watcher in background
    asyncio.create_task(alert_change_stream_watcher())
    logger.info("Alert watcher started")
    
    # Start alert reconciler
    asyncio.create_task(start_reconciler(60))
    logger.info("Alert reconciler started (interval 60s)")

    # Start sensor monitor in background
    asyncio.create_task(sensor_monitor.start())
    logger.info("Sensor monitor started")
    
    logger.info("Application ready")
    
    yield  # Application is running
    
    # Shutdown
    logger.info("Shutting down application...")
    sensor_monitor.stop()
    await cache_service.disconnect()
    await Database.close()
    logger.info("Application closed successfully")


app = FastAPI(
    title="AquaStat IoT Monitoring System",
    description="API for real-time IoT sensor monitoring in reservoirs",
    version="2.1.0",
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware (must come before other middlewares)
app.add_middleware(RequestIDMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "AquaStat IoT Monitoring System API",
        "version": "2.1.0"
    }

@app.get("/api/rate-limit/stats", tags=["Monitoring"])
async def get_rate_limit_stats(current_user: dict = Depends(get_current_user)):
    """
    Get rate limiting statistics (admin only).
    
    Requires authentication and admin role.
    """
    from fastapi import HTTPException, status
    
    # Verify admin role
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view rate limiting statistics"
        )
    
    # Get rate limiting middleware instance
    rate_limit_instance = None
    for middleware in app.user_middleware:
        if middleware.cls == RateLimitMiddleware:
            # Middleware is a wrapped instance, need to access original app
            rate_limit_instance = middleware.kwargs.get("app")
            break
    
    if rate_limit_instance:
        # Search for actual middleware instance in chain
        for mw in app.middleware_stack.__self__.middleware:
            if isinstance(mw, RateLimitMiddleware):
                return mw.get_stats()
    
    # Fallback: return basic response
    return {
        "message": "Rate limiting active but stats unavailable",
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
