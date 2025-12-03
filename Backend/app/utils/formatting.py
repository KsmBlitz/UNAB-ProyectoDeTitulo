"""
Formatting utilities
Common text and value formatting functions used across services
"""

import re
from typing import Union


def format_disconnect_duration(value: Union[str, int, float]) -> str:
    """
    Format disconnect duration from minutes to human-readable format.
    
    Args:
        value: Duration value - can be:
            - Integer/float minutes
            - String containing minutes (e.g., "15 minutos" or "15")
        
    Returns:
        Formatted duration string in Spanish (e.g., "15 minutos", "1 hora 30 minutos")
        
    Examples:
        >>> format_disconnect_duration(15)
        '15 minutos'
        >>> format_disconnect_duration(90)
        '1 hora 30 minutos'
        >>> format_disconnect_duration("45 minutos")
        '45 minutos'
    """
    try:
        # Extract number from string if needed
        if isinstance(value, str):
            match = re.search(r'(\d+)', value)
            if not match:
                return str(value)
            minutes = int(match.group(1))
        else:
            minutes = int(value)
        
        if minutes < 60:
            return f"{minutes} minuto{'s' if minutes != 1 else ''}"
        
        hours = minutes // 60
        remaining_mins = minutes % 60
        
        if remaining_mins == 0:
            return f"{hours} hora{'s' if hours != 1 else ''}"
        
        return f"{hours} hora{'s' if hours != 1 else ''} {remaining_mins} minuto{'s' if remaining_mins != 1 else ''}"
        
    except (ValueError, TypeError):
        return str(value)


# Alert type configuration - centralized to avoid duplication
ALERT_CONFIG = {
    'ph_range': {'name': 'pH Fuera de Rango', 'icon': '⚗️', 'color': '#ff6b6b'},
    'ph': {'name': 'pH Fuera de Rango', 'icon': '⚗️', 'color': '#ff6b6b'},
    'conductivity': {'name': 'Conductividad Anormal', 'icon': '⚡', 'color': '#feca57'},
    'ec': {'name': 'Conductividad Eléctrica Anormal', 'icon': '⚡', 'color': '#feca57'},
    'temperature': {'name': 'Temperatura Crítica', 'icon': '🌡️', 'color': '#ff9f43'},
    'water_level': {'name': 'Nivel de Agua Crítico', 'icon': '💧', 'color': '#54a0ff'},
    'sensor_disconnection': {'name': 'Sensor Desconectado', 'icon': '🔌', 'color': '#636e72'}
}


def get_alert_display_config(alert_type: str) -> dict:
    """
    Get display configuration for an alert type.
    
    Args:
        alert_type: Alert type identifier
        
    Returns:
        Dict with 'name', 'icon', and 'color' keys
    """
    return ALERT_CONFIG.get(alert_type, {
        'name': alert_type,
        'icon': '⚠️',
        'color': '#dc3545'
    })
