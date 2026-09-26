"""API routers package."""

from app.routers import auth, health
from app.routers.api import api_router

__all__ = ["api_router", "auth", "health"]
