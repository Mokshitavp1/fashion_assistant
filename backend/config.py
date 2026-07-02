"""Configuration and environment variables for the Fashion App API."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env regardless of the launch directory
load_dotenv(Path(__file__).resolve().with_name(".env"))

# ============ CONFIGURATION ============

# File Upload Settings
UPLOAD_DIR: str = "uploaded_images"
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# CORS Settings
ALLOWED_ORIGINS: list = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]

# Email Verification Settings
EMAIL_VERIFICATION_REQUIRED: bool = os.getenv(
    "EMAIL_VERIFICATION_REQUIRED", "true"
).strip().lower() not in {"false", "0", "no", "off"}

# JWT/Security Settings
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY must be set and at least 32 characters long. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )

ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRATION_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRATION_DAYS: int = int(
    os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7")
)
PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES: int = int(
    os.getenv("PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES", "30")
)
EMAIL_VERIFICATION_EXPIRATION_HOURS: int = int(
    os.getenv("EMAIL_VERIFICATION_EXPIRATION_HOURS", "24")
)
PBKDF2_ITERATIONS: int = int(os.getenv("PBKDF2_ITERATIONS", "310000"))

# Environment Settings
ENVIRONMENT: str = os.getenv("ENV", "development").lower()
IS_DEV_ENV: bool = ENVIRONMENT in {"dev", "development", "local"}

# SMTP Settings
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_ADDRESS: str = os.getenv("SMTP_FROM_ADDRESS", SMTP_USERNAME).strip()
SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Inference/Worker Settings
MAX_CONCURRENT_IMAGE_JOBS: int = int(os.getenv("MAX_CONCURRENT_IMAGE_JOBS", "4"))
INFERENCE_QUEUE_ENABLED: bool = os.getenv(
    "INFERENCE_QUEUE_ENABLED",
    "false" if IS_DEV_ENV else "true",
).strip().lower() in {"1", "true", "yes", "on"}
