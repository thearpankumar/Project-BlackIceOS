from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from app.database.connection import get_database
from app.database.models import User, APIKey, Session as UserSession
from app.auth.models import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    APIKeyCreate, APIKeyResponse, APIKeyUpdate, APIKeyListResponse,
    PasswordChange, UserUpdate, SessionResponse, UserStatsResponse
)
from app.core.security import (
    create_access_token, verify_token, hash_password, verify_password
)
from app.utils.encryption import encrypt_api_key, decrypt_api_key
from app.auth.dependencies import get_current_user, get_current_active_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_database)):
    """
    Register a new user account
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If username or email already exists
    """
    logger.info(f"Registration attempt for username: {user_data.username}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")
        
        return UserResponse.from_orm(new_user)
    
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed for {user_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: UserLogin, 
    request: Request,
    db: Session = Depends(get_database)
):
    """
    Login user and return JWT token with encrypted API keys
    
    Args:
        credentials: User login credentials
        request: FastAPI request object (for IP and user agent)
        db: Database session
        
    Returns:
        TokenResponse: JWT token and encrypted API keys
        
    Raises:
        HTTPException: If credentials are invalid
    """
    logger.info(f"Login attempt for username: {credentials.username}")
    
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not user.is_active:
        logger.warning(f"Login failed - user not found or inactive: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Login failed - invalid password for: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    try:
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Generate JWT token
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(data=token_data)
        
        # Create session record
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Token expiration
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(session)
        
        # Get user's API keys (encrypted)
        api_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
        encrypted_keys = {}
        
        for key in api_keys:
            try:
                # Keys are already encrypted in database, just return them
                encrypted_keys[key.key_name] = key.encrypted_key
                # Update last_used timestamp
                key.last_used = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Failed to process API key {key.key_name} for user {user.id}: {e}")
        
        db.commit()
        
        logger.info(f"User logged in successfully: {user.username} (ID: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours in seconds
            user_id=user.id,
            username=user.username,
            encrypted_api_keys=encrypted_keys
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Login processing failed for {credentials.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: dict,
    db: Session = Depends(get_database)
):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_request: Contains refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access token
    """
    # Implementation for refresh token
    # This is a placeholder - full implementation would verify refresh token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token functionality not yet implemented"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User information
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Update user profile information
    
    Args:
        user_update: Updated user data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserResponse: Updated user information
    """
    try:
        if user_update.email:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == user_update.email,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered by another user"
                )
            
            current_user.email = user_update.email
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User profile updated: {current_user.username} (ID: {current_user.id})")
        
        return UserResponse.from_orm(current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Change user password
    
    Args:
        password_change: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    try:
        # Hash new password
        new_password_hash = hash_password(password_change.new_password)
        current_user.password_hash = new_password_hash
        
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.username} (ID: {current_user.id})")
        
        return {"message": "Password changed successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Password change failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Add or update an API key for the current user
    
    Args:
        api_key_data: API key information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyResponse: Created/updated API key information
    """
    try:
        # Check if API key for this provider already exists
        existing_key = db.query(APIKey).filter(
            APIKey.user_id == current_user.id,
            APIKey.key_name == api_key_data.key_name
        ).first()
        
        # Encrypt the API key
        encrypted_key = encrypt_api_key(api_key_data.api_key)
        
        if existing_key:
            # Update existing key
            existing_key.encrypted_key = encrypted_key
            existing_key.last_used = None  # Reset usage timestamp
            db.commit()
            db.refresh(existing_key)
            
            logger.info(f"API key updated for user {current_user.id}: {api_key_data.key_name}")
            
            return APIKeyResponse.from_orm(existing_key)
        else:
            # Create new API key
            new_api_key = APIKey(
                user_id=current_user.id,
                key_name=api_key_data.key_name,
                encrypted_key=encrypted_key
            )
            
            db.add(new_api_key)
            db.commit()
            db.refresh(new_api_key)
            
            logger.info(f"API key added for user {current_user.id}: {api_key_data.key_name}")
            
            return APIKeyResponse.from_orm(new_api_key)
    
    except Exception as e:
        db.rollback()
        logger.error(f"API key creation/update failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save API key"
        )


@router.get("/api-keys", response_model=APIKeyListResponse)
async def get_user_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Get all API keys for the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyListResponse: List of user's API keys
    """
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    return APIKeyListResponse(
        api_keys=[APIKeyResponse.from_orm(key) for key in api_keys],
        total_count=len(api_keys)
    )


@router.delete("/api-keys/{key_name}")
async def delete_api_key(
    key_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Delete an API key for the current user
    
    Args:
        key_name: Name of the API key to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
    """
    # Validate key name
    if key_name not in ["groq", "google_genai"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key name"
        )
    
    api_key = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.key_name == key_name
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_name}' not found"
        )
    
    try:
        db.delete(api_key)
        db.commit()
        
        logger.info(f"API key deleted for user {current_user.id}: {key_name}")
        
        return {"message": f"API key '{key_name}' deleted successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"API key deletion failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Get all active sessions for the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[SessionResponse]: List of user's sessions
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.expires_at > datetime.utcnow()
    ).order_by(UserSession.created_at.desc()).all()
    
    # Mark current session (this is simplified - in practice you'd compare tokens)
    session_responses = []
    for session in sessions:
        session_response = SessionResponse.from_orm(session)
        # You could implement logic to identify current session here
        session_response.is_current = False
        session_responses.append(session_response)
    
    return session_responses


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Revoke a specific session
    
    Args:
        session_id: ID of session to revoke
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
    """
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    try:
        db.delete(session)
        db.commit()
        
        logger.info(f"Session revoked for user {current_user.id}: session {session_id}")
        
        return {"message": "Session revoked successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Session revocation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """
    Get user statistics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserStatsResponse: User statistics
    """
    # Count API keys
    total_api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).count()
    
    # Count active sessions
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.expires_at > datetime.utcnow()
    ).count()
    
    # Check which API keys are configured
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    groq_configured = any(key.key_name == "groq" for key in api_keys)
    google_genai_configured = any(key.key_name == "google_genai" for key in api_keys)
    
    return UserStatsResponse(
        total_api_keys=total_api_keys,
        active_sessions=active_sessions,
        last_login=current_user.last_login,
        account_created=current_user.created_at,
        groq_key_configured=groq_configured,
        google_genai_key_configured=google_genai_configured
    )