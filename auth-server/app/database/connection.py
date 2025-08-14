import logging
import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure logging
logger = logging.getLogger(__name__)

# Database URL from environment with fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://kali_auth:password@localhost:5432/kali_auth_db"
)

# Create engine with connection pooling and error handling
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        echo=os.getenv("DEBUG", "false").lower() == "true",
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    logger.info(
        f"Database engine created for: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}"
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> bool:
    """
    Create all database tables if they don't exist (fallback method)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from .models import Base

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def check_database_health() -> bool:
    """
    Check if database connection is healthy

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        db = SessionLocal()
        # Test basic query
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database connection information for monitoring

    Returns:
        dict: Database connection details
    """
    try:
        db = SessionLocal()

        # Get database version and basic info
        if "postgresql" in DATABASE_URL.lower():
            result = db.execute(text("SELECT version()")).fetchone()
            db_version = result[0] if result else "Unknown"
            db_type = "PostgreSQL"
        elif "sqlite" in DATABASE_URL.lower():
            result = db.execute(text("SELECT sqlite_version()")).fetchone()
            db_version = result[0] if result else "Unknown"
            db_type = "SQLite"
        else:
            db_version = "Unknown"
            db_type = "Unknown"

        # Get table count
        if "postgresql" in DATABASE_URL.lower():
            table_count_result = db.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
            ).fetchone()
        else:
            table_count_result = db.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            ).fetchone()

        table_count = table_count_result[0] if table_count_result else 0

        db.close()

        return {
            "type": db_type,
            "version": db_version,
            "table_count": table_count,
            "url_safe": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
            "healthy": True,
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "type": "Unknown",
            "version": "Unknown",
            "table_count": 0,
            "url_safe": "Unknown",
            "healthy": False,
            "error": str(e),
        }


def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions from database

    Returns:
        int: Number of expired sessions removed
    """
    try:
        from datetime import datetime

        from .models import Session as UserSession

        db = SessionLocal()

        # Delete expired sessions
        expired_count = (
            db.query(UserSession)
            .filter(UserSession.expires_at < datetime.utcnow())
            .count()
        )

        db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()

        db.commit()
        db.close()

        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")

        return expired_count
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
        return 0


def initialize_database() -> bool:
    """
    Initialize database with tables and default data

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create tables
        if not create_tables():
            return False

        # Clean up any expired sessions on startup
        cleanup_expired_sessions()

        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
