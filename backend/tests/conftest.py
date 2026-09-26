from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.main import app


from app.core.database import get_db

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Test client fixture with overridden database session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()



@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Database session fixture that runs within a rolled-back transaction."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()

from app.core.security import create_access_token
from app.models.user import User, Role

@pytest.fixture(scope="function")
def admin_token_headers(db: Session) -> dict:
    admin_user = User(
        email="admin@example.com",
        username="admin",
        hashed_password="hashed_password",
        role=Role.ADMIN
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def normal_user_token_headers(db: Session) -> dict:
    normal_user = User(
        email="user@example.com",
        username="user",
        hashed_password="hashed_password",
        role=Role.STAFF
    )
    db.add(normal_user)
    db.commit()
    db.refresh(normal_user)
    token = create_access_token(normal_user.id)
    return {"Authorization": f"Bearer {token}"}
