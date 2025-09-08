"""Encryption utilities for sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handles encryption and decryption of sensitive data."""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            master_key: Master key for encryption. If None, will use environment variable.
        """
        if master_key is None:
            master_key = os.getenv("MASTER_ENCRYPTION_KEY")
            if not master_key:
                raise ValueError("No master encryption key provided")
        
        self.master_key = master_key.encode()
        self._fernet = None
    
    def _get_fernet(self, salt: Optional[bytes] = None) -> Fernet:
        """Get or create Fernet instance with derived key."""
        if salt is None:
            salt = b"dydx_trading_bot_salt"  # Static salt for simplicity
        
        # Derive key from master key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)
    
    def encrypt(self, data: str, salt: Optional[bytes] = None) -> str:
        """
        Encrypt a string.
        
        Args:
            data: String to encrypt
            salt: Optional salt for key derivation
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            fernet = self._get_fernet(salt)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str, salt: Optional[bytes] = None) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            salt: Optional salt for key derivation
            
        Returns:
            Decrypted string
        """
        try:
            fernet = self._get_fernet(salt)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_dict(self, data_dict: dict, salt: Optional[bytes] = None) -> dict:
        """
        Encrypt values in a dictionary.
        
        Args:
            data_dict: Dictionary with string values to encrypt
            salt: Optional salt for key derivation
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted_dict = {}
        for key, value in data_dict.items():
            if isinstance(value, str):
                encrypted_dict[key] = self.encrypt(value, salt)
            else:
                encrypted_dict[key] = value
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict: dict, salt: Optional[bytes] = None) -> dict:
        """
        Decrypt values in a dictionary.
        
        Args:
            encrypted_dict: Dictionary with encrypted string values
            salt: Optional salt for key derivation
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted_dict = {}
        for key, value in encrypted_dict.items():
            if isinstance(value, str):
                try:
                    decrypted_dict[key] = self.decrypt(value, salt)
                except Exception:
                    # If decryption fails, assume it's not encrypted
                    decrypted_dict[key] = value
            else:
                decrypted_dict[key] = value
        return decrypted_dict


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_sensitive_data(data: str) -> str:
    """Convenience function to encrypt sensitive data."""
    return get_encryption_manager().encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Convenience function to decrypt sensitive data."""
    return get_encryption_manager().decrypt(encrypted_data)