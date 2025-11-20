# Backend/app/routes/websocket.py
"""
WebSocket endpoints for real-time updates
Elimina la necesidad de polling en el frontend
"""

import logging
import asyncio
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime, timezone

from app.config import alerts_collection
from app.utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """
    Gestor de conexiones WebSocket
    Maneja múltiples clientes conectados simultáneamente
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Acepta y registra una nueva conexión"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remueve una conexión del registro"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Envía un mensaje a todos los clientes conectados
        Maneja desconexiones automáticamente
        """
        disconnected = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)
        
        # Limpiar conexiones rotas
        if disconnected:
            async with self._lock:
                self.active_connections -= disconnected
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Envía un mensaje a un cliente específico"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)


# Instancia global del gestor de conexiones
manager = ConnectionManager()


@router.websocket("/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para alertas en tiempo real
    
    Flujo:
    1. Cliente se conecta
    2. Recibe estado inicial de alertas
    3. Recibe actualizaciones en tiempo real cuando cambian
    4. Heartbeat cada 30 segundos para mantener conexión
    
    Mensajes enviados:
    - type: "initial" - Estado inicial de alertas
    - type: "update" - Nueva alerta o cambio en alerta existente
    - type: "dismissed" - Alerta cerrada
    - type: "heartbeat" - Keep-alive
    """
    await manager.connect(websocket)
    
    try:
        # Enviar estado inicial
        initial_alerts = await get_active_alerts_summary()
        await websocket.send_json({
            "type": "initial",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": initial_alerts
        })
        
        # Mantener conexión activa y responder a mensajes
        while True:
            try:
                # Recibir mensajes del cliente (con timeout)
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Procesar mensaje del cliente
                await handle_client_message(message, websocket)
                
            except asyncio.TimeoutError:
                # Enviar heartbeat si no hay actividad
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        await manager.disconnect(websocket)


async def handle_client_message(message: str, websocket: WebSocket):
    """
    Procesa mensajes del cliente
    
    Mensajes soportados:
    - {"action": "ping"} - Responde con pong
    - {"action": "refresh"} - Envía estado actual de alertas
    """
    try:
        data = json.loads(message)
        action = data.get("action")
        
        if action == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        elif action == "refresh":
            alerts = await get_active_alerts_summary()
            await websocket.send_json({
                "type": "refresh",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": alerts
            })
        
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown action: {action}"
            })
    
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid JSON"
        })


async def get_active_alerts_summary() -> dict:
    """
    Obtiene resumen de alertas activas
    """
    try:
        # Contar alertas activas por nivel
        pipeline = [
            {"$match": {"is_resolved": {"$ne": True}}},
            {"$group": {
                "_id": "$level",
                "count": {"$sum": 1}
            }}
        ]
        
        results = await alerts_collection.aggregate(pipeline).to_list(length=None)
        
        summary = {
            "total": 0,
            "critical": 0,
            "warning": 0,
            "info": 0
        }
        
        for result in results:
            level = result["_id"]
            count = result["count"]
            summary["total"] += count
            
            if level in ["critical", "crítica", "crítico"]:
                summary["critical"] += count
            elif level in ["warning", "advertencia"]:
                summary["warning"] += count
            elif level in ["info", "información"]:
                summary["info"] += count
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting alerts summary: {e}")
        return {
            "total": 0,
            "critical": 0,
            "warning": 0,
            "info": 0
        }


async def broadcast_alert_update(alert_data: dict):
    """
    Función helper para broadcast de actualizaciones de alertas
    Llamar desde alert_watcher.py cuando se detecte una nueva alerta
    """
    message = {
        "type": "update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": alert_data
    }
    await manager.broadcast(message)


async def broadcast_alert_dismissed(alert_id: str):
    """
    Función helper para broadcast cuando se cierra una alerta
    Llamar desde alerts.py cuando se dismissea una alerta
    """
    message = {
        "type": "dismissed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert_id
    }
    await manager.broadcast(message)


@router.websocket("/sensors")
async def websocket_sensors_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para datos de sensores en tiempo real
    Actualiza cada 10 segundos con las últimas lecturas
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Enviar datos de sensores cada 10 segundos
            from app.routes.sensors import get_latest_metrics
            
            # Simular current_user (en producción, validar token)
            latest_data = await get_latest_metrics(reservoir_id=None, current_user={})
            
            await websocket.send_json({
                "type": "sensor_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": latest_data
            })
            
            await asyncio.sleep(10)
    
    except WebSocketDisconnect:
        logger.info("Sensor WebSocket disconnected")
    except Exception as e:
        logger.error(f"Sensor WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


# Exportar manager para uso en otros módulos
__all__ = ["router", "manager", "broadcast_alert_update", "broadcast_alert_dismissed"]
