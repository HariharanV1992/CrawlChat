"""
API dependencies for authentication and common functionality.
"""

import logging
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt

from common.src.models.auth import TokenData
from common.src.services.auth_service import auth_service
from common.src.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return auth_service._user_to_response(user)
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenVerification:
    """Verify if the current token is valid."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        if not user:
            return TokenVerification(valid=False)
        
        return TokenVerification(valid=True, user=auth_service._user_to_response(user))
        
    except Exception as e:
        logger.error(f"Error in verify_token: {e}")
        return TokenVerification(valid=False)

async def verify_token_graceful(authorization: Optional[str] = Header(None)) -> TokenVerification:
    """Verify if the current token is valid (graceful handling)."""
    if not authorization or not authorization.startswith("Bearer "):
        return TokenVerification(valid=False)
    
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        if not user:
            return TokenVerification(valid=False)
        
        return TokenVerification(valid=True, user=auth_service._user_to_response(user))
        
    except jwt.PyJWTError:
        return TokenVerification(valid=False)
    except Exception as e:
        logger.error(f"Error in verify_token_graceful: {e}")
        return TokenVerification(valid=False)

async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        
        if not user:
            return None
        
        return auth_service._user_to_response(user)
        
    except Exception as e:
        logger.error(f"Error in get_optional_user: {e}")
        return None 