"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import timedelta

from ..database.base import get_db
from ..security.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    AuthenticationManager, get_current_user, User
)
from ..security.key_manager import APIKeyManager
from .schemas import (
    UserLogin, UserRegister, TwoFactorRequest, TokenResponse, 
    UserResponse
)
from ..config.settings import get_settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user account."""
    try:
        # Validate password confirmation
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        auth_manager = AuthenticationManager(db)
        success, message, user = await auth_manager.register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        logger.info(f"User registered: {user_data.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_2fa_enabled=user.is_2fa_enabled,
            is_active=user.is_active,
            trading_enabled=user.trading_enabled,
            paper_trading_mode=user.paper_trading_mode,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    try:
        user = await authenticate_user(
            email=login_data.email,
            password=login_data.password,
            db=db
        )
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if user == "2fa_required":
            return TokenResponse(
                access_token="",
                requires_2fa=True,
                expires_in=0
            )
        
        # Create access and refresh tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        logger.info(f"User logged in: {login_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            requires_2fa=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login/2fa", response_model=TokenResponse)
async def login_with_2fa(
    login_data: UserLogin,
    two_fa_data: TwoFactorRequest,
    db: Session = Depends(get_db)
):
    """Complete login with 2FA token."""
    try:
        user = await authenticate_user(
            email=login_data.email,
            password=login_data.password,
            db=db,
            totp_token=two_fa_data.token
        )
        
        if user is None or user == "2fa_required":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or 2FA token"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        logger.info(f"User logged in with 2FA: {login_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            requires_2fa=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_2fa_enabled=current_user.is_2fa_enabled,
        is_active=current_user.is_active,
        trading_enabled=current_user.trading_enabled,
        paper_trading_mode=current_user.paper_trading_mode,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize 2FA setup for the user."""
    try:
        auth_manager = AuthenticationManager(db)
        success, message, qr_code = await auth_manager.setup_2fa(current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "success": True,
            "message": message,
            "qr_code": qr_code,
            "instructions": "Scan the QR code with your authenticator app and verify with a token"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA setup failed"
        )


@router.post("/2fa/verify")
async def verify_2fa_setup(
    two_fa_data: TwoFactorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup and enable it."""
    try:
        auth_manager = AuthenticationManager(db)
        success, message, backup_codes = await auth_manager.verify_2fa_setup(
            current_user.id, 
            two_fa_data.token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "success": True,
            "message": message,
            "backup_codes": backup_codes,
            "warning": "Save these backup codes in a secure location"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA verification failed"
        )


@router.post("/2fa/disable")
async def disable_2fa(
    password_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for the user."""
    try:
        if "password" not in password_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required to disable 2FA"
            )
        
        auth_manager = AuthenticationManager(db)
        success, message = await auth_manager.disable_2fa(
            current_user.id,
            password_data["password"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "success": True,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA disable failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        required_fields = ["current_password", "new_password"]
        for field in required_fields:
            if field not in password_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        auth_manager = AuthenticationManager(db)
        success, message = await auth_manager.change_password(
            current_user.id,
            password_data["current_password"],
            password_data["new_password"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "success": True,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/api-keys/store")
async def store_api_keys(
    api_keys_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store encrypted dYdX API keys."""
    try:
        required_fields = ["api_key", "api_secret"]
        for field in required_fields:
            if field not in api_keys_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        key_manager = APIKeyManager(db, current_user.id)
        success = await key_manager.store_api_keys(
            api_key=api_keys_data["api_key"],
            api_secret=api_keys_data["api_secret"],
            api_passphrase=api_keys_data.get("api_passphrase")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store API keys"
            )
        
        logger.info(f"API keys stored for user {current_user.id}")
        
        return {
            "success": True,
            "message": "API keys stored successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key storage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key storage failed"
        )


@router.get("/api-keys/status")
async def get_api_keys_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API keys status and metadata."""
    try:
        key_manager = APIKeyManager(db, current_user.id)
        metadata = await key_manager.get_key_metadata()
        
        return {
            "success": True,
            "data": metadata
        }
        
    except Exception as e:
        logger.error(f"API key status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key status"
        )


@router.post("/api-keys/validate")
async def validate_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate stored API keys."""
    try:
        key_manager = APIKeyManager(db, current_user.id)
        is_valid = await key_manager.validate_api_keys()
        
        return {
            "success": True,
            "valid": is_valid,
            "message": "API keys are valid" if is_valid else "API keys are invalid or missing"
        }
        
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key validation failed"
        )


@router.delete("/api-keys")
async def remove_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove stored API keys."""
    try:
        key_manager = APIKeyManager(db, current_user.id)
        success = await key_manager.remove_api_keys()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove API keys"
            )
        
        logger.info(f"API keys removed for user {current_user.id}")
        
        return {
            "success": True,
            "message": "API keys removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key removal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key removal failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """Logout user (invalidate token on client side)."""
    # Note: With JWT, we can't truly invalidate tokens server-side without
    # maintaining a blacklist. For now, we rely on client-side token removal.
    logger.info(f"User logged out: {current_user.email}")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }