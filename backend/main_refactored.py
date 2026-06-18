"""Fashion App API - Main application entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy import String, inspect, text

from database.database import engine
from database import models
from config import ALLOWED_ORIGINS, ALGORITHM, SECRET_KEY
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from utils import get_rate_limit_key

# Import routers
from routers import auth

logger = logging.getLogger(__name__)

# ============ SETUP ============

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize database
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

    if "password_hash" not in users_columns:
        with engine.begin() as connection:
            if engine.dialect.name == "sqlite":
                connection.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT '' NOT NULL"
                    )
                )
            else:
                connection.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''"
                    )
                )

    user_alterations = []
    if "email_verified" not in users_columns:
        if engine.dialect.name == "sqlite":
            user_alterations.append(
                "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0"
            )
        else:
            user_alterations.append(
                "ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0"
            )
    if "email_verification_token_hash" not in users_columns:
        user_alterations.append(
            "ALTER TABLE users ADD COLUMN email_verification_token_hash VARCHAR(255)"
        )
    if "email_verification_expires_at" not in users_columns:
        user_alterations.append(
            "ALTER TABLE users ADD COLUMN email_verification_expires_at DATETIME"
        )
    if "email_verified_at" not in users_columns:
        user_alterations.append(
            "ALTER TABLE users ADD COLUMN email_verified_at DATETIME"
        )

    if user_alterations:
        with engine.begin() as connection:
            for stmt in user_alterations:
                connection.execute(text(stmt))

    tables = set(inspector.get_table_names())
    if "refresh_tokens" not in tables:
        return

    refresh_columns = {
        column["name"] for column in inspector.get_columns("refresh_tokens")
    }
    alterations = []
    if "last_used_at" not in refresh_columns:
        alterations.append(
            "ALTER TABLE refresh_tokens ADD COLUMN last_used_at DATETIME"
        )
    if "user_agent" not in refresh_columns:
        alterations.append(
            "ALTER TABLE refresh_tokens ADD COLUMN user_agent VARCHAR(255)"
        )
    if "ip_address" not in refresh_columns:
        alterations.append(
            "ALTER TABLE refresh_tokens ADD COLUMN ip_address VARCHAR(64)"
        )
    if "revoked_reason" not in refresh_columns:
        alterations.append(
            "ALTER TABLE refresh_tokens ADD COLUMN revoked_reason VARCHAR(100)"
        )

    if alterations:
        with engine.begin() as connection:
            for stmt in alterations:
                connection.execute(text(stmt))


ensure_auth_schema()

# ============ APP SETUP ============

app = FastAPI(
    title="Fashion App API",
    version="1.0.0",
    description="AI-powered fashion recommendation and wardrobe management API",
)

# Rate limiting
limiter = Limiter(key_func=get_rate_limit_key)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ============ ROUTE REGISTRATION ============

# Include routers
app.include_router(auth.router)

# Additional routers to be imported as they're created:
# from routers import wardrobe, analysis, user, images, jobs, feedback
# app.include_router(wardrobe.router)
# app.include_router(analysis.router)
# app.include_router(user.router)
# app.include_router(images.router)
# app.include_router(jobs.router)
# app.include_router(feedback.router)

# ============ HEALTH CHECK ============


@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# ============ STARTUP/SHUTDOWN ============


@app.on_event("startup")
async def startup_event() -> None:
    """Run on application startup."""
    logger.info("Fashion App API starting up...")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run on application shutdown."""
    logger.info("Fashion App API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
