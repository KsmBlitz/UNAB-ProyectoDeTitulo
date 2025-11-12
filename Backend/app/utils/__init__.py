"""
Utils package
Shared utilities and helper functions
"""

from .dependencies import (
    oauth2_scheme,
    get_current_user,
    get_current_admin_user
)

from .timezone import (
    ensure_timezone_aware,
    utc_now,
    parse_iso_datetime
)

from .logging import (
    get_logger,
    log_with_context,
    StructuredLogger,
    LoggerAdapter
)

__all__ = [
    "oauth2_scheme",
    "get_current_user",
    "get_current_admin_user",
    "ensure_timezone_aware",
    "utc_now",
    "parse_iso_datetime",
    "get_logger",
    "log_with_context",
    "StructuredLogger",
    "LoggerAdapter"
]
