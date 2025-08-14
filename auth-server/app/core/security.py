from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status

from .config import settings


class SecurityManager:
    """Handle JWT tokens, password hashing, and security operations"""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS
        self.refresh_expiration_days = settings.JWT_REFRESH_EXPIRATION_DAYS

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """
        Create a JWT refresh token
        
        Args:
            data: Data to encode in token
            
        Returns:
            str: JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_expiration_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                )

            # Check expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    def get_token_payload(self, token: str) -> dict[str, Any] | None:
        """
        Get token payload without verification (for debugging)
        
        Args:
            token: JWT token
            
        Returns:
            Optional[Dict[str, Any]]: Token payload or None if invalid
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without raising exception
        
        Args:
            token: JWT token
            
        Returns:
            bool: True if expired, False if valid
        """
        try:
            payload = self.get_token_payload(token)
            if not payload:
                return True

            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.utcnow().timestamp() > exp_timestamp

            return True  # No expiration means invalid
        except Exception:
            return True


class PasswordValidator:
    """Validate password strength and security requirements"""

    def __init__(self):
        self.min_length = settings.MIN_PASSWORD_LENGTH
        self.require_uppercase = settings.REQUIRE_UPPERCASE
        self.require_lowercase = settings.REQUIRE_LOWERCASE
        self.require_digits = settings.REQUIRE_DIGITS
        self.require_special = settings.REQUIRE_SPECIAL_CHARS

    def validate_password(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password against security requirements
        
        Args:
            password: Password to validate
            
        Returns:
            tuple[bool, list[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        # Check uppercase
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        # Check lowercase
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        # Check digits
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        # Check special characters
        if self.require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessed")

        return len(errors) == 0, errors

    def get_password_strength_score(self, password: str) -> int:
        """
        Get password strength score (0-100)
        
        Args:
            password: Password to score
            
        Returns:
            int: Strength score (0=very weak, 100=very strong)
        """
        score = 0

        # Length scoring
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        # Character variety scoring
        if any(c.isupper() for c in password):
            score += 15
        if any(c.islower() for c in password):
            score += 15
        if any(c.isdigit() for c in password):
            score += 15
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15

        return min(score, 100)


# Global instances
security_manager = SecurityManager()
password_validator = PasswordValidator()


# Convenience functions for backward compatibility
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    return security_manager.create_access_token(data, expires_delta)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Verify JWT token"""
    return security_manager.verify_token(token, token_type)


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return security_manager.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return security_manager.verify_password(password, hashed_password)


def validate_password(password: str) -> tuple[bool, list[str]]:
    """Validate password strength"""
    return password_validator.validate_password(password)
