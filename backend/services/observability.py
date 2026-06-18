"""Structured logging helpers for production observability."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request


class JSONFormatter(logging.Formatter):
    """Format log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "error_type",
            "error_detail",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, default=str)


def setup_structured_logging(level: int = logging.INFO) -> None:
    """Configure root logging to emit JSON records to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    request_id: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    client_ip: Optional[str] = None,
    error_type: Optional[str] = None,
    error_detail: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """Emit a structured log entry."""
    logger.log(
        level,
        message or event,
        extra={
            "event": event,
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "error_type": error_type,
            "error_detail": error_detail,
        },
    )


def request_log_payload(
    request: Request, request_id: str, status_code: int, duration_ms: float
) -> Dict[str, Any]:
    """Build a reusable request log payload."""
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else None
    )
    return {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": client_ip,
    }
