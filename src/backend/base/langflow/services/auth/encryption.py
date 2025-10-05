"""Encryption utilities for sensitive data.

CRITICAL FIX #1 from Phase 4 Audit:
Implements encryption for SSO client secrets and other sensitive data.
"""

import os
from base64 import urlsafe_b64decode, urlsafe_b64encode

from cryptography.fernet import Fernet
from loguru import logger


class EncryptionService:
    """Service for encrypting/decrypting sensitive data.

    Uses Fernet (symmetric encryption) with AES-128 in CBC mode.
    Phase 4 Audit - Critical Fix #1: Client secret encryption
    """

    def __init__(self, key: bytes | None = None):
        """Initialize encryption service.

        Args:
            key: Encryption key (32 url-safe base64-encoded bytes).
                 If None, uses LANGFLOW_ENCRYPTION_KEY from environment.
        """
        if key is None:
            # Get key from environment
            key_str = os.getenv("LANGFLOW_ENCRYPTION_KEY")
            if not key_str:
                raise ValueError(
                    "LANGFLOW_ENCRYPTION_KEY environment variable not set. "
                    "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
            key = key_str.encode()

        try:
            self.fernet = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext

        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            return urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext

        try:
            encrypted_bytes = urlsafe_b64decode(ciphertext.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key.

        Returns:
            Base64-encoded 32-byte key suitable for Fernet
        """
        return Fernet.generate_key().decode()


# Global encryption service instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret (convenience function).

    Args:
        plaintext: Secret to encrypt

    Returns:
        Encrypted secret
    """
    return get_encryption_service().encrypt(plaintext)


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a secret (convenience function).

    Args:
        ciphertext: Encrypted secret

    Returns:
        Decrypted secret
    """
    return get_encryption_service().decrypt(ciphertext)
