# app/routes/health.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import asyncio
from typing import Dict, Any
from app.config.database import sensor_collection, users_collection
from app.services.cache import cache_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Variable global para almacenar el tiempo de inicio
start_time = datetime.utcnow()

async def check_mongodb() -> Dict[str, Any]:
    """Verifica la conectividad y latencia de MongoDB"""
    try:
        start = datetime.utcnow()
        # Ping simple a MongoDB
        await sensor_collection.find_one({})
        latency = (datetime.utcnow() - start).total_seconds() * 1000  # en ms
        
        # Contar documentos para verificar acceso
        count = await sensor_collection.count_documents({})
        
        return {
            "status": "up",
            "latency_ms": round(latency, 2),
            "collections_accessible": True,
            "sensor_documents": count
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e)
        }

async def check_disk_space() -> Dict[str, Any]:
    """Verifica el espacio en disco disponible"""
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        percent_used = disk.percent
        
        # Determinar estado
        if percent_used >= 90:
            status = "critical"
        elif percent_used >= 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "percent_used": percent_used
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return {
            "status": "unknown",
            "error": str(e)
        }

async def check_memory() -> Dict[str, Any]:
    """Verifica el uso de memoria RAM"""
    try:
        memory = psutil.virtual_memory()
        
        # Determinar estado
        if memory.percent >= 90:
            status = "critical"
        elif memory.percent >= 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "percent_used": memory.percent,
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "total_gb": round(memory.total / (1024 ** 3), 2)
        }
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return {
            "status": "unknown",
            "error": str(e)
        }

async def check_cpu() -> Dict[str, Any]:
    """Verifica el uso de CPU"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Determinar estado
        if cpu_percent >= 90:
            status = "critical"
        elif cpu_percent >= 75:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "percent_used": cpu_percent,
            "cpu_count": cpu_count
        }
    except Exception as e:
        logger.error(f"CPU check failed: {str(e)}")
        return {
            "status": "unknown",
            "error": str(e)
        }

def get_uptime() -> Dict[str, Any]:
    """Calcula el uptime del servicio"""
    uptime_delta = datetime.utcnow() - start_time
    uptime_seconds = int(uptime_delta.total_seconds())
    
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{days}d {hours}h {minutes}m",
        "started_at": start_time.isoformat()
    }

@router.get("/health")
async def health_check():
    """
    Endpoint de health check completo.
    Verifica el estado de todos los componentes críticos del sistema.
    """
    try:
        # Ejecutar todos los checks en paralelo
        mongodb_check, disk_check, memory_check, cpu_check = await asyncio.gather(
            check_mongodb(),
            check_disk_space(),
            check_memory(),
            check_cpu()
        )
        
        # Obtener estadísticas de caché
        cache_stats = await cache_service.get_stats()
        
        uptime_info = get_uptime()
        
        # Determinar estado general del sistema
        critical_checks = [
            mongodb_check.get("status") == "down",
            disk_check.get("status") == "critical",
            memory_check.get("status") == "critical"
        ]
        
        warning_checks = [
            disk_check.get("status") == "warning",
            memory_check.get("status") == "warning",
            cpu_check.get("status") == "warning"
        ]
        
        if any(critical_checks):
            overall_status = "unhealthy"
        elif any(warning_checks):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": uptime_info,
            "checks": {
                "database": mongodb_check,
                "disk": disk_check,
                "memory": memory_check,
                "cpu": cpu_check,
                "cache": cache_stats
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe para Kubernetes/Docker.
    Verifica si el servicio está listo para recibir tráfico.
    """
    try:
        # Verificar solo MongoDB (componente crítico)
        mongodb_check = await check_mongodb()
        
        if mongodb_check.get("status") == "up":
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=503, detail="Service not ready - Database unavailable")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe para Kubernetes/Docker.
    Verifica si el servicio está vivo (puede ser reiniciado si falla).
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
