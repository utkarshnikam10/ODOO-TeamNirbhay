from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="Valid user email address", examples=["user@example.com"])
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username containing letters, numbers, hyphens, or underscores",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plain text password (minimum 8 characters)",
        examples=["SecretPass123!"],
    )
    full_name: Optional[str] = Field(None, max_length=255, examples=["John Doe"])
    role: Optional[str] = Field("staff", pattern=r"^(admin|manager|staff)$", examples=["staff"])


class UserLoginRequest(BaseModel):
    """Schema for user authentication credentials."""

    email: EmailStr = Field(..., description="Registered email address", examples=["user@example.com"])
    password: str = Field(..., min_length=1, description="Account password", examples=["SecretPass123!"])


class TokenResponse(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifespan in seconds")


class UserResponse(BaseModel):
    """Public user profile schema (never exposes password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset OTP code."""

    email: EmailStr = Field(..., description="Registered user email", examples=["user@example.com"])


class ForgotPasswordResponse(BaseModel):
    """Response returned when an OTP has been generated."""

    message: str
    email: EmailStr
    expires_in_minutes: int
    # Optional debug otp code provided for development/testing
    otp_code: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Schema for submitting an OTP code to set a new password."""

    email: EmailStr = Field(..., description="User email", examples=["user@example.com"])
    otp_code: str = Field(
        ..., min_length=4, max_length=10, description="Verification OTP code received", examples=["123456"]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New secure password",
        examples=["NewSecurePassword123!"],
    )


class MessageResponse(BaseModel):
    """Standard message response."""

    message: str
