"""User profile endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import logging

from database.database import SessionLocal
from database import crud
from utils import verify_user_ownership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Extract user profile endpoints from original main.py
# Currently integrated into other routers

# See REFACTORED_CODEBASE_GUIDE.md for implementation pattern
