"""Shared utility functions."""

from typing import Any, Dict, Union

from fastapi import HTTPException, Request
from slowapi.util import get_remote_address as slowapi_get_remote_address
import jwt
from config import SECRET_KEY, ALGORITHM
import logging

logger = logging.getLogger(__name__)


def get_remote_address(request: Request) -> str:
    """Get remote address from request, preferring X-Forwarded-For header.
    
    Args:
        request: FastAPI request
        
    Returns:
        Remote IP address
    """
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    
    return slowapi_get_remote_address(request)


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key, preferring authenticated user over IP.
    
    Args:
        request: FastAPI request
        
    Returns:
        Rate limit key
    """
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


def to_json_compatible(value: Any) -> Any:
    """Convert numpy/scalar container values into JSON-serializable Python values.
    
    Args:
        value: Value to convert
        
    Returns:
        JSON-compatible value
    """
    import numpy as np
    
    if isinstance(value, dict):
        return {k: to_json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_compatible(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def audit_auth_event(
    event: str,
    request: Request,
    outcome: str,
    user_id: int | None = None,
    email: str | None = None,
    detail: str | None = None,
) -> None:
    """Log structured auth audit event.
    
    Args:
        event: Event name (e.g., 'login', 'register')
        request: FastAPI request
        outcome: 'success' or 'failure'
        user_id: User ID (optional)
        email: Email address (optional)
        detail: Additional detail (optional)
    """
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


def verify_user_ownership(user_id: int, current_user_id: int) -> None:
    """Verify that user has access to target user's data.
    
    Args:
        user_id: Target user ID
        current_user_id: Current authenticated user ID
        
    Raises:
        HTTPException: If user doesn't own the resource
    """
    from fastapi import HTTPException
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")


def validate_file_size(file: Any, max_size: int = 5 * 1024 * 1024) -> None:
    """Validate uploaded file size.
    
    Args:
        file: Uploaded file object
        max_size: Maximum allowed size in bytes
        
    Raises:
        HTTPException: If file is too large
    """
    from fastapi import HTTPException
    
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {max_size // (1024*1024)}MB"
        )


def validate_file_type(file: Any, allowed_extensions: set = None) -> None:
    """Validate uploaded file type.
    
    Args:
        file: Uploaded file object
        allowed_extensions: Set of allowed file extensions
        
    Raises:
        HTTPException: If file type not allowed
    """
    from fastapi import HTTPException
    import os
    
    if allowed_extensions is None:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
        )


async def run_bounded_image_job(job_name: str, func, *args, **kwargs) -> Any:
    """Run CPU-heavy image work in a bounded worker pool.
    
    Args:
        job_name: Name of the job for logging
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    from config import MAX_CONCURRENT_IMAGE_JOBS
    import asyncio
    from fastapi.concurrency import run_in_threadpool
    
    acquire_timeout_seconds = float(kwargs.pop("acquire_timeout_seconds", 0.2))
    
    semaphore = getattr(run_bounded_image_job, '_semaphore', None)
    if semaphore is None:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGE_JOBS)
        run_bounded_image_job._semaphore = semaphore
    
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=acquire_timeout_seconds)
    except asyncio.TimeoutError as exc:
        logger.warning("Service busy for image job: %s", job_name)
        raise HTTPException(
            status_code=503,
            detail="Service is busy processing other image jobs. Please retry shortly.",
            headers={"Retry-After": "5"},
        ) from exc

    try:
        logger.debug("Starting image job: %s", job_name)
        return await run_in_threadpool(func, *args, **kwargs)
    finally:
        semaphore.release()
        logger.debug("Finished image job: %s", job_name)
