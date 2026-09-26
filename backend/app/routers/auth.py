from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with unique email and username validation.",
)
def register(
    user_in: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    """Create a new user account."""
    return AuthService.register(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate with email and password to receive a JWT bearer token.",
)
def login(
    login_in: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials and return JWT access token."""
    return AuthService.authenticate(db=db, login_in=login_in)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset OTP",
    description="Generate a secure temporary OTP code for password recovery.",
)
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Send a password recovery verification OTP."""
    return AuthService.forgot_password(db=db, req=req)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with OTP",
    description="Verify the OTP code and set a new password for the user account.",
)
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Reset account password using verified OTP code."""
    return AuthService.reset_password(db=db, req=req)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the profile of the currently authenticated user via JWT bearer token.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return profile of the authenticated user."""
    return current_user
