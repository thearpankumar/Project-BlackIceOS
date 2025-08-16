from unittest.mock import Mock, patch

import pytest

from src.auth.auth_client import AuthClient


class TestAuthClient:
    """Test suite for desktop automation auth integration"""

    @pytest.fixture
    def auth_client(self):
        """Create auth client for testing"""
        return AuthClient(host_url="http://192.168.1.100:8000")

    def test_memory_key_storage_only(self, auth_client):
        """Test API keys are stored in memory only, never written to disk"""
        # Simulate receiving encrypted keys
        auth_client.encrypted_keys = {
            "google_genai": "encrypted_google_key_data",
            "groq": "encrypted_groq_key_data",
        }

        # Keys should be accessible in memory
        assert len(auth_client.encrypted_keys) == 2
        assert "google_genai" in auth_client.encrypted_keys

        # Should never attempt to write to disk
        with patch('builtins.open') as mock_open:
            auth_client.get_decrypted_key("google_genai")
            mock_open.assert_not_called()

    def test_automatic_cleanup_on_exit(self, auth_client):
        """Test sensitive data is wiped when auth client exits"""
        # Set up authenticated state
        auth_client.encrypted_keys = {"google_genai": "encrypted_key"}
        auth_client.jwt_token = "test_jwt_token"  # noqa: S105
        auth_client.is_authenticated = True

        # Cleanup should wipe all sensitive data
        auth_client.cleanup()

        assert auth_client.encrypted_keys == {}
        assert auth_client.jwt_token is None
        assert auth_client.is_authenticated is False

    def test_key_decryption_for_desktop_automation(self, auth_client):
        """Test decrypted keys can be used for desktop automation commands"""
        # Mock encrypted key and decryption
        auth_client.encrypted_keys = {"google_genai": "encrypted_key_data"}

        with patch('cryptography.fernet.Fernet') as mock_fernet:
            mock_fernet_instance = Mock()
            mock_fernet_instance.decrypt.return_value = b"actual_google_api_key"
            mock_fernet.return_value = mock_fernet_instance

            # Should successfully decrypt key for use
            decrypted_key = auth_client.get_decrypted_key("google_genai")

            assert decrypted_key == "actual_google_api_key"
            # Key should be ready for desktop automation AI processing
            assert isinstance(decrypted_key, str)
            assert len(decrypted_key) > 0
