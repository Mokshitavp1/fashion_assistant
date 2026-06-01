import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
import pymysql
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Use environment variable for database URL (secure)
# Fallback to localhost for local development only
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./backend/clothing_database.db"
)
ENVIRONMENT = os.getenv("ENV", "development").lower()
IS_DEV_ENV = ENVIRONMENT in {"dev", "development", "local", "test"}

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

if not IS_DEV_ENV and DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "SQLite is not supported in production. Set DATABASE_URL to a managed MySQL/PostgreSQL instance."
    )

def ensure_mysql_db_exists(db_url: str):
    """Only run this in development - production DBs should be managed by migrations"""
    if not db_url.startswith("mysql"):
        return
    parsed = urlparse(db_url.replace("+pymysql", ""))
    db_name = parsed.path.lstrip("/")
    try:
        conn = pymysql.connect(
            host=parsed.hostname or "localhost",
            user=parsed.username or "",
            password=parsed.password or "",
            port=parsed.port or 3306,
            database=None,
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
    except Exception as e:
        logger.warning("Could not create database", exc_info=e)

# Only create database in development/local environments
if IS_DEV_ENV:
    ensure_mysql_db_exists(DATABASE_URL)

# Create engine with dialect-specific options
if DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=DB_POOL_RECYCLE,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        connect_args={"charset": "utf8mb4"}
    )
elif DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=DB_POOL_RECYCLE,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
    )
else:
    sqlite_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, connect_args=sqlite_connect_args)


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
