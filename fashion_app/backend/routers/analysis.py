"""User profile analysis endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database.database import SessionLocal
from database import crud
from schemas import UserAnalyze
from utils import verify_user_ownership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["analysis"])


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Extract these endpoints from original main.py:
# - POST /users/{user_id}/analyze
# - GET /users/{user_id}

# Implementation pattern:
# @router.post("/{user_id}/analyze")
# async def analyze_user(...) -> dict:
#     """Analyze user body shape and skin tone."""
#     ...

# See REFACTORED_CODEBASE_GUIDE.md for implementation pattern
