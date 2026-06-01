"""Authentication endpoints."""

from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database import crud
from schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    RegisterResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetRequestResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    ResendVerificationRequest,
    AuthSessionsResponse,
    LogoutAllResponse,
)
from auth_utils import (
    hash_password,
    verify_password,
    create_email_verification_token,
    hash_email_verification_token,
    send_verification_code_email,
    build_auth_response,
    decode_token,
    decode_access_user_id,
    create_password_reset_token,
)
from config import EMAIL_VERIFICATION_REQUIRED
from utils import audit_auth_event, verify_user_ownership
from utils import utcnow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

security = HTTPBearer(auto_error=False)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> int:
    """Verify JWT token and return user_id.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token invalid or missing
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return decode_access_user_id(credentials.credentials)


@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
) -> RegisterResponse:
    """Register a new user.
    
    Args:
        user_data: User registration data
        request: HTTP request
        db: Database session
        
    Returns:
        Registration response with verification token if email verification required
    """
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        audit_auth_event(
            "register",
            request,
            "failure",
            email=user_data.email,
            detail="Email already registered"
        )
        raise crud.DuplicateEmailError("Email already registered")

    password_hash = hash_password(user_data.password)

    if EMAIL_VERIFICATION_REQUIRED:
        verification_token, token_hash, expires_at = create_email_verification_token()

        new_user = crud.create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            email_verified=False,
            email_verification_token_hash=token_hash,
            email_verification_expires_at=expires_at,
        )

        try:
            send_verification_code_email(user_data.email, verification_token)
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            db.delete(new_user)
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to send verification email")

        audit_auth_event(
            "register",
            request,
            "success",
            user_id=new_user.id,
            email=user_data.email
        )

        return RegisterResponse(
            detail="User registered successfully. Please verify your email.",
            email_verification_required=True,
            email=user_data.email,
            verification_token=verification_token
        )
    else:
        new_user = crud.create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            email_verified=True,
        )

        audit_auth_event(
            "register",
            request,
            "success",
            user_id=new_user.id,
            email=user_data.email
        )

        return RegisterResponse(
            detail="User registered successfully",
            email_verification_required=False,
            email=user_data.email,
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Login user and return tokens.
    
    Args:
        user_login: Login credentials
        request: HTTP request
        db: Database session
        
    Returns:
        Tokens and user info
    """
    user = crud.get_user_by_email(db, user_login.email)
    
    if not user or not verify_password(user_login.password, user.password_hash):
        audit_auth_event(
            "login",
            request,
            "failure",
            email=user_login.email,
            detail="Invalid credentials"
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if EMAIL_VERIFICATION_REQUIRED and not user.email_verified:
        audit_auth_event(
            "login",
            request,
            "failure",
            user_id=user.id,
            email=user_login.email,
            detail="Email not verified"
        )
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email before logging in."
        )

    auth_response = build_auth_response(db, user.id, request)
    
    audit_auth_event(
        "login",
        request,
        "success",
        user_id=user.id,
        email=user_login.email
    )
    
    return TokenResponse(**auth_response)


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    data: EmailVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> EmailVerificationResponse:
    """Verify user's email with verification token.
    
    Args:
        data: Email verification data
        request: HTTP request
        db: Database session
        
    Returns:
        Verification response
    """
    token_hash = hash_email_verification_token(data.verification_token)
    user = crud.get_user_by_email_verification_token_hash(db, token_hash)

    if not user:
        audit_auth_event(
            "verify_email",
            request,
            "failure",
            detail="Invalid verification token"
        )
        raise crud.ValidationError("Invalid verification token")

    if user.email_verification_expires_at and user.email_verification_expires_at < utcnow():
        audit_auth_event(
            "verify_email",
            request,
            "failure",
            user_id=user.id,
            detail="Verification token expired"
        )
        raise crud.ValidationError("Verification token expired")

    crud.mark_email_verified(db, user.id)
    
    audit_auth_event(
        "verify_email",
        request,
        "success",
        user_id=user.id,
        email=user.email
    )
    
    return EmailVerificationResponse(
        detail="Email verified successfully",
        email_verification_required=False,
        email=user.email
    )


