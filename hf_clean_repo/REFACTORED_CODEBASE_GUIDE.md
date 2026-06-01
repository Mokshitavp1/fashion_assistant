# Refactored Codebase Guide

## Quick Start

### File Organization
```
backend/
├── main.py                 # Refactored entry point (~110 lines)
├── config.py              # Configuration constants
├── schemas.py             # Pydantic validation models
├── auth_utils.py          # Authentication utilities
├── utils.py               # Shared utilities
├── routers/
│   ├── __init__.py
│   ├── auth.py           # ✅ Authentication endpoints (complete)
│   ├── wardrobe.py       # 🔄 Wardrobe endpoints (TODO)
│   ├── analysis.py       # 🔄 Analysis endpoints (TODO)
│   ├── user.py           # 🔄 User profile endpoints (TODO)
│   ├── images.py         # 🔄 Image endpoints (TODO)
│   ├── jobs.py           # 🔄 Job queue endpoints (TODO)
│   └── feedback.py       # 🔄 Feedback endpoints (TODO)
```

## Adding a New Endpoint

### Step 1: Define Schema (schemas.py)
```python
class YourRequestModel(BaseModel):
    field1: str
    field2: int
    
    @field_validator('field1')
    def validate_field1(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError('field1 is required')
        return v

class YourResponseModel(BaseModel):
    id: int
    field1: str
    field2: int
```

### Step 2: Create Router (routers/your_domain.py)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import SessionLocal

from schemas import YourRequestModel, YourResponseModel
from auth_utils import verify_token
from utils import verify_user_ownership

router = APIRouter(prefix="/your-domain", tags=["your-domain"])

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/items", response_model=YourResponseModel)
async def create_item(
    item_data: YourRequestModel,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> YourResponseModel:
    """Create a new item for the user.
    
    Args:
        item_data: Item creation data
        current_user_id: Current authenticated user
        db: Database session
        
    Returns:
        Created item data
    """
    # Your implementation here
    return YourResponseModel(...)
```

### Step 3: Register Router (main.py)
```python
from routers import auth, your_domain

app.include_router(auth.router)
app.include_router(your_domain.router)
```

## Type Hints Quick Reference

### Common patterns:
```python
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import Request

# Function with type hints
def my_function(
    param1: str,
    param2: int,
    param3: Optional[str] = None,
    db: Session = None
) -> Dict[str, Any]:
    """Function docstring."""
    pass

# Async function
async def my_async_function(
    request: Request,
    current_user_id: int = Depends(verify_token),
) -> List[Dict[str, Any]]:
    """Async function docstring."""
    pass

# Optional parameters
def optional_param(value: Optional[int] = None) -> Optional[str]:
    return str(value) if value else None
```

## Dependency Injection Pattern

All endpoints use FastAPI's dependency injection for:
1. **Database access:** `db: Session = Depends(get_db)`
2. **Authentication:** `current_user_id: int = Depends(verify_token)`
3. **Rate limiting:** `@limiter.limit("10/minute")`

```python
@router.get("/protected")
async def protected_endpoint(
    user_id: int,
    current_user_id: int = Depends(verify_token),  # Authentication
    db: Session = Depends(get_db),                  # Database
    request: Request = None                         # For auditing
) -> dict:
    verify_user_ownership(user_id, current_user_id)  # Authorization
    # Implementation
    return {"status": "ok"}
```

## Error Handling Pattern

All endpoints should follow this pattern:

```python
@router.post("/items")
async def create_item(
    data: YourModel,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
) -> dict:
    try:
        # Validate user ownership
        user = crud.get_user_by_id(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Your logic here
        result = crud.create_item(db, ...)
        
        # Audit log
        audit_auth_event("create_item", request, "success", user_id=current_user_id)
        
        return result
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Individual Router

```python
# test_routers/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register():
    response = client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@gmail.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@gmail.com"

def test_login():
    # Register first
    client.post("/auth/register", json={...})
    
    # Then test login
    response = client.post("/auth/login", json={
        "email": "test@gmail.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Importing Best Practices

### ✅ DO: Organize imports logically
```python
# External imports first
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# FastAPI imports
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

# Local imports
from config import SECRET_KEY, ALGORITHM
from schemas import UserCreate, UserResponse
from database.database import SessionLocal
from auth_utils import verify_password, create_access_token
```

### ❌ DON'T: Mix import styles
```python
# Avoid this
from auth_utils import (
    verify_password, create_access_token,
    hash_password, decode_token,
    create_email_verification_token, send_verification_code_email
)

# Better: Group related imports
from auth_utils import verify_password, create_access_token
from auth_utils import hash_password, decode_token
from auth_utils import create_email_verification_token, send_verification_code_email
```

## Module Responsibilities

### config.py
- Environment variable loading
- Configuration constants
- Settings validation

### schemas.py
- Request validation (BaseModel)
- Response models
- Field validators
- Pydantic configuration

### auth_utils.py
- Password hashing/verification
- JWT token creation/verification
- Email verification
- Session management

### utils.py
- Shared utility functions
- Validation helpers
- Logging/auditing
- Data transformation

### routers/<domain>.py
- Domain-specific endpoints
- Request handling
- Response formatting
- Error handling

## Common Utilities

### Verify User Ownership
```python
from utils import verify_user_ownership

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user_id: int = Depends(verify_token)
):
    verify_user_ownership(user_id, current_user_id)  # Raises 403 if not owner
    # ... rest of endpoint
```

### Validate File Upload
```python
from utils import validate_file_size, validate_file_type

@router.post("/upload")
async def upload(
    file: UploadFile = File(...)
):
    validate_file_size(file)  # Raises 413 if too large
    validate_file_type(file)  # Raises 415 if wrong type
    # ... rest of endpoint
```

### Async Image Processing
```python
from utils import run_bounded_image_job

result = await run_bounded_image_job(
    "image_analysis",
    analyze_image,
    image_array,
    user_id
)
```

### Audit Logging
```python
from utils import audit_auth_event

audit_auth_event(
    event="login",
    request=request,
    outcome="success",
    user_id=user.id,
    email=user.email
)
```

## Checklist for Adding New Router

- [ ] Create `/routers/your_domain.py`
- [ ] Define all schemas in `schemas.py`
- [ ] Add type hints to all functions
- [ ] Include comprehensive docstrings
- [ ] Use dependency injection for DB and auth
- [ ] Handle errors consistently
- [ ] Add audit logging for important events
- [ ] Register router in `main.py`
- [ ] Add unit tests in `tests/`
- [ ] Update API documentation

## Running the Refactored App

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run development server
cd backend
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## Debugging Tips

### Enable debug logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check database
```bash
cd backend
python -c "from database.database import SessionLocal; from database import crud; db = SessionLocal(); print(crud.get_user_by_id(db, 1))"
```

### Test endpoint directly
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@gmail.com","password":"SecurePass123"}'
```

### Use FastAPI interactive docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
