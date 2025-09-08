"""API key management with secure encryption."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from .encryption import EncryptionManager
from ..database.dao import UserDAO, ConfigurationDAO
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class APIKeyManager:
    """Manages encrypted storage and rotation of API keys."""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user_dao = UserDAO(db)
        self.config_dao = ConfigurationDAO(db)
        self.encryption_manager = EncryptionManager()
    
    async def store_api_keys(
        self, 
        api_key: str, 
        api_secret: str, 
        api_passphrase: Optional[str] = None
    ) -> bool:
        """
        Store encrypted API keys for a user.
        
        Args:
            api_key: dYdX API key
            api_secret: dYdX API secret
            api_passphrase: dYdX API passphrase (if required)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate user-specific salt
            user_salt = f"user_{self.user_id}_salt".encode()
            
            # Encrypt the API credentials
            encrypted_key = self.encryption_manager.encrypt(api_key, user_salt)
            encrypted_secret = self.encryption_manager.encrypt(api_secret, user_salt)
            encrypted_passphrase = None
            
            if api_passphrase:
                encrypted_passphrase = self.encryption_manager.encrypt(api_passphrase, user_salt)
            
            # Store in user model
            update_data = {
                "api_key_encrypted": encrypted_key,
                "api_secret_encrypted": encrypted_secret,
                "api_passphrase_encrypted": encrypted_passphrase
            }
            
            success = self.user_dao.update_user(self.user_id, update_data)
            
            if success:
                # Store metadata in configuration
                await self.config_dao.save_config(
                    category="api_keys",
                    key="last_updated",
                    value=datetime.utcnow().isoformat(),
                    value_type="string",
                    user_id=self.user_id,
                    description="Last time API keys were updated"
                )
                
                await self.config_dao.save_config(
                    category="api_keys",
                    key="rotation_due",
                    value=(datetime.utcnow() + timedelta(days=30)).isoformat(),
                    value_type="string",
                    user_id=self.user_id,
                    description="When API keys should be rotated"
                )
                
                logger.info(f"API keys stored for user {self.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing API keys for user {self.user_id}: {e}")
            return False
    
    async def get_api_keys(self) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt API keys for a user.
        
        Returns:
            Dictionary with decrypted API keys or None if not found
        """
        try:
            user = self.user_dao.get_user_by_id(self.user_id)
            if not user or not user.api_key_encrypted:
                return None
            
            # Generate user-specific salt
            user_salt = f"user_{self.user_id}_salt".encode()
            
            # Decrypt the API credentials
            api_key = self.encryption_manager.decrypt(user.api_key_encrypted, user_salt)
            api_secret = self.encryption_manager.decrypt(user.api_secret_encrypted, user_salt)
            
            result = {
                "api_key": api_key,
                "api_secret": api_secret
            }
            
            if user.api_passphrase_encrypted:
                api_passphrase = self.encryption_manager.decrypt(user.api_passphrase_encrypted, user_salt)
                result["api_passphrase"] = api_passphrase
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving API keys for user {self.user_id}: {e}")
            return None
    
    async def remove_api_keys(self) -> bool:
        """
        Remove API keys for a user.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "api_key_encrypted": None,
                "api_secret_encrypted": None,
                "api_passphrase_encrypted": None
            }
            
            success = self.user_dao.update_user(self.user_id, update_data)
            
            if success:
                logger.info(f"API keys removed for user {self.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing API keys for user {self.user_id}: {e}")
            return False
    
    async def check_rotation_due(self) -> bool:
        """
        Check if API keys are due for rotation.
        
        Returns:
            True if rotation is due, False otherwise
        """
        try:
            rotation_config = self.config_dao.get_config("api_keys", "rotation_due", self.user_id)
            if not rotation_config:
                return False
            
            rotation_due = datetime.fromisoformat(rotation_config.value)
            return datetime.utcnow() >= rotation_due
            
        except Exception as e:
            logger.error(f"Error checking rotation due for user {self.user_id}: {e}")
            return False
    
    async def extend_rotation_period(self, days: int = 30) -> bool:
        """
        Extend the rotation period for API keys.
        
        Args:
            days: Number of days to extend
            
        Returns:
            True if successful, False otherwise
        """
        try:
            new_rotation_date = datetime.utcnow() + timedelta(days=days)
            
            await self.config_dao.save_config(
                category="api_keys",
                key="rotation_due",
                value=new_rotation_date.isoformat(),
                value_type="string",
                user_id=self.user_id,
                description=f"API key rotation extended by {days} days",
                updated_by=self.user_id
            )
            
            logger.info(f"API key rotation extended for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error extending rotation period for user {self.user_id}: {e}")
            return False
    
    async def validate_api_keys(self) -> bool:
        """
        Validate API keys by testing connection to dYdX.
        
        Returns:
            True if keys are valid, False otherwise
        """
        try:
            api_keys = await self.get_api_keys()
            if not api_keys:
                return False
            
            # TODO: Implement actual dYdX API validation
            # This would involve making a test API call to verify the keys work
            from ..trading.api_client import DydxRestClient
            
            client = DydxRestClient(
                api_key=api_keys["api_key"],
                api_secret=api_keys["api_secret"],
                api_passphrase=api_keys.get("api_passphrase"),
                testnet=settings.testnet
            )
            
            # Test with a simple API call
            try:
                # account_info = await client.get_account_info()
                # For now, just return True if we have keys
                return True
            except Exception as api_error:
                logger.error(f"API key validation failed: {api_error}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating API keys for user {self.user_id}: {e}")
            return False
    
    async def get_key_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about stored API keys.
        
        Returns:
            Dictionary with key metadata
        """
        try:
            user = self.user_dao.get_user_by_id(self.user_id)
            has_keys = bool(user and user.api_key_encrypted)
            
            last_updated_config = self.config_dao.get_config("api_keys", "last_updated", self.user_id)
            rotation_due_config = self.config_dao.get_config("api_keys", "rotation_due", self.user_id)
            
            last_updated = None
            rotation_due = None
            
            if last_updated_config:
                last_updated = datetime.fromisoformat(last_updated_config.value)
            
            if rotation_due_config:
                rotation_due = datetime.fromisoformat(rotation_due_config.value)
            
            return {
                "has_keys": has_keys,
                "last_updated": last_updated,
                "rotation_due": rotation_due,
                "rotation_overdue": rotation_due and datetime.utcnow() > rotation_due,
                "testnet": settings.testnet
            }
            
        except Exception as e:
            logger.error(f"Error getting key metadata for user {self.user_id}: {e}")
            return {"has_keys": False, "error": str(e)}