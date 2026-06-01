"""Inference job queue endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import logging

from database.database import SessionLocal
from auth_utils import decode_access_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Extract these endpoints from original main.py:
# - GET /jobs/{job_id}

# Implementation pattern:
# @router.get("/jobs/{job_id}")
# async def get_inference_job(
#     job_id: str,
#     request: Request,
#     current_user_id: int = Depends(verify_token)
# ) -> dict:
#     """Get status and result of inference job."""
#     ...

# See REFACTORED_CODEBASE_GUIDE.md for implementation pattern
