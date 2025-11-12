# Backend/examples/structured_logging_usage.py
"""
Ejemplos de uso del sistema de logging estructurado
"""

from app.utils.logging import get_logger, log_with_context

# Ejemplo 1: Logger básico
logger = get_logger(__name__)

def process_sensor_data(sensor_id: str, value: float):
    """Ejemplo de función con logging estructurado"""
    
    # Log simple
    logger.info("Procesando dato de sensor")
    
    # Log con contexto
    logger.info(
        "Dato de sensor procesado",
        sensor_id=sensor_id,
        value=value,
        unit="pH"
    )
    
    # Log con múltiples campos
    logger.info(
        "Validación completada",
        sensor_id=sensor_id,
        value=value,
        is_valid=True,
        validation_time_ms=45
    )


# Ejemplo 2: Logging en manejo de errores
def risky_operation(user_id: str):
    """Ejemplo de logging en manejo de errores"""
    logger = get_logger(__name__)
    
    try:
        # Operación que puede fallar
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error(
            "Error en operación matemática",
            user_id=user_id,
            operation="division",
            exc_info=True,  # Incluye stack trace
            error_type=type(e).__name__
        )


# Ejemplo 3: Logging de métricas de performance
def calculate_metrics(data_points: int):
    """Ejemplo de logging de métricas"""
    logger = get_logger(__name__)
    
    import time
    start = time.time()
    
    # Hacer cálculos...
    time.sleep(0.1)
    
    duration_ms = (time.time() - start) * 1000
    
    logger.info(
        "Métricas calculadas",
        data_points=data_points,
        duration_ms=round(duration_ms, 2),
        throughput=data_points / (duration_ms / 1000)
    )


# Ejemplo 4: Logging de eventos de auditoría
def log_user_action(user_email: str, action: str):
    """Ejemplo de logging de auditoría"""
    logger = get_logger("audit")
    
    logger.info(
        "Acción de usuario",
        user_email=user_email,
        action=action,
        resource_type="alert",
        resource_id="alert_123"
    )


# Ejemplo 5: Helper rápido
def quick_log_example():
    """Ejemplo usando el helper rápido"""
    log_with_context(
        "info",
        "Operación completada exitosamente",
        logger_name="app.services",
        operation="export_data",
        format="excel",
        rows=1500,
        duration_sec=2.3
    )


# Output esperado:
# [app.services.example] [a7b3c9d2] Procesando dato de sensor
# [app.services.example] [a7b3c9d2] Dato de sensor procesado {"sensor_id": "SENSOR_01", "value": 5.3, "unit": "pH"}
# [app.services.example] [a7b3c9d2] Validación completada {"sensor_id": "SENSOR_01", "value": 5.3, "is_valid": true, "validation_time_ms": 45}

if __name__ == "__main__":
    # Demostración
    process_sensor_data("SENSOR_01", 5.3)
    calculate_metrics(1000)
    log_user_action("admin@embalses.cl", "dismiss_alert")
    quick_log_example()
