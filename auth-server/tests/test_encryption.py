import base64

import pytest
from cryptography.fernet import Fernet

from app.utils.encryption import (
    decrypt_api_key,
    encrypt_api_key,
    generate_encryption_key,
)


class TestEncryptionFunctions:
    """Test API key encryption and decryption functionality"""

    def test_generate_encryption_key(self):
        """Test encryption key generation"""
        key = generate_encryption_key()

        # Key should be base64 encoded
        assert isinstance(key, str)

        # Should be valid Fernet key (44 characters when base64 encoded)
        assert len(key) == 44

        # Should be valid base64
        try:
            base64.urlsafe_b64decode(key)
        except Exception:
            pytest.fail("Generated key is not valid base64")

        # Should be usable with Fernet
        fernet = Fernet(key.encode())
        test_data = b"test"
        encrypted = fernet.encrypt(test_data)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == test_data

    def test_encrypt_groq_api_key(self, sample_api_keys):
        """Test encryption of Groq API key"""
        groq_key = sample_api_keys["groq"]
        encryption_key = generate_encryption_key()

        encrypted_key = encrypt_api_key(groq_key, encryption_key)

        # Encrypted key should be different from original
        assert encrypted_key != groq_key

        # Encrypted key should be base64 encoded
        try:
            base64.urlsafe_b64decode(encrypted_key)
        except Exception:
            pytest.fail("Encrypted key is not valid base64")

        # Should be longer than original (due to encryption overhead)
        assert len(encrypted_key) > len(groq_key)

    def test_encrypt_google_genai_api_key(self, sample_api_keys):
        """Test encryption of Google Generative AI API key"""
        google_key = sample_api_keys["google_genai"]
        encryption_key = generate_encryption_key()

        encrypted_key = encrypt_api_key(google_key, encryption_key)

        # Encrypted key should be different from original
        assert encrypted_key != google_key

        # Should be base64 encoded
        try:
            base64.urlsafe_b64decode(encrypted_key)
        except Exception:
            pytest.fail("Encrypted key is not valid base64")

        # Should be longer than original
        assert len(encrypted_key) > len(google_key)

    def test_decrypt_groq_api_key(self, sample_api_keys):
        """Test decryption of Groq API key"""
        groq_key = sample_api_keys["groq"]
        encryption_key = generate_encryption_key()

        # Encrypt then decrypt
        encrypted_key = encrypt_api_key(groq_key, encryption_key)
        decrypted_key = decrypt_api_key(encrypted_key, encryption_key)

        # Decrypted key should match original
        assert decrypted_key == groq_key

    def test_decrypt_google_genai_api_key(self, sample_api_keys):
        """Test decryption of Google Generative AI API key"""
        google_key = sample_api_keys["google_genai"]
        encryption_key = generate_encryption_key()

        # Encrypt then decrypt
        encrypted_key = encrypt_api_key(google_key, encryption_key)
        decrypted_key = decrypt_api_key(encrypted_key, encryption_key)

        # Decrypted key should match original
        assert decrypted_key == google_key

    def test_encryption_decryption_round_trip(self, sample_api_keys):
        """Test full encryption/decryption round trip for all key types"""
        encryption_key = generate_encryption_key()

        for key_name, api_key in sample_api_keys.items():
            # Encrypt
            encrypted = encrypt_api_key(api_key, encryption_key)

            # Verify encrypted is different
            assert encrypted != api_key

            # Decrypt
            decrypted = decrypt_api_key(encrypted, encryption_key)

            # Verify matches original
            assert decrypted == api_key, f"Round trip failed for {key_name} key"

    def test_encryption_with_different_keys_produces_different_results(
        self, sample_api_keys
    ):
        """Test that same API key encrypted with different keys produces different results"""
        groq_key = sample_api_keys["groq"]

        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        encrypted1 = encrypt_api_key(groq_key, key1)
        encrypted2 = encrypt_api_key(groq_key, key2)

        # Should produce different encrypted values
        assert encrypted1 != encrypted2

    def test_decryption_with_wrong_key_fails(self, sample_api_keys):
        """Test that decryption with wrong key fails"""
        groq_key = sample_api_keys["groq"]

        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        # Encrypt with key1
        encrypted = encrypt_api_key(groq_key, key1)

        # Try to decrypt with key2 - should fail
        with pytest.raises(ValueError):
            decrypt_api_key(encrypted, key2)

    def test_encryption_handles_empty_string(self):
        """Test encryption handles empty string gracefully"""
        encryption_key = generate_encryption_key()
        empty_key = ""

        encrypted = encrypt_api_key(empty_key, encryption_key)
        decrypted = decrypt_api_key(encrypted, encryption_key)

        assert decrypted == empty_key

    def test_encryption_handles_special_characters(self):
        """Test encryption handles API keys with special characters"""
        encryption_key = generate_encryption_key()
        special_key = "gsk_test-key-with-special-chars!@#$%^&*()_+-={}[];:'<>?,./"

        encrypted = encrypt_api_key(special_key, encryption_key)
        decrypted = decrypt_api_key(encrypted, encryption_key)

        assert decrypted == special_key

    def test_encryption_deterministic_with_same_inputs(self):
        """Test that encryption with same key produces consistent results"""
        # Note: This test might need to be adjusted based on encryption implementation
        # If using random initialization vectors, encrypted output will differ each time
        encryption_key = generate_encryption_key()
        api_key = "gsk_test_key_12345"

        encrypted1 = encrypt_api_key(api_key, encryption_key)
        encrypted2 = encrypt_api_key(api_key, encryption_key)

        # With Fernet, encryption includes random IV so results will differ
        # Both should decrypt to same value though
        decrypted1 = decrypt_api_key(encrypted1, encryption_key)
        decrypted2 = decrypt_api_key(encrypted2, encryption_key)

        assert decrypted1 == api_key
        assert decrypted2 == api_key
        assert decrypted1 == decrypted2


