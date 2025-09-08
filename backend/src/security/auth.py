"""Authentication and authorization utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import pyotp
import qrcode
import io
import base64
import secrets
import logging

from ..database.base import get_db
from ..database.models import User as UserModel
from ..database.dao import UserDAO
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class User:
    """User model for authentication."""
    
    def __init__(self, user_data: UserModel):
        self.id = user_data.id
        self.email = user_data.email
        self.username = user_data.username
        self.is_active = user_data.is_active
        self.is_superuser = user_data.is_superuser
        self.is_2fa_enabled = user_data.is_2fa_enabled
        self.trading_enabled = user_data.trading_enabled
        self.paper_trading_mode = user_data.paper_trading_mode
        self.created_at = user_data.created_at
        self.last_login = user_data.last_login


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Token validation error: {e}")
        return None


async def authenticate_user(
    email: str, 
    password: str, 
    db: Session,
    totp_token: Optional[str] = None
) -> Optional[User]:
    """Authenticate a user with email/password and optional 2FA."""
    user_dao = UserDAO(db)
    user_model = user_dao.get_user_by_email(email)
    
    if not user_model:
        logger.warning(f"Authentication failed: user {email} not found")
        return None
    
    if not verify_password(password, user_model.hashed_password):
        logger.warning(f"Authentication failed: invalid password for {email}")
        return None
    
    if not user_model.is_active:
        logger.warning(f"Authentication failed: user {email} is inactive")
        return None
    
    # Check 2FA if enabled
    if user_model.is_2fa_enabled:
        if not totp_token:
            logger.info(f"2FA required for user {email}")
            # Return a special indicator that 2FA is required
            return "2fa_required"
        
        if not verify_totp_token(user_model.totp_secret, totp_token):
            logger.warning(f"Authentication failed: invalid 2FA token for {email}")
            return None
    
    # Update last login
    user_dao.update_last_login(user_model.id)
    
    logger.info(f"User {email} authenticated successfully")
    return User(user_model)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user_dao = UserDAO(db)
    user_model = user_dao.get_user_by_email(email)
    
    if user_model is None:
        raise credentials_exception
    
    return User(user_model)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def generate_2fa_secret() -> str:
    """Generate a new TOTP secret for 2FA."""
    return pyotp.random_base32()


def get_2fa_qr_code(secret: str, email: str, issuer: str = "dYdX Trading Bot") -> str:
    """Generate a QR code for 2FA setup."""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Convert to base64 image
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Encode as base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def verify_totp_token(secret: str, token: str) -> bool:
    """Verify a TOTP token."""
    if not secret or not token:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        # Allow for some clock drift (window of 1 = 30 seconds before/after)
        return totp.verify(token, valid_window=1)
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        return False


def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate backup codes for 2FA recovery."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def verify_backup_code(backup_codes: list[str], provided_code: str) -> tuple[bool, list[str]]:
    """
    Verify a backup code and remove it from the list.
    
    Returns:
        Tuple of (is_valid, updated_backup_codes)
    """
    if not backup_codes or not provided_code:
        return False, backup_codes
    
    provided_code = provided_code.upper().strip()
    
    if provided_code in backup_codes:
        # Remove the used backup code
        updated_codes = [code for code in backup_codes if code != provided_code]
        return True, updated_codes
    
    return False, backup_codes


class AuthenticationManager:
    """Comprehensive authentication management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_dao = UserDAO(db)
    
    async def register_user(
        self, 
        email: str, 
        username: str, 
        password: str
    ) -> tuple[bool, str, Optional[User]]:
        """
        Register a new user.
        
        Returns:
            Tuple of (success, message, user_obj)
        """
        try:
            # Check if user already exists
            existing_user = self.user_dao.get_user_by_email(email)
            if existing_user:
                return False, "User already exists", None
            
            # Create user
            user_data = {
                "email": email,
                "username": username,
                "hashed_password": hash_password(password),
                "is_active": True,
                "is_superuser": False,
                "is_2fa_enabled": False,
                "trading_enabled": True,
                "paper_trading_mode": True  # Default to paper trading
            }
            
            user_model = self.user_dao.create_user(user_data)
            user = User(user_model)
            
            logger.info(f"New user registered: {email}")
            return True, "User registered successfully", user
            
        except Exception as e:
            logger.error(f"User registration error: {e}")
            return False, "Registration failed", None
    
    async def setup_2fa(
        self, 
        user_id: int
    ) -> tuple[bool, str, Optional[str]]:
        """
        Set up 2FA for a user.
        
        Returns:
            Tuple of (success, message, qr_code_base64)
        """
        try:
            user_model = self.user_dao.get_user_by_id(user_id)
            if not user_model:
                return False, "User not found", None
            
            # Generate new TOTP secret
            secret = generate_2fa_secret()
            backup_codes = generate_backup_codes()
            
            # Update user with 2FA secret and backup codes
            self.user_dao.update_user(user_id, {
                "totp_secret": secret,
                "backup_codes": backup_codes,
                "is_2fa_enabled": False  # Will be enabled after verification
            })
            
            # Generate QR code
            qr_code = get_2fa_qr_code(secret, user_model.email)
            
            return True, "2FA setup initiated", qr_code
            
        except Exception as e:
            logger.error(f"2FA setup error: {e}")
            return False, "2FA setup failed", None
    
    async def verify_2fa_setup(
        self, 
        user_id: int, 
        token: str
    ) -> tuple[bool, str, Optional[list[str]]]:
        """
        Verify 2FA setup and enable it.
        
        Returns:
            Tuple of (success, message, backup_codes)
        """
        try:
            user_model = self.user_dao.get_user_by_id(user_id)
            if not user_model or not user_model.totp_secret:
                return False, "2FA setup not initiated", None
            
            # Verify the token
            if not verify_totp_token(user_model.totp_secret, token):
                return False, "Invalid verification code", None
            
            # Enable 2FA
            self.user_dao.update_user(user_id, {
                "is_2fa_enabled": True
            })
            
            logger.info(f"2FA enabled for user {user_id}")
            return True, "2FA enabled successfully", user_model.backup_codes
            
        except Exception as e:
            logger.error(f"2FA verification error: {e}")
            return False, "2FA verification failed", None
    
    async def disable_2fa(
        self, 
        user_id: int, 
        password: str
    ) -> tuple[bool, str]:
        """
        Disable 2FA for a user.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            user_model = self.user_dao.get_user_by_id(user_id)
            if not user_model:
                return False, "User not found"
            
            # Verify password
            if not verify_password(password, user_model.hashed_password):
                return False, "Invalid password"
            
            # Disable 2FA
            self.user_dao.update_user(user_id, {
                "is_2fa_enabled": False,
                "totp_secret": None,
                "backup_codes": None
            })
            
            logger.info(f"2FA disabled for user {user_id}")
            return True, "2FA disabled successfully"
            
        except Exception as e:
            logger.error(f"2FA disable error: {e}")
            return False, "Failed to disable 2FA"
    
    async def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> tuple[bool, str]:
        """
        Change user password.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            user_model = self.user_dao.get_user_by_id(user_id)
            if not user_model:
                return False, "User not found"
            
            # Verify current password
            if not verify_password(current_password, user_model.hashed_password):
                return False, "Invalid current password"
            
            # Update password
            new_hashed_password = hash_password(new_password)
            self.user_dao.update_user(user_id, {
                "hashed_password": new_hashed_password
            })
            
            logger.info(f"Password changed for user {user_id}")
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, "Failed to change password"