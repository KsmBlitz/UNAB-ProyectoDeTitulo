#!/usr/bin/env python3
"""
Script para crear índices optimizados en MongoDB
Ejecutar: python scripts/create_indexes.py
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_indexes():
    """Crear todos los índices necesarios para optimizar queries"""
    
    # Conectar a MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    logger.info(f"Conectado a base de datos: {settings.DATABASE_NAME}")
    
    # ============================================
    # COLECCIÓN: Sensor_Data
    # ============================================
    sensor_collection = db["Sensor_Data"]
    
    logger.info("Creando índices para Sensor_Data...")
    
    # Índice compuesto para queries por reservoir y tiempo (más usado)
    await sensor_collection.create_index(
        [("reservoirId", 1), ("ReadTime", -1)],
        name="idx_reservoir_time",
        background=True
    )
    logger.info("[OK] Índice creado: idx_reservoir_time")
    
    # Índice para consultas solo por tiempo
    await sensor_collection.create_index(
        [("ReadTime", -1)],
        name="idx_time",
        background=True
    )
    logger.info("[OK] Índice creado: idx_time")
    
    # Índice para timestamp alternativo
    await sensor_collection.create_index(
        [("timestamp", -1)],
        name="idx_timestamp",
        background=True,
        sparse=True  # Solo documentos con timestamp
    )
    logger.info("[OK] Índice creado: idx_timestamp")
    
    # ============================================
    # COLECCIÓN: alerts
    # ============================================
    alerts_collection = db["alerts"]
    
    logger.info("Creando índices para alerts...")
    
    # Índice compuesto para alertas activas (query más frecuente)
    await alerts_collection.create_index(
        [("is_resolved", 1), ("level", 1), ("created_at", -1)],
        name="idx_active_alerts",
        background=True
    )
    logger.info("[OK] Índice creado: idx_active_alerts")
    
    # Índice para búsqueda por tipo y sensor
    await alerts_collection.create_index(
        [("type", 1), ("sensor_id", 1), ("is_resolved", 1)],
        name="idx_type_sensor",
        background=True
    )
    logger.info("[OK] Índice creado: idx_type_sensor")
    
    # Índice para búsqueda por fecha de creación
    await alerts_collection.create_index(
        [("created_at", -1)],
        name="idx_created_at",
        background=True
    )
    logger.info("[OK] Índice creado: idx_created_at")
    
    # ============================================
    # COLECCIÓN: alert_history
    # ============================================
    alert_history_collection = db["alert_history"]
    
    logger.info("Creando índices para alert_history...")
    
    # Índice para búsqueda por fecha de creación (ordenamiento común)
    await alert_history_collection.create_index(
        [("created_at", -1)],
        name="idx_history_created",
        background=True
    )
    logger.info("[OK] Índice creado: idx_history_created")
    
    # Índice para búsqueda por tipo y nivel
    await alert_history_collection.create_index(
        [("type", 1), ("level", 1), ("created_at", -1)],
        name="idx_history_type_level",
        background=True
    )
    logger.info("[OK] Índice creado: idx_history_type_level")
    
    # Índice para búsqueda por usuario que cerró la alerta
    await alert_history_collection.create_index(
        [("dismissed_by", 1), ("dismissed_at", -1)],
        name="idx_dismissed_by",
        background=True,
        sparse=True
    )
    logger.info("[OK] Índice creado: idx_dismissed_by")
    
    # ============================================
    # COLECCIÓN: users
    # ============================================
    users_collection = db["users"]
    
    logger.info("Creando índices para users...")
    
    # Índice único para email (ya debería existir, pero aseguramos)
    await users_collection.create_index(
        [("email", 1)],
        name="idx_email_unique",
        unique=True,
        background=True
    )
    logger.info("[OK] Índice creado: idx_email_unique")
    
    # Índice para búsqueda por rol y estado
    await users_collection.create_index(
        [("role", 1), ("disabled", 1)],
        name="idx_role_status",
        background=True
    )
    logger.info("[OK] Índice creado: idx_role_status")
    
    # ============================================
    # COLECCIÓN: audit_log
    # ============================================
    audit_collection = db["audit_log"]
    
    logger.info("Creando índices para audit_log...")
    
    # Índice compuesto para búsqueda por usuario y fecha
    await audit_collection.create_index(
        [("user_email", 1), ("timestamp", -1)],
        name="idx_user_audit",
        background=True
    )
    logger.info("[OK] Índice creado: idx_user_audit")
    
    # Índice para búsqueda por acción
    await audit_collection.create_index(
        [("action", 1), ("timestamp", -1)],
        name="idx_action_time",
        background=True
    )
    logger.info("[OK] Índice creado: idx_action_time")
    
    # Índice para búsqueda por timestamp (limpieza de logs antiguos)
    await audit_collection.create_index(
        [("timestamp", -1)],
        name="idx_audit_timestamp",
        background=True
    )
    logger.info("[OK] Índice creado: idx_audit_timestamp")
    
    # Índice TTL para auto-eliminar logs después de 180 días (opcional)
    await audit_collection.create_index(
        [("timestamp", 1)],
        name="idx_audit_ttl",
        expireAfterSeconds=15552000,  # 180 días
        background=True
    )
    logger.info("[OK] Índice TTL creado: idx_audit_ttl (180 días)")
    
    # ============================================
    # COLECCIÓN: notifications_sent
    # ============================================
    notifications_collection = db["notifications_sent"]
    
    logger.info("Creando índices para notifications_sent...")
    
    # Índice para búsqueda por last_sent (throttling)
    await notifications_collection.create_index(
        [("last_sent", -1)],
        name="idx_last_sent",
        background=True
    )
    logger.info("[OK] Índice creado: idx_last_sent")
    
    # Índice TTL para limpiar notificaciones antiguas (7 días)
    await notifications_collection.create_index(
        [("last_sent", 1)],
        name="idx_notifications_ttl",
        expireAfterSeconds=604800,  # 7 días
        background=True
    )
    logger.info("[OK] Índice TTL creado: idx_notifications_ttl (7 días)")
    
    # ============================================
    # RESUMEN
    # ============================================
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE ÍNDICES CREADOS")
    logger.info("="*60)
    
    collections = [
        ("Sensor_Data", sensor_collection),
        ("alerts", alerts_collection),
        ("alert_history", alert_history_collection),
        ("users", users_collection),
        ("audit_log", audit_collection),
        ("notifications_sent", notifications_collection)
    ]
    
    for name, collection in collections:
        indexes = await collection.index_information()
        logger.info(f"\n{name}: {len(indexes)} índices totales")
        for idx_name in indexes.keys():
            if idx_name != "_id_":  # Omitir el índice por defecto
                logger.info(f"  - {idx_name}")
    
    logger.info("\n" + "="*60)
    logger.info("[SUCCESS] Todos los índices creados exitosamente")
    logger.info("="*60)
    
    # Cerrar conexión
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