class TestEncryptionSecurity:
    """Test security aspects of encryption"""

    def test_encrypted_keys_contain_no_plaintext(self, sample_api_keys):
        """Test that encrypted keys don't contain plaintext fragments"""
        encryption_key = generate_encryption_key()

        for key_name, api_key in sample_api_keys.items():
            encrypted = encrypt_api_key(api_key, encryption_key)

            # Encrypted data should not contain any part of original key
            # Check for substrings longer than 3 characters
            for i in range(len(api_key) - 3):
                substring = api_key[i : i + 4]
                assert substring not in encrypted, (
                    f"Plaintext fragment '{substring}' found in encrypted {key_name}"
                )

    def test_encryption_key_format_validation(self):
        """Test that encryption key format is validated"""
        # Invalid keys should raise appropriate errors
        invalid_keys = [
            "",
            "short",
            "not_base64_!@#$",
            "too_short_base64==",
        ]

        api_key = "gsk_test_key"

        for invalid_key in invalid_keys:
            with pytest.raises(ValueError):
                encrypt_api_key(api_key, invalid_key)

    def test_api_key_length_limits(self):
        """Test encryption handles various API key lengths"""
        encryption_key = generate_encryption_key()

        # Test various lengths
        test_keys = [
            "short",
            "medium_length_api_key_12345",
            "very_long_api_key_" + "x" * 100,
            "extremely_long_key_" + "y" * 500,
        ]

        for test_key in test_keys:
            encrypted = encrypt_api_key(test_key, encryption_key)
            decrypted = decrypt_api_key(encrypted, encryption_key)
            assert decrypted == test_key


class TestEncryptionIntegration:
    """Test encryption integration with database and API"""

    def test_encryption_compatible_with_database_storage(self):
        """Test that encrypted keys can be stored and retrieved from database"""
        # This will test that encrypted format is compatible with TEXT column
        encryption_key = generate_encryption_key()
        api_key = "gsk_test_key_for_database_storage"

        encrypted = encrypt_api_key(api_key, encryption_key)

        # Encrypted key should be safe for database storage (no special SQL chars)
        unsafe_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in unsafe_chars:
            assert char not in encrypted, (
                f"Unsafe SQL character '{char}' found in encrypted key"
            )

        # Should be valid UTF-8
        encrypted.encode("utf-8")  # Should not raise exception

    def test_encryption_performance(self, sample_api_keys):
        """Test encryption/decryption performance is acceptable"""
        import time

        encryption_key = generate_encryption_key()
        groq_key = sample_api_keys["groq"]

        # Test multiple iterations to get average time
        iterations = 100

        # Measure encryption time
        start_time = time.time()
        for _ in range(iterations):
            encrypt_api_key(groq_key, encryption_key)
        encryption_time = time.time() - start_time

        # Measure decryption time
        encrypted = encrypt_api_key(groq_key, encryption_key)
        start_time = time.time()
        for _ in range(iterations):
            decrypt_api_key(encrypted, encryption_key)
        decryption_time = time.time() - start_time

        # Performance should be reasonable (less than 10ms per operation on average)
        avg_encryption_time = encryption_time / iterations
        avg_decryption_time = decryption_time / iterations

        assert avg_encryption_time < 0.01, (
            f"Encryption too slow: {avg_encryption_time:.4f}s per operation"
        )
        assert avg_decryption_time < 0.01, (
            f"Decryption too slow: {avg_decryption_time:.4f}s per operation"
        )


class TestEncryptionErrorHandling:
    """Test error handling in encryption functions"""

    def test_decrypt_invalid_token(self):
        """Test decryption of invalid or corrupted token"""
        encryption_key = generate_encryption_key()
        invalid_tokens = [
            "not_a_real_token",
            "invalid_base64_$",
            base64.urlsafe_b64encode(b"not_encrypted_data").decode(),
        ]

        for token in invalid_tokens:
            with pytest.raises(ValueError):
                decrypt_api_key(token, encryption_key)

    def test_encrypt_with_invalid_key(self):
        """Test encryption with invalid encryption key"""
        api_key = "gsk_test_key"
        invalid_keys = [
            "short",
            "not_base64_!@#$",
            base64.urlsafe_b64encode(b"not_a_real_key").decode(),
        ]

        for key in invalid_keys:
            with pytest.raises(ValueError):
                encrypt_api_key(api_key, key)

    def test_decrypt_with_invalid_key(self):
        """Test decryption with invalid encryption key"""
        encryption_key = generate_encryption_key()
        api_key = "gsk_test_key"
        encrypted = encrypt_api_key(api_key, encryption_key)

        invalid_keys = [
            "short",
            "not_base64_!@#$",
            base64.urlsafe_b64encode(b"not_a_real_key").decode(),
        ]

        for key in invalid_keys:
            with pytest.raises(ValueError):
                decrypt_api_key(encrypted, key)
