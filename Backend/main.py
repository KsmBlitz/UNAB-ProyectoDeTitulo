import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Database, settings
from app.routes import auth_router, users_router, sensors_router, alerts_router, audit_router
from app.routes.analytics import router as analytics_router
from app.services import alert_change_stream_watcher

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

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando aplicación...")
    logger.info(f"Conectado a base de datos: {settings.DATABASE_NAME}")
    
    # Iniciar el watcher de alertas en background
    asyncio.create_task(alert_change_stream_watcher())
    logger.info("Alert watcher iniciado")
    
    logger.info("Aplicación lista")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando aplicación...")
    await Database.close()
    logger.info("Aplicación cerrada correctamente")

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "Sistema de Monitoreo de Embalses IoT API",
        "version": "2.0.0"
    }

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sensors_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
