"""Database base configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
import logging
from typing import Generator
import os
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Database URL from settings
DATABASE_URL = settings.database_url

# Handle SQLite specific configurations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug_sql
    )
    
    # Enable WAL mode for SQLite for better concurrency
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if 'sqlite' in str(dbapi_connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        echo=settings.debug_sql
    )

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    Yields:
        Database session that automatically closes on completion.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    # Import all models to ensure they're registered
    from . import models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialization complete")


async def check_db_health() -> bool:
    """
    Check database connectivity and health.
    
    Returns:
        True if database is healthy, False otherwise.
    """
    try:
        with SessionLocal() as db:
            # Simple query to test connectivity
            db.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False