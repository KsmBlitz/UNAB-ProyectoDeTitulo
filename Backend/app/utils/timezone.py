"""
Timezone utilities
Helper functions for consistent timezone handling
"""

from datetime import datetime, timezone


def ensure_timezone_aware(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware (UTC)
    
    Args:
        dt: datetime to check/convert
        
    Returns:
        timezone-aware datetime (UTC)
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    
    return dt


def utc_now() -> datetime:
    """
    Get current UTC time (timezone-aware)
    
    Returns:
        Current datetime in UTC with timezone info
    """
    return datetime.now(timezone.utc)


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO format datetime string and ensure it's timezone-aware
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        timezone-aware datetime (UTC)
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return ensure_timezone_aware(dt)
    except Exception:
        # Fallback to current time if parsing fails
        return utc_now()
