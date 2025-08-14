import os
import secrets
from typing import List, Optional


class Settings:
    """Application settings and configuration"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://kali_auth:password@localhost:5432/kali_auth_db"
    )
    
    # Redis Configuration (for session management)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(64))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    JWT_REFRESH_EXPIRATION_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "30"))
    
    # Encryption Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = []
    
    # Password Security
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGITS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: int = int(os.getenv("LOGIN_RATE_LIMIT", "5"))  # attempts per minute
    REGISTRATION_RATE_LIMIT: int = int(os.getenv("REGISTRATION_RATE_LIMIT", "3"))  # attempts per minute
    
    # API Key Configuration (for Groq and Google Generative AI)
    SUPPORTED_API_PROVIDERS: List[str] = ["groq", "google_genai"]
    
    # Session Configuration
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24
    MAX_SESSIONS_PER_USER: int = 5
    
    def __init__(self):
        """Initialize settings with environment variable parsing"""
        # Parse CORS origins from environment
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if origins_str:
            try:
                # Handle both JSON format and comma-separated
                if origins_str.startswith("["):
                    import json
                    self.ALLOWED_ORIGINS = json.loads(origins_str)
                else:
                    self.ALLOWED_ORIGINS = [origin.strip() for origin in origins_str.split(",")]
            except Exception:
                self.ALLOWED_ORIGINS = ["*"]  # Fallback to allow all
        else:
            self.ALLOWED_ORIGINS = ["*"]  # Default for development
        
        # Validate critical settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate critical configuration settings"""
        # Validate JWT secret key
        if len(self.JWT_SECRET_KEY) < 32:
            if not self.DEBUG:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        
        # Validate encryption key
        if not self.ENCRYPTION_KEY:
            if not self.DEBUG:
                raise ValueError("ENCRYPTION_KEY must be set in production")
        else:
            # Validate encryption key format (should be base64 encoded Fernet key)
            try:
                import base64
                from cryptography.fernet import Fernet
                # Test if it's a valid Fernet key
                Fernet(self.ENCRYPTION_KEY.encode())
            except Exception:
                if not self.DEBUG:
                    raise ValueError("ENCRYPTION_KEY must be a valid base64-encoded Fernet key")
        
        # Validate database URL
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")
        
        # Validate API providers
        if not all(provider in ["groq", "google_genai"] for provider in self.SUPPORTED_API_PROVIDERS):
            raise ValueError("Invalid API provider in SUPPORTED_API_PROVIDERS")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG and os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration for FastAPI"""
        return {
            "allow_origins": self.ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
        }
    
    def get_database_config(self) -> dict:
        """Get database configuration"""
        return {
            "url": self.DATABASE_URL,
            "echo": self.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings