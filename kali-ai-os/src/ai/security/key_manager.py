import time
from typing import Optional
from cryptography.fernet import Fernet

class APIKeyManager:
    def __init__(self):
        self.keys = {}  # Memory-only storage
        self.key_expiry = {}
        self.encryption_key = None

    def store_encrypted_keys(self, encrypted_keys: str, encryption_key: bytes):
        self.encryption_key = encryption_key
        fernet = Fernet(encryption_key)
        decrypted_data = fernet.decrypt(encrypted_keys.encode())
        import json
        self.keys = json.loads(decrypted_data.decode())
        expiry_time = time.time() + (24 * 60 * 60)
        for key_name in self.keys:
            self.key_expiry[key_name] = expiry_time

    def get_google_api_key(self) -> Optional[str]:
        return self._get_key('google_api_key')

    def get_groq_api_key(self) -> Optional[str]:
        return self._get_key('groq_api_key')

    def _get_key(self, key_name: str) -> Optional[str]:
        if key_name not in self.keys:
            return None
        if time.time() > self.key_expiry.get(key_name, 0):
            del self.keys[key_name]
            del self.key_expiry[key_name]
            return None
        return self.keys[key_name]

    def clear_keys(self):
        self.keys.clear()
        self.key_expiry.clear()
        self.encryption_key = None
