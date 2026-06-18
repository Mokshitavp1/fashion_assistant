"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    def name_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v.strip()) > 100:
            raise ValueError("Name must be less than 100 characters")
        return v.strip()

    @field_validator("password")
    def password_strength(cls, v: str) -> str:
        from auth_utils import validate_password

        validate_password(v)
        return v

    @field_validator("email")
    def gmail_only(cls, v: EmailStr) -> str:
        import re

        email = str(v).strip().lower()
        gmail_pattern = r"^[a-z0-9](?:[a-z0-9._%+-]{0,61}[a-z0-9])?@gmail\.com$"
        if not re.match(gmail_pattern, email):
            raise ValueError("Email not valid. Please use a real Gmail address.")
        if ".." in email.split("@", 1)[0]:
            raise ValueError("Email not valid. Please use a real Gmail address.")
        return email


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str

    @field_validator("password")
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password is required")
        return v


class UserAnalyze(BaseModel):
    """Schema for user profile analysis (height, weight)."""

    height: float
    weight: float

    @field_validator("height", "weight")
    def validate_measurements(cls, v: float) -> float:
        if v <= 0 or v > 300:
            raise ValueError("Measurements must be between 0 and 300")
        return v


class WardrobeItemCreate(BaseModel):
    """Schema for adding a wardrobe item."""

    category: str
    season: Optional[str] = None

    @field_validator("category")
    def category_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Category is required")
        if len(v.strip()) > 50:
            raise ValueError("Category must be less than 50 characters")
        return v.strip()

    @field_validator("season")
    def validate_season(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) > 50:
            raise ValueError("Season must be less than 50 characters")
        return v


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    access_token_expires_in: int


class RegisterResponse(BaseModel):
    """Schema for registration response."""

    detail: str
    email_verification_required: bool = True
    email: str
    verification_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str

    @field_validator("refresh_token")
    def refresh_token_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("refresh_token is required")
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    reset_token: str
    new_password: str

    @field_validator("reset_token")
    def reset_token_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("reset_token is required")
        return v

    @field_validator("new_password")
    def new_password_strength(cls, v: str) -> str:
        from auth_utils import validate_password

        validate_password(v)
        return v


class PasswordResetRequestResponse(BaseModel):
    """Schema for password reset request response."""

    detail: str
    reset_token: Optional[str] = None


class EmailVerificationRequest(BaseModel):
    """Schema for email verification."""

    verification_token: str

    @field_validator("verification_token")
    def verification_token_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("verification_token is required")
        return v


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""

    email: EmailStr


class EmailVerificationResponse(BaseModel):
    """Schema for email verification response."""

    detail: str
    email_verification_required: bool = True
    email: Optional[str] = None
    verification_token: Optional[str] = None


class AuthSessionInfo(BaseModel):
    """Schema for active authentication session."""

    jti: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool


class AuthSessionsResponse(BaseModel):
    """Schema for listing all sessions."""

    total_sessions: int
    active_sessions: int
    sessions: list[AuthSessionInfo]


class LogoutAllResponse(BaseModel):
    """Schema for logout all sessions response."""

    detail: str
    revoked_sessions: int
