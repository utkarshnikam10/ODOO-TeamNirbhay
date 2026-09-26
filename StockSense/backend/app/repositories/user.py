from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.auth import UserRegisterRequest


class UserRepository:
    """Data access repository for User entities."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.lower())
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, user_in: UserRegisterRequest) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email.lower(),
            username=user_in.username.lower(),
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role or "staff",
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_password(db: Session, user: User, new_password_hash: str) -> User:
        user.hashed_password = new_password_hash
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class PasswordResetRepository:
    """Data access repository for OTP and password recovery records."""

    @staticmethod
    def create_otp(
        db: Session, user_id: int, otp_code: str, expires_minutes: int = 15
    ) -> PasswordReset:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_minutes)

        reset_record = PasswordReset(
            user_id=user_id,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(reset_record)
        db.commit()
        db.refresh(reset_record)
        return reset_record

    @staticmethod
    def get_valid_otp(
        db: Session, user_id: int, otp_code: str
    ) -> Optional[PasswordReset]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(PasswordReset)
            .where(
                PasswordReset.user_id == user_id,
                PasswordReset.otp_code == otp_code,
                PasswordReset.is_used == False,  # noqa: E712
                PasswordReset.expires_at > now,
            )
            .order_by(PasswordReset.id.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def mark_as_used(db: Session, reset_record: PasswordReset) -> None:
        reset_record.is_used = True
        db.add(reset_record)
        db.commit()
