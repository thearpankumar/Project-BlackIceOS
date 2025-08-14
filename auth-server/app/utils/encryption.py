import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import settings


class EncryptionManager:
    """Handle encryption and decryption of API keys and sensitive data"""

    def __init__(self, encryption_key: str | None = None):
        """
        Initialize encryption manager

        Args:
            encryption_key: Base64 encoded Fernet key. If None, uses settings.ENCRYPTION_KEY
        """
        self.encryption_key = encryption_key or settings.ENCRYPTION_KEY

        if not self.encryption_key:
            # Generate a key if none provided (for development/testing)
            if settings.DEBUG:
                self.encryption_key = self.generate_encryption_key()
            else:
                raise ValueError("ENCRYPTION_KEY must be provided in production")

        # Validate and initialize Fernet cipher
        try:
            self.cipher = Fernet(self.encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}") from e

    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a new Fernet encryption key

        Returns:
            str: Base64 encoded encryption key
        """
        key = Fernet.generate_key()
        return key.decode()

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes | None = None) -> str:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: Password to derive key from
            salt: Salt bytes. If None, generates random salt

        Returns:
            str: Base64 encoded derived key
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key for secure storage

        Args:
            api_key: Plain text API key (Groq or Google Generative AI)

        Returns:
            str: Base64 encoded encrypted API key

        Raises:
            ValueError: If encryption fails
        """
        try:
            # Convert API key to bytes
            api_key_bytes = api_key.encode("utf-8")

            # Encrypt using Fernet
            encrypted_bytes = self.cipher.encrypt(api_key_bytes)

            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode()

        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {e}") from e

    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """
        Decrypt an API key from storage

        Args:
            encrypted_api_key: Base64 encoded encrypted API key

        Returns:
            str: Plain text API key

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_api_key.encode())

            # Decrypt using Fernet
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)

            # Return as string
            return decrypted_bytes.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {e}") from e

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt arbitrary string data

        Args:
            data: Plain text data to encrypt

        Returns:
            str: Base64 encoded encrypted data
        """
        return self.encrypt_api_key(data)  # Same process

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt arbitrary string data

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            str: Plain text data
        """
        return self.decrypt_api_key(encrypted_data)  # Same process

    def encrypt_groq_key(self, groq_key: str) -> str:
        """
        Encrypt Groq API key with validation

        Args:
            groq_key: Groq API key (should start with 'gsk_')

        Returns:
            str: Encrypted API key

        Raises:
            ValueError: If key format is invalid
        """
        # Validate Groq key format
        if not groq_key.startswith("gsk_"):
            raise ValueError("Invalid Groq API key format (should start with 'gsk_')")

        return self.encrypt_api_key(groq_key)

    def encrypt_google_genai_key(self, google_key: str) -> str:
        """
        Encrypt Google Generative AI API key with validation

        Args:
            google_key: Google Generative AI API key (should start with 'AIza')

        Returns:
            str: Encrypted API key

        Raises:
            ValueError: If key format is invalid
        """
        # Validate Google Generative AI key format
        if not google_key.startswith("AIza"):
            raise ValueError(
                "Invalid Google Generative AI API key format (should start with 'AIza')"
            )

        return self.encrypt_api_key(google_key)

    def validate_api_key_format(self, api_key: str, provider: str) -> bool:
        """
        Validate API key format for specific provider

        Args:
            api_key: API key to validate
            provider: Provider name ('groq' or 'google_genai')

        Returns:
            bool: True if format is valid
        """
        if provider == "groq":
            return api_key.startswith("gsk_") and len(api_key) > 10
        elif provider == "google_genai":
            return api_key.startswith("AIza") and len(api_key) > 20
        else:
            return False

    def get_key_info(self) -> dict:
        """
        Get information about the encryption key (for debugging)

        Returns:
            dict: Key information (without revealing the actual key)
        """
        return {
            "key_length": len(self.encryption_key),
            "key_set": bool(self.encryption_key),
            "cipher_initialized": hasattr(self, "cipher"),
            "key_prefix": (
                self.encryption_key[:8] + "..." if self.encryption_key else None
            ),
        }


# Global encryption manager instance
encryption_manager = EncryptionManager()


# Convenience functions for backward compatibility
def generate_encryption_key() -> str:
    """Generate a new encryption key"""
    return EncryptionManager.generate_encryption_key()


def encrypt_api_key(api_key: str, encryption_key: str | None = None) -> str:
    """
    Encrypt an API key

    Args:
        api_key: Plain text API key
        encryption_key: Optional encryption key (uses global if None)

    Returns:
        str: Encrypted API key
    """
    if encryption_key:
        manager = EncryptionManager(encryption_key)
        return manager.encrypt_api_key(api_key)
    else:
        return encryption_manager.encrypt_api_key(api_key)


def decrypt_api_key(encrypted_api_key: str, encryption_key: str | None = None) -> str:
    """
    Decrypt an API key

    Args:
        encrypted_api_key: Encrypted API key
        encryption_key: Optional encryption key (uses global if None)

    Returns:
        str: Plain text API key
    """
    if encryption_key:
        manager = EncryptionManager(encryption_key)
        return manager.decrypt_api_key(encrypted_api_key)
    else:
        return encryption_manager.decrypt_api_key(encrypted_api_key)


def validate_groq_key(api_key: str) -> bool:
    """Validate Groq API key format"""
    return encryption_manager.validate_api_key_format(api_key, "groq")


def validate_google_genai_key(api_key: str) -> bool:
    """Validate Google Generative AI API key format"""
    return encryption_manager.validate_api_key_format(api_key, "google_genai")
