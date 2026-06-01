"""Image handling and retrieval endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging

from database.database import SessionLocal
from auth_utils import decode_access_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["images"])


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Extract these endpoints from original main.py:
# - GET /images/{image_id}

# Implementation pattern:
# @router.get("/images/{image_id}")
# async def get_image(
#     image_id: str,
#     request: Request
# ) -> StreamingResponse:
#     """Retrieve encrypted user image."""
#     ...

# See REFACTORED_CODEBASE_GUIDE.md for implementation pattern
