"""Core configuration, settings, security, and database session components."""

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.core.dependencies import (
    get_current_user,
    require_admin,
    require_manager_or_admin,
    require_roles,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_otp_code,
    get_password_hash,
    verify_password,
)

__all__ = [
    "settings",
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "generate_otp_code",
    "get_current_user",
    "require_roles",
    "require_admin",
    "require_manager_or_admin",
]
