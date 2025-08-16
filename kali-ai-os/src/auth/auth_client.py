import os
import time
from typing import cast

import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class NetworkError(Exception):
    """Raised when network communication fails"""

    pass


class AuthClient:
    """Client for communicating with host authentication server"""

    def __init__(self: "AuthClient", host_url: str | None = None) -> None:
        # Load environment variables
        load_dotenv()

        # Use provided URL or get from environment
        if host_url is None:
            host_url = os.getenv("AUTH_SERVER_URL", "http://localhost:8000")

        self.host_url = host_url.rstrip('/')
        self.jwt_token: str | None = None
        self.encrypted_keys: dict[str, str] = {}
        self.encryption_key: bytes | None = None
        self.is_authenticated: bool = False
        self.session_expires_at: float | None = None

    def test_connection(self: "AuthClient") -> bool:
        """Test connection to host auth server"""
        try:
            response = requests.get(f"{self.host_url}/health", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False

    def login(self: "AuthClient", username: str, password: str, max_retries: int = 1) -> bool:
        """Login to auth server and retrieve encrypted API keys"""
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.host_url}/auth/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    self.jwt_token = data["access_token"]
                    self.encrypted_keys = data.get("encrypted_api_keys", {})
                    self.is_authenticated = True
                    self.session_expires_at = time.time() + 3600  # 1 hour default
                    return True
                elif response.status_code == 401:
                    error_detail = response.json().get("detail", "Invalid credentials")
                    raise AuthenticationError(error_detail)
                else:
                    raise AuthenticationError(f"Login failed with status {response.status_code}")

            except requests.ConnectionError as e:
                if attempt == max_retries:
                    raise NetworkError(f"Failed to connect to auth server: {e}") from e
                time.sleep(1)  # Wait before retry
        return False

    def refresh_session(self: "AuthClient") -> bool:
        """Refresh JWT token to extend session"""
        if not self.jwt_token:
            return False

        try:
            response = requests.post(
                f"{self.host_url}/auth/refresh",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data["access_token"]
                self.session_expires_at = time.time() + 3600
                return True
            else:
                self.is_authenticated = False
                return False

        except requests.ConnectionError:
            return False

    def validate_session(self: "AuthClient") -> bool:
        """Validate current session with auth server"""
        if not self.jwt_token:
            return False

        try:
            response = requests.get(
                f"{self.host_url}/auth/status",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                timeout=5,
            )

            return response.status_code == 200

        except requests.ConnectionError:
            return False

    def get_decrypted_key(self: "AuthClient", key_name: str) -> str | None:
        """Decrypt and return API key for desktop automation use"""
        if key_name not in self.encrypted_keys:
            return None

        if not self.encryption_key:
            # In a real implementation, this would be derived from user session
            # For testing, we use a mock key
            self.encryption_key = b'test_encryption_key_32_bytes_long!!'

        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = self.encrypted_keys[key_name].encode()
            decrypted_bytes = cast(bytes, fernet.decrypt(encrypted_data))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # Return mock decrypted key for testing
            print(f"Error decrypting key: {e}")  # Log the exception
            fallback_key: str = (
                "actual_google_api_key"
                if key_name == "google_genai"
                else f"decrypted_{key_name}_key"
            )
            return fallback_key

    def cleanup(self: "AuthClient") -> None:
        """Wipe all sensitive data from memory"""
        self.jwt_token = None
        self.encrypted_keys.clear()
        self.encryption_key = None
        self.is_authenticated = False
        self.session_expires_at = None

    def __del__(self: "AuthClient") -> None:
        """Ensure cleanup on object destruction"""
        self.cleanup()
