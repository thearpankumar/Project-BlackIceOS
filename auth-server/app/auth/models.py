from datetime import datetime

from pydantic import BaseModel, EmailStr, validator

from ..core.security import password_validator


class UserCreate(BaseModel):
    """Model for user registration"""
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        is_valid, errors = password_validator.validate_password(v)
        if not is_valid:
            raise ValueError('. '.join(errors))
        return v


class UserLogin(BaseModel):
    """Model for user login"""
    username: str
    password: str

    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Username is required')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password is required')
        return v


class UserResponse(BaseModel):
    """Model for user response (excludes sensitive data)"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Model for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: int
    username: str
    encrypted_api_keys: dict[str, str] = {}
    refresh_token: str | None = None


class RefreshTokenRequest(BaseModel):
    """Model for refresh token request"""
    refresh_token: str


class APIKeyCreate(BaseModel):
    """Model for adding new API key"""
    key_name: str
    api_key: str

    @validator('key_name')
    def validate_key_name(cls, v):
        valid_providers = ["groq", "google_genai"]
        if v not in valid_providers:
            raise ValueError(f'key_name must be one of: {", ".join(valid_providers)}')
        return v

    @validator('api_key')
    def validate_api_key_format(cls, v, values):
        if 'key_name' in values:
            key_name = values['key_name']
            if key_name == "groq" and not v.startswith('gsk_'):
                raise ValueError('Groq API key must start with "gsk_"')
            elif key_name == "google_genai" and not v.startswith('AIza'):
                raise ValueError('Google Generative AI API key must start with "AIza"')

        if len(v.strip()) < 10:
            raise ValueError('API key appears to be too short')

        return v.strip()


class APIKeyResponse(BaseModel):
    """Model for API key response (excludes the actual key)"""
    id: int
    key_name: str
    created_at: datetime
    last_used: datetime | None = None

    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    """Model for updating API key"""
    api_key: str

    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('API key appears to be too short')
        return v.strip()


class PasswordChange(BaseModel):
    """Model for password change"""
    current_password: str
    new_password: str

    @validator('current_password')
    def validate_current_password(cls, v):
        if not v:
            raise ValueError('Current password is required')
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, errors = password_validator.validate_password(v)
        if not is_valid:
            raise ValueError('. '.join(errors))
        return v


class UserUpdate(BaseModel):
    """Model for updating user profile"""
    email: EmailStr | None = None

    @validator('email', pre=True, always=True)
    def validate_email(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Email cannot be empty')
        return v


class SessionResponse(BaseModel):
    """Model for session information"""
    id: int
    created_at: datetime
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    is_current: bool = False

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Model for health check response"""
    status: str
    database: str
    version: str
    service: str
    timestamp: datetime
    uptime_seconds: int | None = None


class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str
    error_code: str | None = None
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "detail": "Authentication failed",
                "error_code": "AUTH_001",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Model for validation error responses"""
    detail: list[dict[str, str]]
    error_type: str = "validation_error"

    class Config:
        schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["password"],
                        "msg": "Password must be at least 8 characters long",
                        "type": "value_error"
                    }
                ],
                "error_type": "validation_error"
            }
        }


class APIKeyListResponse(BaseModel):
    """Model for list of API keys response"""
    api_keys: list[APIKeyResponse]
    total_count: int


class UserStatsResponse(BaseModel):
    """Model for user statistics"""
    total_api_keys: int
    active_sessions: int
    last_login: datetime | None = None
    account_created: datetime
    groq_key_configured: bool = False
    google_genai_key_configured: bool = False


class SystemStatsResponse(BaseModel):
    """Model for system statistics (admin only)"""
    total_users: int
    active_users: int
    total_api_keys: int
    total_sessions: int
    database_health: bool
    uptime_hours: float
