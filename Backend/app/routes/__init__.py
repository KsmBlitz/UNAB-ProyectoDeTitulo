"""
Routes package
API endpoint routers
"""

from .auth import router as auth_router
from .users import router as users_router
from .sensors import router as sensors_router
from .alerts import router as alerts_router

__all__ = [
    "auth_router",
    "users_router",
    "sensors_router",
    "alerts_router"
]
