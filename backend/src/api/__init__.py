"""API package initialization."""

from .trading_routes import router as trading_router
from .auth_routes import router as auth_router
from .websocket_routes import router as websocket_router
from .health_routes import router as health_router

__all__ = [
    "trading_router",
    "auth_router", 
    "websocket_router",
    "health_router",
]