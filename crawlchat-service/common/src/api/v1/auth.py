"""
Authentication API endpoints for Stock Market Crawler.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials

from common.src.models.auth import (
    User, UserCreate, Token, TokenData, UserInDB, UserResponse, LoginResponse,
    UserLogin, TokenVerification, EmailConfirmation, EmailConfirmationResponse, ResendConfirmationEmail
)
from common.src.services.auth_service import auth_service
from common.src.api.dependencies import security, get_current_user, verify_token_graceful
from common.src.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate):
    """Register a new user account."""
    try:
        user = await auth_service.register_user(user_create)
        return auth_service._user_to_response(user)
    except AuthenticationError as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login(user_login: UserLogin, response: Response):
    """Authenticate user and return access token."""
    try:
        logger.info(f"Login attempt for email: {user_login.email}")
        result = await auth_service.login_user(user_login.email, user_login.password)
        if not result:
            logger.warning(f"Login failed for email: {user_login.email} - invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"Login successful for email: {user_login.email}, setting cookie")
        
        # Set HTTP-only cookie for server-side authentication
        response.set_cookie(
            key="access_token",
            value=result.access_token,
            httponly=True,
            secure=True,  # MUST be True for HTTPS
            samesite="none",  # MUST be 'none' for cross-site cookies
            max_age=3600,  # 1 hour
            domain=".crawlchat.site"  # Ensures cookie is sent to all subdomains
        )
        
        logger.info(f"Login response prepared for email: {user_login.email}")
        logger.info(f"Response data: access_token={result.access_token[:10]}..., user_id={result.user.user_id}")
        
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error for email {user_login.email}: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during login for email {user_login.email}: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security), response: Response = None):
    """Logout current user by invalidating their session/token."""
    try:
        token = credentials.credentials
        success = auth_service.logout_user(token)
        
        # Clear the access_token cookie
        if response:
            response.delete_cookie(key="access_token")
        
        if success:
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout-simple")
async def logout_simple(response: Response):
    """Simple logout that just clears the cookie without requiring authentication."""
    try:
        # Clear the access_token cookie
        response.delete_cookie(key="access_token")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Error in simple logout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile."""
    return current_user

@router.get("/verify", response_model=TokenVerification)
async def verify_token_endpoint(token_verification: TokenVerification = Depends(verify_token_graceful)):
    """Verify if the current token is valid."""
    return token_verification

@router.post("/confirm-email", response_model=EmailConfirmationResponse)
async def confirm_email(confirmation: EmailConfirmation):
    """Confirm user email with token."""
    try:
        success = await auth_service.confirm_email(confirmation.token)
        if success:
            return EmailConfirmationResponse(
                success=True,
                message="Email confirmed successfully! You can now log in to your account."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid or expired confirmation token. Please request a new confirmation email."
            )
    except Exception as e:
        logger.error(f"Error confirming email: {e}")
        raise HTTPException(status_code=500, detail="Email confirmation failed")

@router.post("/resend-confirmation", response_model=dict)
async def resend_confirmation_email(request: ResendConfirmationEmail):
    """Resend confirmation email."""
    try:
        success = await auth_service.resend_confirmation_email(request.email)
        if success:
            return {
                "message": "Confirmation email sent successfully. Please check your inbox."
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Unable to resend confirmation email. Please check your email address or contact support."
            )
    except Exception as e:
        logger.error(f"Error resending confirmation email: {e}")
        raise HTTPException(status_code=500, detail="Failed to resend confirmation email") 