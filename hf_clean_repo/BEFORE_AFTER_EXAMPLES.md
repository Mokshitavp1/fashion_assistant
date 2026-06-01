# Code Quality Refactoring - Before & After Examples

## Problem Examples & Solutions

### Example 1: Type Hints Missing

**BEFORE (main.py - 1770 lines)**
```python
def verify_token(credentials):
    if credentials is None:
        raise HTTPException(...)
    return decode_access_user_id(credentials.credentials)

def decode_access_user_id(token):
    try:
        payload = decode_token(token, expected_type="access")
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**AFTER (auth_utils.py + routers/auth.py)**
```python
# auth_utils.py - Full type hints
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

# routers/auth.py - Uses typed dependency
def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> int:
    """Verify JWT token and return user_id.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token invalid or missing
    """
    if credentials is None:
        raise HTTPException(...)
    return decode_access_user_id(credentials.credentials)
```

---

### Example 2: Configuration Scattered

**BEFORE (main.py)**
```python
# Lines 100-150: Configuration mixed with imports and functions
UPLOAD_DIR = "uploaded_images"
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FILE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")
EMAIL_VERIFICATION_REQUIRED = os.getenv("EMAIL_VERIFICATION_REQUIRED", "true").strip().lower() not in {"false", "0", "no", "off"}
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(...)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTES", "15"))
REFRESH_TOKEN_EXPIRATION_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))
# ... 30+ more configuration lines mixed with code
```

**AFTER (config.py - Clean & Organized)**
```python
"""Configuration and environment variables for the Fashion App API."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

# ============ CONFIGURATION ============

# File Upload Settings
UPLOAD_DIR: str = "uploaded_images"
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# CORS Settings
ALLOWED_ORIGINS: list = [
    origin.strip() for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
]

# Email Verification Settings
EMAIL_VERIFICATION_REQUIRED: bool = os.getenv(
    "EMAIL_VERIFICATION_REQUIRED", "true"
).strip().lower() not in {"false", "0", "no", "off"}

# JWT/Security Settings (with validation)
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY must be set and at least 32 characters long. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )

ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRATION_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTES", "15"))
REFRESH_TOKEN_EXPIRATION_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))
# ... all configuration in one place with type hints
```

---

### Example 3: Pydantic Models Scattered

**BEFORE (main.py - Lines 168-320)**
```python
# 16 Pydantic models scattered throughout main.py

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
    # ... more validators

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    # ...

class UserAnalyze(BaseModel):
    height: float
    weight: float
    # ...

# ... 13 more models scattered throughout
```

**AFTER (schemas.py - Organized & Complete)**
```python
"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""
    
    name: str
    email: EmailStr
    password: str
    
    @field_validator('name')
    def name_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if len(v.strip()) > 100:
            raise ValueError('Name must be less than 100 characters')
        return v.strip()

    @field_validator('password')
    def password_strength(cls, v: str) -> str:
        from auth_utils import validate_password
        validate_password(v)
        return v

    @field_validator('email')
    def gmail_only(cls, v: EmailStr) -> str:
        import re
        email = str(v).strip().lower()
        gmail_pattern = r'^[a-z0-9](?:[a-z0-9._%+-]{0,61}[a-z0-9])?@gmail\.com$'
        if not re.match(gmail_pattern, email):
            raise ValueError('Email not valid. Please use a real Gmail address.')
        if '..' in email.split('@', 1)[0]:
            raise ValueError('Email not valid. Please use a real Gmail address.')
        return email


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr
    password: str

    @field_validator('password')
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Password is required')
        return v


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    access_token_expires_in: int


# ... all 16 models organized with clear docstrings
```

---

### Example 4: Mixed Endpoint Logic

**BEFORE (main.py - All mixed together)**
```python
# Configuration + Models + Auth functions + Endpoints all in one file

# Line 100: Configuration
SECRET_KEY = os.getenv("SECRET_KEY")

# Line 168: Models
class UserCreate(BaseModel):
    ...

# Line 400: Database setup
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Line 500: Authentication functions
def validate_password(password):
    ...

def hash_password(password):
    ...

# Line 638: First endpoint
@app.post("/auth/register", response_model=RegisterResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    ...

# Line 683: Second endpoint
@app.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin, request: Request, db: Session = Depends(get_db)):
    ...

# ... more endpoints and utilities mixed throughout
```

**AFTER (Clean modular structure)**
```
config.py          # All configuration
    ↓
schemas.py         # All validation models
    ↓
auth_utils.py      # All auth utilities
    ↓
routers/auth.py    # All auth endpoints
    ↓
main.py            # Clean orchestration
```

---

### Example 5: Function Dependency Tracking

**BEFORE (main.py - Hard to trace)**
```python
# Line 638: register() needs:
@app.post("/auth/register", response_model=RegisterResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user_data.email)  # Where defined?
    password_hash = hash_password(user_data.password)             # Line 500?
    verification_token, token_hash, expires_at = create_email_verification_token()  # Line 520?
    new_user = crud.create_user(...)                              # database/crud.py
    send_verification_code_email(user_data.email, verification_token)  # Line 530?
    # ... mixed with 1000+ other functions throughout file

# Hard to tell which functions are used where
# Hard to reuse functions across routers
# Hard to test individual functions
```

**AFTER (Clear organization)**
```python
# routers/auth.py imports what it needs

from schemas import UserCreate, RegisterResponse          # schemas.py
from auth_utils import (                                  # auth_utils.py
    hash_password,
    verify_password,
    create_email_verification_token,
    send_verification_code_email,
)
from database import crud                                 # database/crud.py
from utils import audit_auth_event, verify_user_ownership  # utils.py

@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
) -> RegisterResponse:
    """Register a new user.
    
    Dependencies:
    - schemas.UserCreate: Request validation
    - auth_utils.hash_password: Password hashing
    - auth_utils.create_email_verification_token: Token generation
    - auth_utils.send_verification_code_email: Email sending
    - database.crud.create_user: User creation
    - utils.audit_auth_event: Audit logging
    """
    # ... implementation

# Clear imports at top
# Easy to understand dependencies
# Easy to mock for testing
# Easy to reuse functions
```

---

## Migration Commands

### Backup & Test
```bash
# Backup original
cp backend/main.py backend/main_original_backup.py

# Run existing tests on original
pytest backend/tests/ -v

# View test results
cat backend/pytest.ini  # Shows which tests were ignored
```

### Switch to Refactored
```bash
# Option 1: Gradual (auth only)
python -c "
import sys
sys.path.insert(0, 'backend')
from main_refactored import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post('/auth/register', json={
    'name': 'Test',
    'email': 'test@gmail.com',
    'password': 'TestPass123'
})
print(f'Auth endpoints working: {response.status_code == 200}')
"

# Option 2: Full switch (after all routers implemented)
mv backend/main.py backend/main_original_backup.py
mv backend/main_refactored.py backend/main.py
pytest backend/tests/ --cov=backend
```

---

## Importing Pattern Changes

### For developers extending the code:

**OLD:** Hard to find where things are
```python
# Where do I import UserCreate from?
from main import UserCreate  # Had to search 1770 lines

# Where is verify_password?
from main import verify_password  # Buried in 1770 lines

# Where are the endpoints?
# Searching 1770 lines...
```

**NEW:** Clear import locations
```python
# Request/response models
from schemas import UserCreate, TokenResponse

# Authentication utilities
from auth_utils import verify_password, hash_password

# Shared utilities
from utils import verify_user_ownership, audit_auth_event

# Database operations
from database import crud

# Routers
from routers import auth, wardrobe, analysis

# Configuration
from config import SECRET_KEY, MAX_FILE_SIZE
```

---

## Testing Pattern Changes

### OLD: Difficult to test
```python
# Had to import everything from monolithic main.py
from main import app, verify_token, hash_password, validate_file_size
# Heavy imports, testing one function meant loading entire monolith
```

### NEW: Easy to test individual components
```python
# Test utility functions in isolation
from auth_utils import verify_password, hash_password
from utils import validate_file_size

def test_verify_password():
    hash_val = hash_password("TestPass123")
    assert verify_password("TestPass123", hash_val) == True
    assert verify_password("WrongPass", hash_val) == False

# Test routers independently
from fastapi.testclient import TestClient
from routers import auth

# Create test app with just auth router
test_app = FastAPI()
test_app.include_router(auth.router)
client = TestClient(test_app)

def test_register():
    response = client.post("/auth/register", json={...})
    assert response.status_code == 200
```

---

## Architecture Visualization

### BEFORE (Monolithic)
```
┌─────────────────────────────────────────────┐
│              main.py (1770 lines)           │
├─────────────────────────────────────────────┤
│ - All imports (50+ lines)                   │
│ - All configuration (100+ lines)            │
│ - All models (150+ lines)                   │
│ - All auth utilities (200+ lines)           │
│ - All endpoints (50+ endpoints, 900+ lines) │
│ - All utility functions (200+ lines)        │
│ - Database setup, middleware, etc.          │
│                                             │
│ Result: Hard to navigate, test, maintain   │
└─────────────────────────────────────────────┘
```

### AFTER (Modular)
```
config.py (86 lines)
├─ All configuration constants
├─ Centralized and typed
└─ Easy to override per environment

schemas.py (191 lines)
├─ 16 Pydantic models
├─ Request/response validation
└─ Clear API contracts

auth_utils.py (266 lines)
├─ Password operations
├─ Token operations
├─ Email operations
└─ Testable in isolation

utils.py (156 lines)
├─ Shared utilities
├─ Validation helpers
├─ Logging helpers
└─ Used across all routers

routers/auth.py (386 lines)
├─ 11 auth endpoints
├─ Focused and testable
└─ Clear responsibility

routers/*.py (multiple)
└─ Other domain-specific endpoints

main.py (110 lines)
├─ Just orchestration
├─ Clean and readable
└─ Easy to add/remove routers

Result: Easy to navigate, test, maintain, extend
```

---

This refactoring transforms the codebase from a difficult-to-maintain monolith into a clean, organized, and scalable architecture!