@router.post("/resend-verification", response_model=EmailVerificationResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> EmailVerificationResponse:
    """Resend verification email.
    
    Args:
        data: Email to resend verification to
        request: HTTP request
        db: Database session
        
    Returns:
        Verification response
    """
    user = crud.get_user_by_email(db, data.email)

    if not user:
        raise crud.UserNotFoundError("User not found")

    if user.email_verified:
        return EmailVerificationResponse(
            detail="Email already verified",
            email_verification_required=False,
            email=user.email
        )

    verification_token, token_hash, expires_at = create_email_verification_token()

    crud.update_email_verification_token(
        db,
        user.id,
        token_hash,
        expires_at
    )

    try:
        send_verification_code_email(user.email, verification_token)
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    audit_auth_event(
        "resend_verification",
        request,
        "success",
        user_id=user.id,
        email=user.email
    )

    return EmailVerificationResponse(
        detail="Verification email sent",
        email_verification_required=True,
        email=user.email,
        verification_token=verification_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token.
    
    Args:
        data: Refresh token request
        request: HTTP request
        db: Database session
        
    Returns:
        New access token
    """
    try:
        payload = decode_token(data.refresh_token, expected_type="refresh")
        user_id = payload.get("user_id")
        previous_jti = payload.get("jti")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        auth_response = build_auth_response(db, user_id, request, previous_jti)

        return TokenResponse(**auth_response)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(
    request: Request,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> dict:
    """Logout current session.
    
    Args:
        request: HTTP request
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Logout confirmation
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token, expected_type="access")
            jti = payload.get("jti")
            if jti:
                crud.revoke_refresh_token(db, jti, reason="user_logout")
        except Exception:
            pass

    audit_auth_event(
        "logout",
        request,
        "success",
        user_id=current_user_id
    )

    return {"message": "Logged out successfully"}


@router.post("/logout-all", response_model=LogoutAllResponse)
async def logout_all_sessions(
    request: Request,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> LogoutAllResponse:
    """Logout all sessions for current user.
    
    Args:
        request: HTTP request
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Number of sessions revoked
    """
    revoked_count = crud.revoke_all_user_sessions(db, current_user_id, reason="user_logout_all")

    audit_auth_event(
        "logout_all",
        request,
        "success",
        user_id=current_user_id,
        detail=f"Revoked {revoked_count} sessions"
    )

    return LogoutAllResponse(
        detail=f"All sessions revoked",
        revoked_sessions=revoked_count
    )


@router.get("/sessions", response_model=AuthSessionsResponse)
async def get_sessions(
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> AuthSessionsResponse:
    """Get all active sessions for current user.
    
    Args:
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        List of active sessions
    """
    sessions = crud.get_user_sessions(db, current_user_id)

    total = len(sessions)
    active = sum(1 for s in sessions if s.revoked_at is None)

    session_infos = [
        {
            "jti": s.jti,
            "created_at": s.created_at,
            "last_used_at": s.last_used_at,
            "expires_at": s.expires_at,
            "revoked_at": s.revoked_at,
            "revoked_reason": s.revoked_reason,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "is_active": s.revoked_at is None,
        }
        for s in sessions
    ]

    return AuthSessionsResponse(
        total_sessions=total,
        active_sessions=active,
        sessions=session_infos
    )


@router.delete("/sessions/{jti}")
async def revoke_session(
    jti: str,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> dict:
    """Revoke a specific session.
    
    Args:
        jti: Session JWT ID
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Revocation confirmation
    """
    session = crud.get_refresh_token_by_jti(db, jti)

    if not session or session.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    crud.revoke_refresh_token(db, jti, reason="user_revoked_session")

    return {"message": "Session revoked"}


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> PasswordResetRequestResponse:
    """Request password reset token.
    
    Args:
        data: Email for password reset
        request: HTTP request
        db: Database session
        
    Returns:
        Password reset request response
    """
    user = crud.get_user_by_email(db, data.email)

    if not user:
        return PasswordResetRequestResponse(
            detail="If email exists, password reset link will be sent"
        )

    reset_token = create_password_reset_token(user.id)

    try:
        _send_password_reset_email(user.email, reset_token)
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send password reset email")

    audit_auth_event(
        "password_reset_request",
        request,
        "success",
        user_id=user.id,
        email=user.email
    )

    return PasswordResetRequestResponse(
        detail="Password reset link sent to email"
    )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """Confirm password reset with token.
    
    Args:
        data: Password reset confirmation data
        request: HTTP request
        db: Database session
        
    Returns:
        Confirmation response
    """
    try:
        payload = decode_token(data.reset_token, expected_type="password_reset")
        user_id = payload.get("user_id")

        if not user_id:
            raise crud.ValidationError("Invalid reset token")

        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise crud.UserNotFoundError("User not found")

        password_hash = hash_password(data.new_password)
        crud.update_user_password(db, user_id, password_hash)

        audit_auth_event(
            "password_reset_confirm",
            request,
            "success",
            user_id=user_id,
            email=user.email
        )

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except crud.CRUDException:
        raise
    except Exception:
        raise crud.ValidationError("Invalid or expired reset token")


def _send_password_reset_email(email: str, reset_token: str) -> None:
    """Send password reset email.
    
    Args:
        email: Recipient email
        reset_token: Reset token to send
    """
    import smtplib
    from email.message import EmailMessage
    from config import (
        SMTP_HOST,
        SMTP_PORT,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        SMTP_FROM_ADDRESS,
        SMTP_USE_TLS,
        IS_DEV_ENV,
    )

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        if IS_DEV_ENV:
            logger.info(
                "DEV_PASSWORD_RESET recipient=%s token=%s",
                email,
                reset_token,
            )
            return
        raise RuntimeError("SMTP credentials are required to send password reset emails")

    message = EmailMessage()
    message["Subject"] = "Fashion App Password Reset"
    message["From"] = SMTP_FROM_ADDRESS or SMTP_USERNAME
    message["To"] = email
    message.set_content(
        f"""Your password reset link is below.

Reset Token: {reset_token}

This token expires in 30 minutes.
If you did not request this, you can ignore this email.
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


# datetime import removed (not used)
