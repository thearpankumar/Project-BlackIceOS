import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.database.connection import get_database
from app.database.models import User

# Configure logging
logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_database)
) -> User:
    """
    Get current user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify JWT token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user:
            logger.warning(f"Token valid but user not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (ensures user is not disabled)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.username} (ID: {current_user.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return current_user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_database)
) -> User | None:
    """
    Get current user optionally (for endpoints that work with or without auth)
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin user privileges
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    # Check if user is admin (you can implement this based on your needs)
    # For now, we'll check if username is 'admin'
    if current_user.username != 'admin':
        logger.warning(f"Non-admin user attempted admin access: {current_user.username} (ID: {current_user.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def validate_api_key_access(
    key_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> bool:
    """
    Validate that user has access to specific API key
    
    Args:
        key_name: Name of API key to validate access for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user has access to the API key
        
    Raises:
        HTTPException: If user doesn't have access to the API key
    """
    from app.database.models import APIKey

    # Check if user has this API key
    api_key = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.key_name == key_name
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_name}' not found for user"
        )

    return True


class RateLimiter:
    """Simple rate limiter for authentication endpoints"""

    def __init__(self):
        self.attempts = {}  # In production, use Redis or similar

    def is_rate_limited(self, identifier: str, max_attempts: int, window_minutes: int) -> bool:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: IP address or username
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                attempt for attempt in self.attempts[identifier]
                if attempt > window_start
            ]

        # Check if rate limited
        if identifier in self.attempts:
            return len(self.attempts[identifier]) >= max_attempts

        return False

    def record_attempt(self, identifier: str):
        """Record a login attempt"""
        from datetime import datetime

        if identifier not in self.attempts:
            self.attempts[identifier] = []

        self.attempts[identifier].append(datetime.utcnow())


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_login_rate_limit(
    credentials: dict,
    request_ip: str = None
):
    """
    Check login rate limiting
    
    Args:
        credentials: Login credentials
        request_ip: Request IP address
        
    Raises:
        HTTPException: If rate limited
    """
    from app.core.config import settings

    # Check by username
    username = credentials.get("username", "")
    if rate_limiter.is_rate_limited(username, settings.LOGIN_RATE_LIMIT, 60):
        logger.warning(f"Login rate limit exceeded for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Check by IP
    if request_ip and rate_limiter.is_rate_limited(request_ip, settings.LOGIN_RATE_LIMIT * 2, 60):
        logger.warning(f"Login rate limit exceeded for IP: {request_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts from this IP. Please try again later."
        )

    # Record attempts
    rate_limiter.record_attempt(username)
    if request_ip:
        rate_limiter.record_attempt(request_ip)
