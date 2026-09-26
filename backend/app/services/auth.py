from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_otp_code,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import PasswordResetRepository, UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.notification import notification_service


class AuthService:
    """Business logic for user authentication, registration, and password recovery."""

    @staticmethod
    def register(db: Session, user_in: UserRegisterRequest) -> User:
        """Register a new user account with duplicate prevention."""
        # 1. Check duplicate email
        existing_email = UserRepository.get_by_email(db, user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with email '{user_in.email}' already exists.",
            )

        # 2. Check duplicate username
        existing_username = UserRepository.get_by_username(db, user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_in.username}' is already taken.",
            )

        # 3. Create user
        return UserRepository.create(db, user_in)

    @staticmethod
    def authenticate(db: Session, login_in: UserLoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue signed JWT access token."""
        user = UserRepository.get_by_email(db, login_in.email)
        if not user or not verify_password(login_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        # Generate JWT
        token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.role},
        )
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
        )

    @staticmethod
    def forgot_password(
        db: Session, req: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        """Generate and dispatch a temporary OTP for password reset."""
        user = UserRepository.get_by_email(db, req.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No registered account found with email '{req.email}'.",
            )

        # Generate OTP
        otp_code = generate_otp_code(6)

        # Store in database
        PasswordResetRepository.create_otp(
            db,
            user_id=user.id,
            otp_code=otp_code,
            expires_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
        )

        # Send via notification service
        notification_service.send_password_reset_otp(email=user.email, otp_code=otp_code)

        return ForgotPasswordResponse(
            message="Verification OTP has been sent to your email address.",
            email=user.email,
            expires_in_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
            otp_code=otp_code if settings.DEBUG else None,
        )

    @staticmethod
    def reset_password(
        db: Session, req: ResetPasswordRequest
    ) -> MessageResponse:
        """Verify OTP and update user's password."""
        user = UserRepository.get_by_email(db, req.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No account found with email '{req.email}'.",
            )

        reset_record = PasswordResetRepository.get_valid_otp(
            db, user_id=user.id, otp_code=req.otp_code
        )
        if not reset_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification OTP code.",
            )

        # Update password
        new_hashed = get_password_hash(req.new_password)
        UserRepository.update_password(db, user, new_hashed)

        # Mark OTP as consumed
        PasswordResetRepository.mark_as_used(db, reset_record)

        return MessageResponse(message="Password has been successfully reset.")
