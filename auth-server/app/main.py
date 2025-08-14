import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import routes as auth_routes
from app.auth.models import HealthCheckResponse
from app.core.config import settings

# Import application components
from app.database.connection import (
    check_database_health,
    cleanup_expired_sessions,
    initialize_database,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Application startup time for uptime calculation
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management

    Handles startup and shutdown tasks:
    - Database initialization
    - Health checks
    - Cleanup tasks
    """
    # Startup tasks
    logger.info("Starting Kali AI-OS Authentication Server...")

    # Skip database initialization in test environment
    if settings.ENVIRONMENT != "test":
        try:
            # Initialize database (create tables if needed)
            if not initialize_database():
                logger.error("Database initialization failed")
                raise Exception("Cannot start server - database initialization failed")

            # Perform initial health check
            if not check_database_health():
                logger.error("Database health check failed")
                raise Exception("Cannot start server - database unavailable")

            # Clean up expired sessions on startup
            expired_count = cleanup_expired_sessions()
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions on startup")

            logger.info("Authentication server started successfully")
            logger.info(
                f"Server configuration: DEBUG={settings.DEBUG}, CORS={settings.ALLOWED_ORIGINS}"
            )

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise
    else:
        logger.info("Running in TEST environment, skipping database initialization")

    yield

    # Shutdown tasks
    logger.info("Shutting down authentication server...")

    if settings.ENVIRONMENT != "test":
        try:
            # Clean up expired sessions before shutdown
            expired_count = cleanup_expired_sessions()
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions on shutdown")

            logger.info("Authentication server shutdown completed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Kali AI-OS Authentication Server",
    description="Secure authentication and API key management for Kali AI-OS with support for Groq and Google Generative AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Hide docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# CORS middleware configuration
app.add_middleware(CORSMiddleware, **settings.get_cors_config())


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information"""
    start_time = time.time()

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}"
    )

    try:
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - ERROR - {process_time:.3f}s - {str(e)}"
        )
        raise


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    # Convert ValidationError details to JSON-serializable format
    errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": str(error.get("msg")),  # Convert to string
            "input": error.get("input"),
        }
        errors.append(serializable_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "error_type": "validation_error",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    logger.error(f"ValueError on {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_type": "value_error",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors"""
    logger.error(f"Internal server error on {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Comprehensive health check including database connectivity

    Returns:
        HealthCheckResponse: Server health status
    """
    db_healthy = check_database_health()
    uptime_seconds = int(time.time() - startup_time)

    return HealthCheckResponse(
        status="healthy" if db_healthy else "degraded",
        database="connected" if db_healthy else "disconnected",
        version="1.0.0",
        service="kali-ai-os-auth",
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime_seconds,
    )


# Database status endpoint
@app.get("/database/status")
async def database_status():
    """
    Check database connection status with detailed information

    Returns:
        dict: Database status and information
    """
    from app.database.connection import get_database_info

    db_info = get_database_info()

    return {
        "database_connected": db_info["healthy"],
        "database_type": db_info["type"],
        "database_version": db_info["version"],
        "table_count": db_info["table_count"],
        "status": "ok" if db_info["healthy"] else "error",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information

    Returns:
        dict: API information and available endpoints
    """
    return {
        "message": "Kali AI-OS Authentication Server",
        "version": "1.0.0",
        "description": "Secure authentication and API key management for Groq and Google Generative AI",
        "endpoints": {
            "health": "/health",
            "database_status": "/database/status",
            "register": "/auth/register",
            "login": "/auth/login",
            "user_profile": "/auth/me",
            "api_keys": "/auth/api-keys",
            "sessions": "/auth/sessions",
            "documentation": "/docs" if settings.DEBUG else None,
        },
        "supported_providers": ["groq", "google_genai"],
        "timestamp": datetime.utcnow().isoformat(),
    }


# System information endpoint (for monitoring)
@app.get("/system/info")
async def system_info():
    """
    System information endpoint for monitoring and debugging

    Returns:
        dict: System information
    """
    uptime_seconds = int(time.time() - startup_time)

    return {
        "service": "kali-ai-os-auth",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "debug_mode": settings.DEBUG,
        "database_type": (
            "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite"
        ),
        "supported_api_providers": settings.SUPPORTED_API_PROVIDERS,
        "cors_origins": (
            settings.ALLOWED_ORIGINS if settings.DEBUG else ["***"]
        ),  # Hide in production
        "timestamp": datetime.utcnow().isoformat(),
    }


# Include authentication routes
app.include_router(auth_routes.router, prefix="/auth", tags=["authentication"])


# Admin endpoints (if needed)
@app.get("/admin/stats")
async def admin_stats():
    """
    Admin statistics endpoint

    Returns:
        dict: System statistics (implement admin authentication as needed)
    """
    from app.database.connection import SessionLocal
    from app.database.models import APIKey
    from app.database.models import Session as UserSession
    from app.database.models import User

    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active).count()
        total_api_keys = db.query(APIKey).count()
        total_sessions = (
            db.query(UserSession)
            .filter(UserSession.expires_at > datetime.utcnow())
            .count()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_api_keys": total_api_keys,
            "active_sessions": total_sessions,
            "database_healthy": check_database_health(),
            "uptime_hours": (time.time() - startup_time) / 3600,
            "timestamp": datetime.utcnow().isoformat(),
        }

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn  # type: ignore

    # Run server
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
