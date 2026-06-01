"""Authentication utilities and helper functions."""

import hashlib
import hmac
import logging
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any, Dict, Optional, Tuple

import jwt
from sqlalchemy.orm import Session

from config import (
    ALGORITHM,
    EMAIL_VERIFICATION_EXPIRATION_HOURS,
    IS_DEV_ENV,
    PBKDF2_ITERATIONS,
    PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES,
    ACCESS_TOKEN_EXPIRATION_MINUTES,
    REFRESH_TOKEN_EXPIRATION_DAYS,
    SECRET_KEY,
    SMTP_FROM_ADDRESS,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)
from database import crud
from utils import utcnow

logger = logging.getLogger(__name__)


def validate_password(password: str) -> None:
    """Validate password meets security requirements.
    
    Args:
        password: Password string to validate
        
    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be less than 129 characters")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")


def hash_password(password: str) -> str:
    """Hash password using PBKDF2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password in format: pbkdf2_sha256$iterations$salt$hash
    """
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    password_hash = derived_key.hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash.
    
    Args:
        password: Plain text password to verify
        stored_hash: Stored PBKDF2 hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        algorithm, iterations, salt, password_hash = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(derived_key.hex(), password_hash)
    except (ValueError, TypeError):
        return False


def create_email_verification_token() -> Tuple[str, str, datetime]:
    """Create email verification token.
    
    Returns:
        Tuple of (raw_token, token_hash, expires_at)
    """
    raw_token = f"{secrets.randbelow(1_000_000):06d}"
    token_hash = hmac.new(
        SECRET_KEY.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expires_at = utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRATION_HOURS)
    return raw_token, token_hash, expires_at


def hash_email_verification_token(token: str) -> str:
    """Hash email verification token.
    
    Args:
        token: Raw verification token
        
    Returns:
        Hashed token
    """
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        token.strip().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def send_verification_code_email(recipient_email: str, verification_code: str) -> None:
    """Send verification code email.
    
    Args:
        recipient_email: Recipient email address
        verification_code: Verification code to send
        
    Raises:
        RuntimeError: If SMTP credentials not configured in production
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        if IS_DEV_ENV:
            logger.info(
                "DEV_EMAIL_VERIFICATION recipient=%s code=%s",
                recipient_email,
                verification_code,
            )
            return
        raise RuntimeError("SMTP credentials are required to send verification emails")

    message = EmailMessage()
    message["Subject"] = "Your Fashion App confirmation code"
    message["From"] = SMTP_FROM_ADDRESS or SMTP_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"""Your confirmation code is below.

Confirmation code: {verification_code}

This code expires in {EMAIL_VERIFICATION_EXPIRATION_HOURS} hours.
If you did not request this, you can ignore this email.
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


def create_token(user_id: int, token_type: str, expires_delta: timedelta) -> Dict[str, Any]:
    """Create JWT token payload.
    
    Args:
        user_id: User ID
        token_type: Type of token ('access', 'refresh', 'password_reset')
        expires_delta: Token expiration delta
        
    Returns:
        Token payload dictionary
    """
    now = utcnow()
    expire = now + expires_delta
    return {
        "sub": str(user_id),
        "user_id": user_id,
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }


def encode_token(payload: Dict[str, Any]) -> str:
    """Encode token payload to JWT string.
    
    Args:
        payload: Token payload
        
    Returns:
        Encoded JWT token
    """
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    """Create access token.
    
    Args:
        user_id: User ID
        
    Returns:
        Encoded JWT access token
    """
    payload = create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRATION_MINUTES),
    )
    return encode_token(payload)


def create_refresh_token(user_id: int) -> Tuple[str, str, datetime]:
    """Create refresh token.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (encoded_token, jti, expiration_datetime)
    """
    payload = create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS),
    )
    encoded = encode_token(payload)
    return encoded, str(payload["jti"]), payload["exp"]


def create_password_reset_token(user_id: int) -> str:
    """Create password reset token.
    
    Args:
        user_id: User ID
        
    Returns:
        Encoded JWT password reset token
    """
    payload = create_token(
        user_id=user_id,
        token_type="password_reset",
        expires_delta=timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES),
    )
    return encode_token(payload)


def build_auth_response(
    db: Session,
    user_id: int,
    request: Optional[Any] = None,
    previous_refresh_jti: Optional[str] = None,
) -> Dict[str, Any]:
    """Build authentication response with tokens.
    
    Args:
        db: Database session
        user_id: User ID
        request: FastAPI request object (optional)
        previous_refresh_jti: Previous JTI to revoke (optional)
        
    Returns:
        Dictionary with tokens and user info
    """
    from utils import get_remote_address
    
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(user_id)
    user_agent = (
        request.headers.get("user-agent")[:255] 
        if request and request.headers.get("user-agent") 
        else None
    )
    ip_address = get_remote_address(request) if request else None
    
    crud.create_refresh_token(
        db,
        user_id=user_id,
        jti=refresh_jti,
        expires_at=refresh_exp,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    if previous_refresh_jti:
        crud.revoke_refresh_token(
            db,
            previous_refresh_jti,
            replaced_by_jti=refresh_jti,
            reason="rotated",
        )

    return {
        "access_token": create_access_token(user_id),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user_id,
        "access_token_expires_in": ACCESS_TOKEN_EXPIRATION_MINUTES * 60,
    }


def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """Decode and validate JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type
        
    Returns:
        Token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    from fastapi import HTTPException
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


def decode_access_user_id(token: str) -> int:
    """Decode access token and extract user ID.
    
    Args:
        token: JWT access token
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    from fastapi import HTTPException
    
    try:
        payload = decode_token(token, expected_type="access")
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
