# Backend/app/utils/logging.py
"""
Utilidades de logging estructurado con contexto
Mejora la trazabilidad y debugging en producción
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable para request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredLogger:
    """
    Logger estructurado que añade contexto automáticamente a todos los logs
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _build_log_data(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Construye un diccionario estructurado para el log"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": self.name,
            "message": message,
        }
        
        # Añadir request_id si existe en el contexto
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Añadir datos extra
        if extra:
            log_data.update(extra)
        
        # Añadir kwargs
        if kwargs:
            log_data.update(kwargs)
        
        return log_data
    
    def _format_message(self, log_data: Dict[str, Any]) -> str:
        """Formatea el mensaje para logging legible"""
        # Formato legible para desarrollo
        parts = [f"[{log_data.get('logger', 'app')}]"]
        
        if 'request_id' in log_data:
            parts.append(f"[{log_data['request_id'][:8]}]")
        
        parts.append(log_data['message'])
        
        # Añadir campos adicionales
        extra_fields = {k: v for k, v in log_data.items() 
                       if k not in ['timestamp', 'logger', 'message', 'request_id']}
        
        if extra_fields:
            parts.append(json.dumps(extra_fields))
        
        return " ".join(parts)
    
    def info(self, message: str, **kwargs):
        """Log nivel INFO con contexto"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.info(self._format_message(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log nivel WARNING con contexto"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.warning(self._format_message(log_data))
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log nivel ERROR con contexto"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.error(self._format_message(log_data), exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log nivel DEBUG con contexto"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.debug(self._format_message(log_data))
    
    def critical(self, message: str, **kwargs):
        """Log nivel CRITICAL con contexto"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.critical(self._format_message(log_data))


def get_logger(name: str) -> StructuredLogger:
    """
    Factory para obtener un logger estructurado
    
    Usage:
        from app.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Usuario logueado", user_id="123", email="user@example.com")
    """
    return StructuredLogger(name)


class LoggerAdapter:
    """
    Adapter para mantener compatibilidad con logging.Logger estándar
    Permite migración gradual del código existente
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def info(self, msg: str, *args, **kwargs):
        """Compatible con logging.Logger.info()"""
        if args:
            msg = msg % args
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Compatible con logging.Logger.warning()"""
        if args:
            msg = msg % args
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Compatible con logging.Logger.error()"""
        if args:
            msg = msg % args
        exc_info = kwargs.pop('exc_info', False)
        self.logger.error(msg, exc_info=exc_info, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Compatible con logging.Logger.debug()"""
        if args:
            msg = msg % args
        self.logger.debug(msg, **kwargs)


def log_with_context(
    level: str,
    message: str,
    logger_name: str = "app",
    **context
):
    """
    Helper para logging rápido con contexto
    
    Usage:
        log_with_context("info", "Procesando archivo", 
                        filename="data.csv", rows=1000)
    """
    logger = get_logger(logger_name)
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, **context)


# Configuración de formato JSON para producción (opcional)
class JSONFormatter(logging.Formatter):
    """
    Formatter para output JSON en producción
    Útil para sistemas de logging centralizados (ELK, Splunk, etc.)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Añadir request_id si existe
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Añadir exception info si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Añadir campos extra
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


# Ejemplo de uso en producción
def configure_production_logging():
    """
    Configura logging para producción con formato JSON
    Llamar esto en main.py para entornos de producción
    """
    root_logger = logging.getLogger()
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear handler con formato JSON
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
