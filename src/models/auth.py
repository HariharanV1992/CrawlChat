"""
Authentication models for Stock Market Crawler.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class UserResponse(UserBase):
    """User response model."""
    user_id: str = Field(..., description="Unique user ID")
    created_at: datetime = Field(..., description="Account creation timestamp")
    is_active: bool = Field(default=True, description="Account status")


class UserSession(BaseModel):
    """User session model."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenVerification(BaseModel):
    """Token verification response model."""
    valid: bool = Field(..., description="Whether the token is valid")
    user: Optional[UserResponse] = Field(None, description="User information if token is valid")


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordReset(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class EmailConfirmation(BaseModel):
    """Email confirmation model."""
    token: str = Field(..., description="Email confirmation token")


class EmailConfirmationResponse(BaseModel):
    """Email confirmation response model."""
    success: bool = Field(..., description="Whether confirmation was successful")
    message: str = Field(..., description="Confirmation message")
    user: Optional[UserResponse] = Field(None, description="User information if confirmation successful")


class ResendConfirmationEmail(BaseModel):
    """Resend confirmation email model."""
    email: EmailStr = Field(..., description="Email address to resend confirmation to")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    email: Optional[EmailStr] = Field(None, description="New email address")
    is_active: Optional[bool] = Field(None, description="Account status")


class UserInDB(UserBase):
    user_id: str = Field(..., description="Unique user ID")
    hashed_password: str = Field(..., description="Hashed password")
    salt: Optional[str] = Field(default="", description="Password salt (not used with bcrypt)")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=False, description="Account status - requires email confirmation")
    email_confirmed: bool = Field(default=False, description="Email confirmation status")
    email_confirmation_token: Optional[str] = Field(default=None, description="Email confirmation token")
    email_confirmation_expires: Optional[datetime] = Field(default=None, description="Email confirmation token expiry")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class Token(BaseModel):
    """JWT Token model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Token data for JWT payload."""
    username: str = Field(..., description="Username from token payload")


# For compatibility with legacy code, alias User to UserResponse
User = UserResponse 