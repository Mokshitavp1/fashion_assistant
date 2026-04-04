import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import shutil
import os
import logging
import asyncio
import base64
import hashlib
import hmac
import smtplib
import re
import secrets
import uuid
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import cv2
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import String, Boolean, inspect, text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database
from database.database import engine, SessionLocal
from database import models, crud

# Import services
from services.color_analysis import (
    detect_face_region,
    extract_dominant_skin_color,
    classify_undertone
)
from services.body_shape import classify_body_shape_with_bmi
from services.clothing_classifier import classify_clothing
from services.discard_analyzer import get_discard_recommendations
from services.shopping_assistant import analyze_shopping_item
from services.outfit_generator import get_outfit_recommendations
from services.secure_image_storage import (
    store_encrypted_image,
    retrieve_encrypted_image,
    delete_encrypted_image,
    get_image_info,
    cleanup_old_images
)
from services.task_queue import enqueue_inference_job, fetch_job, get_job_owner, get_job_type

logger = logging.getLogger(__name__)


def audit_auth_event(
    event: str,
    request: Request,
    outcome: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """Structured auth audit logs for security monitoring."""
    payload = {
        "event": event,
        "outcome": outcome,
        "user_id": user_id,
        "email": email,
        "ip": get_remote_address(request),
        "path": request.url.path,
        "detail": detail,
    }
    if outcome == "success":
        logger.info("AUTH_AUDIT %s", payload)
    else:
        logger.warning("AUTH_AUDIT %s", payload)


def get_rate_limit_key(request: Request) -> str:
    """Prefer a verified user key when possible; fallback to client IP."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "access" and payload.get("user_id"):
                return f"user:{payload['user_id']}"
        except jwt.InvalidTokenError:
            pass
    return get_remote_address(request)

# ============ CONFIGURATION ============
UPLOAD_DIR = "uploaded_images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY must be set and at least 32 characters long. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTES", "15"))
REFRESH_TOKEN_EXPIRATION_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))
PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES", "30"))
EMAIL_VERIFICATION_EXPIRATION_HOURS = int(os.getenv("EMAIL_VERIFICATION_EXPIRATION_HOURS", "24"))
PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "310000"))
ENVIRONMENT = os.getenv("ENV", "development").lower()
IS_DEV_ENV = ENVIRONMENT in {"dev", "development", "local"}
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_ADDRESS = os.getenv("SMTP_FROM_ADDRESS", SMTP_USERNAME).strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
MAX_CONCURRENT_IMAGE_JOBS = int(os.getenv("MAX_CONCURRENT_IMAGE_JOBS", "4"))
IMAGE_JOB_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_IMAGE_JOBS)
INFERENCE_QUEUE_ENABLED = os.getenv(
    "INFERENCE_QUEUE_ENABLED",
    "false" if IS_DEV_ENV else "true",
).strip().lower() in {"1", "true", "yes", "on"}


async def run_bounded_image_job(job_name: str, func, *args, **kwargs):
    """Run CPU-heavy image work in a bounded worker pool to protect event loop latency."""
    async with IMAGE_JOB_SEMAPHORE:
        logger.debug("Starting image job: %s", job_name)
        try:
            return await run_in_threadpool(func, *args, **kwargs)
        finally:
            logger.debug("Finished image job: %s", job_name)


def _analyze_skin_tone(image_array: np.ndarray) -> Tuple[Tuple[int, int, int], str]:
    face_region = detect_face_region(image_array)
    dominant_color = extract_dominant_skin_color(face_region)
    undertone = classify_undertone(dominant_color)
    return dominant_color, undertone


def to_json_compatible(value):
    """Convert numpy/scalar container values into JSON-serializable Python values."""
    if isinstance(value, dict):
        return {k: to_json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_compatible(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value

# ============ PYDANTIC MODELS ============
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @field_validator('name')
    def name_not_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if len(v.strip()) > 100:
            raise ValueError('Name must be less than 100 characters')
        return v.strip()

    @field_validator('password')
    def password_strength(cls, v):
        validate_password(v)
        return v

    @field_validator('email')
    def gmail_only(cls, v):
        email = str(v).strip().lower()
        gmail_pattern = r'^[a-z0-9](?:[a-z0-9._%+-]{0,61}[a-z0-9])?@gmail\.com$'
        if not re.match(gmail_pattern, email):
            raise ValueError('Email not valid. Please use a real Gmail address.')
        if '..' in email.split('@', 1)[0]:
            raise ValueError('Email not valid. Please use a real Gmail address.')
        return email

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password is required')
        return v

class UserAnalyze(BaseModel):
    height: float
    weight: float
    
    @field_validator('height', 'weight')
    def validate_measurements(cls, v):
        if v <= 0 or v > 300:
            raise ValueError('Measurements must be between 0 and 300')
        return v

class WardrobeItemCreate(BaseModel):
    category: str
    season: Optional[str] = None
    
    @field_validator('category')
    def category_not_empty(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Category is required')
        if len(v.strip()) > 50:
            raise ValueError('Category must be less than 50 characters')
        return v.strip()
    
    @field_validator('season')
    def validate_season(cls, v):
        if v is not None and len(v.strip()) > 50:
            raise ValueError('Season must be less than 50 characters')
        return v

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    access_token_expires_in: int

class RegisterResponse(BaseModel):
    detail: str
    email_verification_required: bool = True
    email: str
    verification_token: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

    @field_validator('refresh_token')
    def refresh_token_required(cls, v):
        if not v or not v.strip():
            raise ValueError('refresh_token is required')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str

    @field_validator('reset_token')
    def reset_token_required(cls, v):
        if not v or not v.strip():
            raise ValueError('reset_token is required')
        return v

    @field_validator('new_password')
    def new_password_strength(cls, v):
        validate_password(v)
        return v

class PasswordResetRequestResponse(BaseModel):
    detail: str
    reset_token: Optional[str] = None

class EmailVerificationRequest(BaseModel):
    verification_token: str

    @field_validator('verification_token')
    def verification_token_required(cls, v):
        if not v or not v.strip():
            raise ValueError('verification_token is required')
        return v

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationResponse(BaseModel):
    detail: str
    email_verification_required: bool = True
    email: Optional[str] = None
    verification_token: Optional[str] = None

class AuthSessionInfo(BaseModel):
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
    total_sessions: int
    active_sessions: int
    sessions: list[AuthSessionInfo]

class LogoutAllResponse(BaseModel):
    detail: str
    revoked_sessions: int

# ============ SETUP ============
for table in models.Base.metadata.tables.values():
    for col in table.columns:
        if isinstance(col.type, String) and col.type.length is None:
            col.type.length = 255

try:
    models.Base.metadata.create_all(bind=engine)
except OperationalError as exc:
    raise RuntimeError(
        "Database connection failed. Check DATABASE_URL credentials or switch to SQLite."
    ) from exc

def ensure_auth_schema() -> None:
    """Backfill auth schema for existing databases."""
    inspector = inspect(engine)
    users_columns = {column["name"] for column in inspector.get_columns("users")}
    if "password_hash" in users_columns:
        pass
    else:
        with engine.begin() as connection:
            if engine.dialect.name == "sqlite":
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT '' NOT NULL")
                )
            else:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''")
                )

    user_alterations = []
    if "email_verified" not in users_columns:
        if engine.dialect.name == "sqlite":
            user_alterations.append("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
        else:
            user_alterations.append("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0")
    if "email_verification_token_hash" not in users_columns:
        user_alterations.append("ALTER TABLE users ADD COLUMN email_verification_token_hash VARCHAR(255)")
    if "email_verification_expires_at" not in users_columns:
        user_alterations.append("ALTER TABLE users ADD COLUMN email_verification_expires_at DATETIME")
    if "email_verified_at" not in users_columns:
        user_alterations.append("ALTER TABLE users ADD COLUMN email_verified_at DATETIME")

    if user_alterations:
        with engine.begin() as connection:
            for stmt in user_alterations:
                connection.execute(text(stmt))

    tables = set(inspector.get_table_names())
    if "refresh_tokens" not in tables:
        return

    refresh_columns = {column["name"] for column in inspector.get_columns("refresh_tokens")}
    alterations = []
    if "last_used_at" not in refresh_columns:
        alterations.append("ALTER TABLE refresh_tokens ADD COLUMN last_used_at DATETIME")
    if "user_agent" not in refresh_columns:
        alterations.append("ALTER TABLE refresh_tokens ADD COLUMN user_agent VARCHAR(255)")
    if "ip_address" not in refresh_columns:
        alterations.append("ALTER TABLE refresh_tokens ADD COLUMN ip_address VARCHAR(64)")
    if "revoked_reason" not in refresh_columns:
        alterations.append("ALTER TABLE refresh_tokens ADD COLUMN revoked_reason VARCHAR(100)")

    if alterations:
        with engine.begin() as connection:
            for stmt in alterations:
                connection.execute(text(stmt))

ensure_auth_schema()

app = FastAPI(title="Fashion App API", version="1.0.0")

# Rate limiting
limiter = Limiter(key_func=get_rate_limit_key)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

# CORS - Restrict to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

security = HTTPBearer(auto_error=False)

# ============ AUTHENTICATION ============
def validate_password(password: str) -> None:
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
    """Return a PBKDF2 hash in format: pbkdf2_sha256$iterations$salt$hash."""
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
    raw_token = f"{secrets.randbelow(1_000_000):06d}"
    token_hash = hmac.new(
        SECRET_KEY.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRATION_HOURS)
    return raw_token, token_hash, expires_at

def hash_email_verification_token(token: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        token.strip().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

def send_verification_code_email(recipient_email: str, verification_code: str) -> None:
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
        """Your confirmation code is below.

Confirmation code: {code}

This code expires in {hours} hours.
If you did not request this, you can ignore this email.
""".format(code=verification_code, hours=EMAIL_VERIFICATION_EXPIRATION_HOURS)
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

def create_token(user_id: int, token_type: str, expires_delta: timedelta) -> Dict[str, Any]:
    now = datetime.utcnow()
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
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(user_id: int) -> str:
    payload = create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRATION_MINUTES),
    )
    return encode_token(payload)

def create_refresh_token(user_id: int) -> Tuple[str, str, datetime]:
    payload = create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS),
    )
    encoded = encode_token(payload)
    return encoded, str(payload["jti"]), payload["exp"]

def create_password_reset_token(user_id: int) -> str:
    payload = create_token(
        user_id=user_id,
        token_type="password_reset",
        expires_delta=timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES),
    )
    return encode_token(payload)

def build_auth_response(
    db: Session,
    user_id: int,
    request: Optional[Request] = None,
    previous_refresh_jti: Optional[str] = None,
) -> Dict[str, Any]:
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(user_id)
    user_agent = request.headers.get("user-agent")[:255] if request and request.headers.get("user-agent") else None
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
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload

def decode_access_user_id(token: str) -> int:
    """Decode an access token and return the user id."""
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

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> int:
    """Verify JWT token and return user_id"""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return decode_access_user_id(credentials.credentials)

# ============ DATABASE ============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ HELPER FUNCTIONS ============
def validate_file_size(file: UploadFile) -> None:
    """Validate uploaded file size"""
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )

def validate_file_type(file: UploadFile) -> None:
    """Validate uploaded file extension"""
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
            )

def verify_user_ownership(user_id: int, current_user_id: int) -> None:
    """Verify that current user owns the resource"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

# ============ ROUTES ============
@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Fashion App API is running"}

@app.post("/auth/register", response_model=RegisterResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user and return access token"""
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        audit_auth_event("register", request, "failure", email=user_data.email, detail="email_exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    verification_token, token_hash, expires_at = create_email_verification_token()
    crud.set_email_verification_token(db, user.id, token_hash, expires_at)
    try:
        send_verification_code_email(user.email, verification_token)
    except RuntimeError as exc:
        logger.error("Failed to send verification code to %s: %s", user.email, exc)
        raise HTTPException(status_code=502, detail="Unable to send confirmation email right now.")

    audit_auth_event("register", request, "success", user_id=user.id, email=user.email)
    return {
        "detail": "Account created. Please check your Gmail for the confirmation code.",
        "email_verification_required": True,
        "email": user.email,
        "verification_token": verification_token if ENVIRONMENT in {"development", "dev", "local", "test"} else None,
    }

@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    if not email or "@" not in email:
        audit_auth_event("login", request, "failure", email=email, detail="invalid_email_format")
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not password:
        audit_auth_event("login", request, "failure", email=email, detail="missing_password")
        raise HTTPException(status_code=400, detail="Password is required")
    
    user = crud.get_user_by_email(db, email)
    if not user or not user.password_hash:
        audit_auth_event("login", request, "failure", email=email, detail="invalid_credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.email_verified:
        audit_auth_event("login", request, "failure", user_id=user.id, email=user.email, detail="email_not_verified")
        raise HTTPException(status_code=403, detail="Please confirm your email before signing in")

    if not verify_password(password, user.password_hash):
        audit_auth_event("login", request, "failure", user_id=user.id, email=user.email, detail="invalid_credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    audit_auth_event("login", request, "success", user_id=user.id, email=user.email)
    return build_auth_response(db, user.id, request=request)

@app.post("/auth/verify-email", response_model=EmailVerificationResponse)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """Confirm a user's email address using a verification token."""
    token_hash = hash_email_verification_token(verification_data.verification_token)
    user = crud.get_user_by_email_verification_token(db, token_hash)
    if not user:
        audit_auth_event("verify_email", request, "failure", detail="token_not_found")
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if user.email_verified:
        audit_auth_event("verify_email", request, "success", user_id=user.id, email=user.email, detail="already_verified")
        return {
            "detail": "Email is already verified.",
            "email_verification_required": False,
            "email": user.email,
        }

    if not user.email_verification_expires_at or user.email_verification_expires_at <= datetime.utcnow():
        audit_auth_event("verify_email", request, "failure", user_id=user.id, email=user.email, detail="token_expired")
        raise HTTPException(status_code=400, detail="Verification token expired. Please request a new one.")

    crud.mark_email_verified(db, user.id)
    audit_auth_event("verify_email", request, "success", user_id=user.id, email=user.email)
    return {
        "detail": "Email confirmed. You can now sign in.",
        "email_verification_required": False,
        "email": user.email,
    }

@app.post("/auth/resend-verification", response_model=EmailVerificationResponse)
@limiter.limit("5/minute")
async def resend_verification_email(
    request: Request,
    resend_data: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Generate a fresh verification token for an unverified account."""
    user = crud.get_user_by_email(db, resend_data.email)
    if not user:
        audit_auth_event("resend_verification", request, "success", email=resend_data.email, detail="user_not_found")
        return {
            "detail": "If that email is registered, a new verification token was generated.",
            "email_verification_required": True,
            "email": resend_data.email,
        }

    if user.email_verified:
        audit_auth_event("resend_verification", request, "success", user_id=user.id, email=user.email, detail="already_verified")
        return {
            "detail": "Email is already verified.",
            "email_verification_required": False,
            "email": user.email,
        }

    verification_token, token_hash, expires_at = create_email_verification_token()
    crud.set_email_verification_token(db, user.id, token_hash, expires_at)
    try:
        send_verification_code_email(user.email, verification_token)
    except RuntimeError as exc:
        logger.error("Failed to resend verification code to %s: %s", user.email, exc)
        raise HTTPException(status_code=502, detail="Unable to send confirmation email right now.")
    audit_auth_event("resend_verification", request, "success", user_id=user.id, email=user.email)
    return {
        "detail": "A fresh confirmation code was sent.",
        "email_verification_required": True,
        "email": user.email,
        "verification_token": verification_token if ENVIRONMENT in {"development", "dev", "local", "test"} else None,
    }

@app.post("/auth/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Rotate access/refresh tokens using a valid refresh token."""
    try:
        payload = decode_token(refresh_data.refresh_token, expected_type="refresh")
        user_id = payload.get("user_id")
        jti = payload.get("jti")
        if not user_id:
            audit_auth_event("refresh", request, "failure", detail="missing_user_id")
            raise HTTPException(status_code=401, detail="Invalid token")
        if not jti:
            audit_auth_event("refresh", request, "failure", user_id=int(user_id), detail="missing_jti")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        audit_auth_event("refresh", request, "failure", detail="expired")
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        audit_auth_event("refresh", request, "failure", detail="invalid_token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_record = crud.get_refresh_token_by_jti(db, str(jti))
    if not token_record or token_record.user_id != int(user_id):
        audit_auth_event("refresh", request, "failure", user_id=int(user_id), detail="token_not_found")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if token_record.revoked_at is not None:
        audit_auth_event("refresh", request, "failure", user_id=int(user_id), detail="token_replay")
        raise HTTPException(status_code=401, detail="Refresh token already used")
    if token_record.expires_at <= datetime.utcnow():
        audit_auth_event("refresh", request, "failure", user_id=int(user_id), detail="token_expired_db")
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = crud.get_user_by_id(db, int(user_id))
    if not user:
        audit_auth_event("refresh", request, "failure", user_id=int(user_id), detail="user_not_found")
        raise HTTPException(status_code=401, detail="User not found")

    crud.touch_refresh_token_usage(db, str(jti))
    audit_auth_event("refresh", request, "success", user_id=user.id, email=user.email)
    return build_auth_response(db, user.id, request=request, previous_refresh_jti=str(jti))

@app.post("/auth/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Revoke a specific refresh token (logout current session)."""
    try:
        payload = decode_token(refresh_data.refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        user_id = payload.get("user_id")
        if jti:
            crud.revoke_refresh_token(db, str(jti), reason="logout")
        audit_auth_event("logout", request, "success", user_id=int(user_id) if user_id else None)
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, HTTPException):
        # Return generic success to avoid token existence leakage.
        audit_auth_event("logout", request, "failure", detail="invalid_or_expired_refresh_token")

    return {"detail": "Logged out"}

@app.post("/auth/logout-all", response_model=LogoutAllResponse)
@limiter.limit("10/minute")
async def logout_all_devices(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token),
):
    """Revoke all active refresh tokens for the current user."""
    revoked = crud.revoke_all_user_refresh_tokens(db, current_user_id)
    audit_auth_event("logout_all", request, "success", user_id=current_user_id, detail=f"revoked={revoked}")
    return {"detail": "Logged out from all devices", "revoked_sessions": revoked}

@app.get("/auth/sessions", response_model=AuthSessionsResponse)
@limiter.limit("30/minute")
async def list_auth_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token),
):
    """List user sessions from refresh token records."""
    now = datetime.utcnow()
    tokens = crud.list_user_refresh_tokens(db, current_user_id)
    sessions = [
        {
            "jti": token.jti,
            "created_at": token.created_at,
            "last_used_at": token.last_used_at,
            "expires_at": token.expires_at,
            "revoked_at": token.revoked_at,
            "revoked_reason": token.revoked_reason,
            "ip_address": token.ip_address,
            "user_agent": token.user_agent,
            "is_active": token.revoked_at is None and token.expires_at > now,
        }
        for token in tokens
    ]
    active_count = sum(1 for s in sessions if s["is_active"])
    audit_auth_event("sessions_list", request, "success", user_id=current_user_id, detail=f"count={len(sessions)}")
    return {
        "total_sessions": len(sessions),
        "active_sessions": active_count,
        "sessions": sessions,
    }

@app.delete("/auth/sessions/{jti}")
@limiter.limit("30/minute")
async def revoke_auth_session(
    request: Request,
    jti: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token),
):
    """Revoke one of the current user's sessions by refresh token JTI."""
    revoked = crud.revoke_user_refresh_token(db, current_user_id, jti, reason="manual_revoke")
    if not revoked:
        audit_auth_event("session_revoke", request, "failure", user_id=current_user_id, detail="not_found_or_not_owned")
        raise HTTPException(status_code=404, detail="Session not found")
    audit_auth_event("session_revoke", request, "success", user_id=current_user_id, detail=f"jti={jti}")
    return {"detail": "Session revoked"}

@app.post("/auth/password-reset/request", response_model=PasswordResetRequestResponse)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Request a password reset token without leaking whether the email exists."""
    detail = "If that email is registered, password reset instructions have been sent."
    user = crud.get_user_by_email(db, reset_data.email)
    if not user:
        audit_auth_event("password_reset_request", request, "success", email=reset_data.email, detail="non_enumerating")
        return {"detail": detail}

    token = create_password_reset_token(user.id)
    if IS_DEV_ENV:
        audit_auth_event("password_reset_request", request, "success", user_id=user.id, email=user.email)
        return {"detail": detail, "reset_token": token}

    audit_auth_event("password_reset_request", request, "success", user_id=user.id, email=user.email)
    logger.info("Password reset requested for user_id=%s", user.id)
    return {"detail": detail}

@app.post("/auth/password-reset/confirm")
@limiter.limit("5/minute")
async def confirm_password_reset(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset with a short-lived reset token."""
    try:
        payload = decode_token(reset_data.reset_token, expected_type="password_reset")
        user_id = payload.get("user_id")
        if not user_id:
            audit_auth_event("password_reset_confirm", request, "failure", detail="missing_user_id")
            raise HTTPException(status_code=401, detail="Invalid reset token")
    except jwt.ExpiredSignatureError:
        audit_auth_event("password_reset_confirm", request, "failure", detail="expired")
        raise HTTPException(status_code=401, detail="Reset token expired")
    except jwt.InvalidTokenError:
        audit_auth_event("password_reset_confirm", request, "failure", detail="invalid_token")
        raise HTTPException(status_code=401, detail="Invalid reset token")

    updated = crud.update_user_password(
        db,
        int(user_id),
        hash_password(reset_data.new_password),
    )
    if not updated:
        audit_auth_event("password_reset_confirm", request, "failure", user_id=int(user_id), detail="user_not_found")
        raise HTTPException(status_code=404, detail="User not found")

    # Password reset invalidates all active sessions for this account.
    crud.revoke_all_user_refresh_tokens(db, int(user_id))
    audit_auth_event("password_reset_confirm", request, "success", user_id=int(user_id))

    return {"detail": "Password reset successful"}

@app.get("/images/{image_id}")
@limiter.limit("60/minute")
async def retrieve_image(
    request: Request,
    image_id: str,
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    AUTHENTICATED image retrieval endpoint.
    
    Returns encrypted image if user has access.
    Verifies ownership before decryption.
    """
    bearer_token = token or (credentials.credentials if credentials else None)
    if not bearer_token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    current_user_id = decode_access_user_id(bearer_token)

    try:
        image_bytes = retrieve_encrypted_image(
            image_id=image_id,
            user_id=current_user_id,
            secret_key=SECRET_KEY,
            verify_ownership=True
        )
        
        logger.info(f"Image retrieval: user {current_user_id} accessed image {image_id}")
        
        return StreamingResponse(
            iter([image_bytes]),
            media_type="image/jpeg",
            headers={
                "Cache-Control": "private, max-age=3600",
                "Content-Disposition": f'inline; filename="image.jpg"',
                "X-Content-Type-Options": "nosniff",
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")
    except PermissionError:
        logger.warning(f"Unauthorized image access: user {current_user_id} tried to access {image_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    except ValueError as e:
        logger.error(f"Image retrieval error for {image_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Image data corrupted")


@app.get("/jobs/{job_id}")
@limiter.limit("120/minute")
async def get_inference_job(
    request: Request,
    job_id: str,
    current_user_id: int = Depends(verify_token),
):
    """Get status/result for a queued inference job owned by the current user."""
    try:
        job = fetch_job(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    owner_user_id = get_job_owner(job_id)

    if owner_user_id is not None and owner_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    status = str(job.status or "PENDING").lower()
    payload = {
        "job_id": job.id,
        "job_type": get_job_type(job_id),
        "status": status,
        "is_finished": bool(job.ready() and job.successful()),
        "is_failed": bool(job.failed()),
    }

    if job.ready() and job.successful():
        payload["result"] = to_json_compatible(job.result)
    elif job.failed():
        payload["error"] = str(job.result or "Job failed")[:1000]

    return payload

@app.post("/users/{user_id}/analyze")
@limiter.limit("10/minute")
async def analyze_user(
    request: Request,
    user_id: int,
    image: UploadFile = File(...),
    height: float = Form(...),
    weight: float = Form(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Analyze user's body shape and skin tone, save to database"""
    verify_user_ownership(user_id, current_user_id)
    validate_file_size(image)
    validate_file_type(image)
    
    user_data = UserAnalyze(height=height, weight=weight)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if INFERENCE_QUEUE_ENABLED:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Invalid image file")
        try:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            job = enqueue_inference_job(
                "worker_tasks.process_analyze_job",
                kwargs={
                    "user_id": user_id,
                    "height": float(user_data.height),
                    "weight": float(user_data.weight),
                    "image_b64": image_b64,
                },
                user_id=user_id,
                job_type="analyze",
            )
        except Exception as exc:
            logger.error("Failed to enqueue analyze job: %s", exc)
            raise HTTPException(status_code=503, detail="Inference queue unavailable")

        base = str(request.base_url).rstrip("/")
        return JSONResponse(
            status_code=202,
            content={
                "message": "Analyze job queued",
                "job_id": job,
                "status": "queued",
                "result_url": f"{base}/jobs/{job}",
                "queue_mode": "async",
            },
        )
    
    image_bytes = await image.read()
    np_array = np.frombuffer(image_bytes, np.uint8)
    image_array = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image_array is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Store encrypted image
    try:
        image_id, image_reference = store_encrypted_image(
            image_bytes=image_bytes,
            user_id=user_id,
            secret_key=SECRET_KEY,
            image_type="profile",
            metadata={"width": image_array.shape[1], "height": image_array.shape[0]}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Image storage failed: {str(e)}")
    
    dominant_color, undertone = await run_bounded_image_job(
        "skin_tone_analysis",
        _analyze_skin_tone,
        image_array,
    )

    body_analysis = await run_bounded_image_job(
        "body_shape_analysis",
        classify_body_shape_with_bmi,
        image_array,
        user_data.height,
        user_data.weight,
    )
    
    updated_user = crud.update_user_analysis(
        db=db,
        user_id=user_id,
        height=user_data.height,
        weight=user_data.weight,
        body_shape=body_analysis["body_shape"],
        undertone=undertone,
        bmi=body_analysis["bmi"]
    )
    
    # Store encrypted reference instead of plain path
    updated_user.profile_image_path = image_reference
    db.commit()
    
    return {
        "message": "Analysis complete and saved",
        "user_id": user_id,
        "dominant_skin_color_rgb": to_json_compatible(dominant_color),
        "undertone": undertone,
        "body_shape": body_analysis["body_shape"],
        "body_shape_confidence": to_json_compatible(body_analysis["confidence"]),
        "measurements": to_json_compatible(body_analysis["measurements"]),
        "bmi": to_json_compatible(body_analysis["bmi"]),
        "height": user_data.height,
        "weight": user_data.weight,
        "profile_image_id": image_id
    }

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    request: Request = None,
    current_user_id: int = Depends(verify_token)
):
    """Get user profile and analysis data"""
    verify_user_ownership(user_id, current_user_id)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert encrypted reference to image URL if present
    profile_image_url = None
    if user.profile_image_path and user.profile_image_path.startswith("encrypted://"):
        image_id = user.profile_image_path.replace("encrypted://", "")
        profile_image_url = f"{request.base_url}images/{image_id}".rstrip("/") if request else f"/images/{image_id}"
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image_url": profile_image_url,
        "height": user.height,
        "weight": user.weight,
        "body_shape": user.body_shape,
        "undertone": user.undertone,
        "bmi": user.bmi,
        "created_at": user.created_at
    }

@app.post("/users/{user_id}/wardrobe/add")
@limiter.limit("30/minute")
async def add_wardrobe_item(
    request: Request,
    user_id: int,
    image: UploadFile = File(...),
    category: str = Form(...),
    season: str = Form(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Add a clothing item to user's wardrobe"""
    verify_user_ownership(user_id, current_user_id)
    validate_file_size(image)
    validate_file_type(image)
    
    item_data = WardrobeItemCreate(category=category, season=season)

    def normalize_type_with_category(predicted_type: str, selected_category: str) -> str:
        predicted = (predicted_type or "other").strip().lower()
        category_norm = (selected_category or "").strip().lower()

        if category_norm == "bottom" and predicted in {"top", "outerwear", "dress"}:
            return "bottom"
        if category_norm == "top" and predicted in {"bottom", "jeans", "dress"}:
            return "top"
        if category_norm == "dress":
            return "dress"
        if category_norm == "shoes":
            return "shoes"
        if category_norm == "accessories":
            return "accessories"
        return predicted
    
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if INFERENCE_QUEUE_ENABLED:
            image_bytes = await image.read()
            if not image_bytes:
                raise HTTPException(status_code=400, detail="Invalid image file")
            try:
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                job = enqueue_inference_job(
                    "worker_tasks.process_wardrobe_add_job",
                    kwargs={
                        "user_id": user_id,
                        "category": item_data.category,
                        "season": item_data.season or "all",
                        "image_b64": image_b64,
                    },
                    user_id=user_id,
                    job_type="wardrobe_add",
                )
            except Exception as exc:
                logger.error("Failed to enqueue wardrobe job: %s", exc)
                raise HTTPException(status_code=503, detail="Inference queue unavailable")

            base = str(request.base_url).rstrip("/")
            return JSONResponse(
                status_code=202,
                content={
                    "message": "Wardrobe add job queued",
                    "job_id": job,
                    "status": "queued",
                    "result_url": f"{base}/jobs/{job}",
                    "queue_mode": "async",
                },
            )
        
        image_bytes = await image.read()
        
        np_array = np.frombuffer(image_bytes, np.uint8)
        image_array = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Store encrypted image
        try:
            image_id, image_reference = store_encrypted_image(
                image_bytes=image_bytes,
                user_id=user_id,
                secret_key=SECRET_KEY,
                image_type="wardrobe",
                metadata={"width": image_array.shape[1], "height": image_array.shape[0]}
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Image storage failed: {str(e)}")
        
        classification = await run_bounded_image_job(
            "clothing_classification",
            classify_clothing,
            image_array,
        )

        normalized_type = normalize_type_with_category(
            classification.get("type"),
            item_data.category,
        )
        
        season_to_store = item_data.season or "all"
        wardrobe_item = crud.create_wardrobe_item(
            db=db,
            user_id=user_id,
            image_path=image_reference,
            clothing_type=normalized_type,
            color_primary=classification["color_primary"],
            color_secondary=classification["color_secondary"],
            pattern=classification["pattern"],
            season=season_to_store,
            category=item_data.category
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        try:
            db.refresh(wardrobe_item)
        except Exception:
            pass
        
        # Generate reference URL for frontend
        image_url = f"{request.base_url}images/{image_id}".rstrip("/")
        return {
            "message": "Clothing item added to wardrobe",
            "item": {
                "id": getattr(wardrobe_item, "id", None),
                "type": getattr(wardrobe_item, "clothing_type", None),
                "category": getattr(wardrobe_item, "category", None),
                "color_primary": getattr(wardrobe_item, "color_primary", None),
                "color_secondary": getattr(wardrobe_item, "color_secondary", None),
                "pattern": getattr(wardrobe_item, "pattern", None),
                "season": getattr(wardrobe_item, "season", None),
                "image_path": getattr(wardrobe_item, "image_path", None),
                "image_url": image_url,
                "image_id": image_id,
                "rgb_colors": classification.get("rgb_colors"),
                "model_confidence": classification.get("model_confidence"),
                "confidence_threshold": classification.get("confidence_threshold"),
                "used_fallback": classification.get("used_fallback"),
                "fallback_reason": classification.get("fallback_reason"),
                "top_model_label": classification.get("top_model_label"),
                "region_detection": classification.get("region_detection"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/users/{user_id}/wardrobe")
async def get_wardrobe(
    user_id: int,
    db: Session = Depends(get_db),
    request: Request = None,
    current_user_id: int = Depends(verify_token)
):
    """Get user's wardrobe items"""
    verify_user_ownership(user_id, current_user_id)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    items = crud.get_user_wardrobe(db, user_id)
    
    normalized_items = []
    seen_ids = set()
    for item in items:
        if hasattr(item, "id"):
            item_id = getattr(item, "id")
            if item_id is None or item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            img_path = getattr(item, "image_path", None)
            image_url = None
            image_id = None
            if img_path:
                # Convert encrypted reference to image URL
                if img_path.startswith("encrypted://"):
                    image_id = img_path.replace("encrypted://", "")
                    image_url = f"{request.base_url}images/{image_id}".rstrip("/") if request else f"/images/{image_id}"
                else:
                    # Legacy: plain path (shouldn't happen for new uploads)
                    filename_only = os.path.basename(img_path)
                    base = str(request.base_url).rstrip("/") if request else ""
                    image_url = f"{base}/uploads/{filename_only}" if base else f"/uploads/{filename_only}"
            
            normalized_items.append({
                "id": item_id,
                "type": item.clothing_type,
                "category": item.category,
                "color_primary": item.color_primary,
                "color_secondary": item.color_secondary,
                "pattern": item.pattern,
                "season": item.season,
                "image_path": img_path,
                "image_url": image_url,
                "image_id": image_id
            })
        else:
            minimal = models._item_to_dict_minimal(item)
            item_id = minimal.get("id")
            if item_id is None or item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            img_path = minimal.get("image_path")
            image_url = None
            image_id = None
            if img_path:
                if img_path.startswith("encrypted://"):
                    image_id = img_path.replace("encrypted://", "")
                    image_url = f"{request.base_url}images/{image_id}".rstrip("/") if request else f"/images/{image_id}"
                else:
                    filename_only = os.path.basename(img_path)
                    base = str(request.base_url).rstrip("/") if request else ""
                    image_url = f"{base}/uploads/{filename_only}" if base else f"/uploads/{filename_only}"
            
            normalized_items.append({
                "id": item_id,
                "type": minimal.get("type"),
                "category": minimal.get("category"),
                "color_primary": minimal.get("color"),
                "color_secondary": None,
                "pattern": minimal.get("pattern"),
                "season": None,
                "image_path": img_path,
                "image_url": image_url,
                "image_id": image_id
            })
    
    return {
        "user_id": user_id,
        "total_items": len(normalized_items),
        "items": normalized_items
    }

@app.get("/users/{user_id}/outfits/recommend")
@limiter.limit("10/minute")
async def recommend_outfits(
    request: Request,
    user_id: int,
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Generate outfit recommendations for user based on their wardrobe"""
    verify_user_ownership(user_id, current_user_id)
    
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.body_shape or not user.undertone:
        raise HTTPException(
            status_code=400,
            detail="User profile not analyzed. Please analyze user first with /users/{user_id}/analyze"
        )
    
    wardrobe_items = crud.get_user_wardrobe(db, user_id)
    
    if len(wardrobe_items) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough items in wardrobe. Add at least 2 items to generate outfits."
        )
    
    recommendations = get_outfit_recommendations(
        wardrobe_items=wardrobe_items,
        user_body_shape=user.body_shape,
        user_undertone=user.undertone,
        occasion=occasion,
        season=season,
        limit=limit
    )
    
    return {
        "user_id": user_id,
        "body_shape": user.body_shape,
        "undertone": user.undertone,
        "total_wardrobe_items": len(wardrobe_items),
        "recommended_outfits": recommendations,
        "total_recommendations": len(recommendations)
    }

@app.get("/users/{user_id}/wardrobe/discard-recommendations")
@limiter.limit("10/minute")
async def get_discard_suggestions(
    request: Request,
    user_id: int,
    threshold: float = 0.5,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """
    Analyze wardrobe and suggest items to discard based on:
    - Undertone compatibility (30%)
    - Body shape flattering (40%)
    - Versatility/outfit potential (30%)
    """
    verify_user_ownership(user_id, current_user_id)
    
    if threshold < 0 or threshold > 1:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 1")
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.body_shape or not user.undertone:
        raise HTTPException(
            status_code=400,
            detail="User profile not analyzed. Please analyze user first."
        )
    
    wardrobe_items = crud.get_user_wardrobe(db, user_id)
    
    if not wardrobe_items:
        raise HTTPException(
            status_code=400,
            detail="No items in wardrobe."
        )
    
    recommendations = get_discard_recommendations(
        wardrobe_items=wardrobe_items,
        user_body_shape=user.body_shape,
        user_undertone=user.undertone,
        discard_threshold=threshold
    )
    
    return {
        "user_id": user_id,
        "body_shape": user.body_shape,
        "undertone": user.undertone,
        "analysis": recommendations,
        "recommendation": recommendations["summary"]
    }

@app.post("/users/{user_id}/shopping/analyze")
@limiter.limit("10/minute")
async def analyze_shopping_item_endpoint(
    request: Request,
    user_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """
    Analyze a clothing item the user is considering buying.
    Provides compatibility check with wardrobe and purchase recommendation.
    """
    verify_user_ownership(user_id, current_user_id)
    validate_file_size(image)
    validate_file_type(image)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.body_shape or not user.undertone:
        raise HTTPException(
            status_code=400,
            detail="User profile not analyzed. Please analyze user first."
        )
    
    wardrobe_items = crud.get_user_wardrobe(db, user_id)
    
    image_bytes = await image.read()
    np_array = np.frombuffer(image_bytes, np.uint8)
    image_array = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    if image_array is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    analysis = analyze_shopping_item(
        image=image_array,
        wardrobe_items=wardrobe_items,
        user_body_shape=user.body_shape,
        user_undertone=user.undertone
    )
    
    return {
        "user_id": user_id,
        "analysis": analysis,
        "summary": f"Recommendation: {analysis['recommendation'].upper()}"
    }

@app.delete("/users/{user_id}/wardrobe/{item_id}")
@limiter.limit("20/minute")
async def delete_wardrobe_item_endpoint(
    request: Request,
    user_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Delete a wardrobe item and its uploaded image file"""
    verify_user_ownership(user_id, current_user_id)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    item = db.query(models.WardrobeItem).filter(
        models.WardrobeItem.id == item_id,
        models.WardrobeItem.user_id == user_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wardrobe item not found")

    image_path = getattr(item, "image_path", None)

    try:
        deleted = crud.delete_wardrobe_item(db, item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")

    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete wardrobe item")

    try:
        if image_path:
            if os.path.isabs(image_path):
                p = image_path
            else:
                p = os.path.join(UPLOAD_DIR, os.path.basename(image_path))
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        pass

    return {"message": "Wardrobe item deleted", "item_id": item_id}


# ============ FEEDBACK & LEARNING ENDPOINTS ============

@app.post("/users/{user_id}/outfits/{outfit_id}/rate")
async def rate_outfit(
    user_id: int,
    outfit_id: int,
    rating: int,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Rate an outfit (1-5 scale) to improve recommendations"""
    verify_user_ownership(user_id, current_user_id)
    
    try:
        outfit_rating = crud.create_outfit_rating(
            db=db,
            user_id=user_id,
            outfit_id=outfit_id,
            rating=rating,
            comment=comment,
            requester_id=current_user_id
        )
        return {
            "message": "Outfit rating recorded",
            "rating_id": outfit_rating.id,
            "outfit_id": outfit_id,
            "rating": outfit_rating.rating,
            "comment": outfit_rating.comment
        }
    except crud.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except crud.AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except crud.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/{user_id}/recommendations/{rec_type}/{rec_id}/feedback")
async def feedback_recommendation(
    user_id: int,
    rec_type: str,
    rec_id: str,
    helpful: bool,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """
    Mark a recommendation as helpful or not to train the system.
    rec_type: 'outfit', 'shopping', or 'discard'
    """
    verify_user_ownership(user_id, current_user_id)
    
    try:
        feedback = crud.create_recommendation_feedback(
            db=db,
            user_id=user_id,
            recommendation_type=rec_type,
            recommendation_id=rec_id,
            helpful=helpful,
            requester_id=current_user_id
        )
        return {
            "message": "Recommendation feedback recorded",
            "feedback_id": feedback.id,
            "recommendation_type": feedback.recommendation_type,
            "helpful": bool(feedback.helpful)
        }
    except crud.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except crud.AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except crud.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/{user_id}/wardrobe/{item_id}/usage")
async def track_item_usage(
    user_id: int,
    item_id: int,
    action: str,  # "kept", "discarded", "worn"
    wear_count: int = 1,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Track wardrobe item usage (worn, kept, discarded) to improve recommendations"""
    verify_user_ownership(user_id, current_user_id)
    
    try:
        usage = crud.create_item_usage(
            db=db,
            user_id=user_id,
            item_id=item_id,
            action=action,
            wear_count=wear_count,
            requester_id=current_user_id
        )
        return {
            "message": "Item usage tracked",
            "usage_id": usage.id,
            "item_id": item_id,
            "action": usage.action,
            "wear_count": usage.wear_count
        }
    except crud.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except crud.AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except crud.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ ADMIN METRICS ENDPOINTS ============

@app.get("/admin/metrics/models")
async def get_model_metrics_endpoint(
    model_name: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """
    Get model performance metrics over time.
    Admin endpoint - restricted to monitoring systems.
    """
    # Note: In production, add admin role check
    try:
        if model_name:
            metrics = crud.get_model_metrics(db, model_name, limit=limit)
            return {
                "model_name": model_name,
                "metrics": [
                    {
                        "id": m.id,
                        "metric_type": m.metric_type,
                        "value": m.value,
                        "version": m.version,
                        "evaluation_date": m.evaluation_date
                    }
                    for m in metrics
                ]
            }
        else:
            # Return all models
            all_models = ["color_harmony", "clothing_classifier", "body_shape"]
            result = {}
            for model in all_models:
                metrics = crud.get_model_metrics(db, model, limit=limit)
                result[model] = [
                    {
                        "metric_type": m.metric_type,
                        "value": m.value,
                        "version": m.version,
                        "evaluation_date": m.evaluation_date
                    }
                    for m in metrics
                ]
            return result
    except crud.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/metrics/feedback-volume")
async def get_feedback_volume(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    """Get feedback volume collected in the last N days"""
    # Note: In production, add admin role check
    try:
        feedback_data = crud.get_feedback_for_period(db, days=days)
        return {
            "period_days": days,
            "outfit_ratings": len(feedback_data["outfit_ratings"]),
            "recommendation_feedback": len(feedback_data["recommendation_feedback"]),
            "item_usage_tracking": len(feedback_data["item_usage"]),
            "total_feedback_points": feedback_data["total_feedback"],
            "cutoff_date": feedback_data["cutoff_date"]
        }
    except crud.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))