"""
Authentication service for user management and JWT token handling.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from src.core.config import config
from src.models.auth import User, UserCreate, Token, TokenData, UserInDB, UserResponse, LoginResponse
from src.core.exceptions import AuthenticationError
import uuid
from src.core.database import mongodb
import logging
from src.services.email_service import email_service
from datetime import timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = config.secret_key
ALGORITHM = config.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.access_token_expire_minutes

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user management and JWT operations using MongoDB."""
    
    def __init__(self):
        pass  # No in-memory users
    
    async def _ensure_mongodb_connected(self):
        """Ensure MongoDB is connected before operations."""
        try:
            if not mongodb.is_connected():
                await mongodb.connect()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise AuthenticationError(f"MongoDB connection failed: {e}")
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        await self._ensure_mongodb_connected()
        user_doc = await mongodb.get_collection("users").find_one({"username": username})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        await self._ensure_mongodb_connected()
        user_doc = await mongodb.get_collection("users").find_one({"email": email})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with username/email and password."""
        user = await self.get_user_by_username(username_or_email)
        if not user:
            user = await self.get_user_by_email(username_or_email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
            return token_data
        except jwt.PyJWTError:
            return None
    
    async def get_current_user(self, token: str) -> Optional[UserInDB]:
        """Get current user from token."""
        token_data = self.verify_token(token)
        if token_data is None:
            return None
        user = await self.get_user_by_username(token_data.username)
        if user is None:
            return None
        return user
    
    async def create_user(self, user_create: UserCreate) -> UserInDB:
        """Create a new user with email confirmation."""
        await self._ensure_mongodb_connected()
        
        # Check if user already exists
        existing = await self.get_user_by_username(user_create.username)
        if existing:
            raise AuthenticationError("Username already registered")
        existing_email = await self.get_user_by_email(user_create.email)
        if existing_email:
            raise AuthenticationError("Email already registered")
        
        # Generate confirmation token
        confirmation_token = email_service.generate_confirmation_token()
        confirmation_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Create new user (inactive until email confirmed)
        hashed_password = self.get_password_hash(user_create.password)
        user = UserInDB(
            user_id=str(uuid.uuid4()),
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            salt="",  # Not used with bcrypt
            is_active=False,  # Will be activated after email confirmation
            email_confirmed=False,
            email_confirmation_token=confirmation_token,
            email_confirmation_expires=confirmation_expires,
            created_at=datetime.utcnow()
        )
        
        await mongodb.get_collection("users").insert_one(user.dict())
        
        # Send confirmation email
        try:
            email_sent = email_service.send_confirmation_email(
                user_create.email, 
                user_create.username, 
                confirmation_token
            )
            if not email_sent:
                logger.warning(f"Failed to send confirmation email to {user_create.email}")
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
        
        return user
    
    async def ensure_default_user(self):
        """Create a default admin user if no users exist."""
        try:
            # Check if any users exist
            user_count = await mongodb.get_collection("users").count_documents({})
            if user_count == 0:
                # Create default admin user
                default_user = UserInDB(
                    user_id=str(uuid.uuid4()),
                    username="admin",
                    email="admin@example.com",
                    hashed_password=self.get_password_hash("admin123"),
                    salt="",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                await mongodb.get_collection("users").insert_one(default_user.dict())
                logger.info("Created default admin user: admin@example.com / admin123")
        except Exception as e:
            logger.error(f"Error creating default user: {e}")
    
    async def login_user(self, username_or_email: str, password: str) -> Optional[LoginResponse]:
        """Login a user and return access token."""
        user = await self.authenticate_user(username_or_email, password)
        if not user:
            return None
        
        # Check if account is active
        if not user.is_active:
            raise AuthenticationError("Account is not active. Please contact support.")
        
        # For now, skip email confirmation check to allow login
        # TODO: Re-enable email confirmation in production
        # if not user.email_confirmed:
        #     raise AuthenticationError("Please confirm your email address before logging in. Check your inbox for a confirmation email.")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Update last login
        await mongodb.get_collection("users").update_one(
            {"user_id": user.user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=self._user_to_response(user),
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def logout_user(self, token: str) -> bool:
        """Logout a user (invalidate token)."""
        # In a production system, you would add the token to a blacklist
        # For now, we just return True as JWT tokens are stateless
        return True
    
    async def confirm_email(self, token: str) -> bool:
        """Confirm user email with token."""
        try:
            await self._ensure_mongodb_connected()
            
            # Find user with this confirmation token
            user_doc = await mongodb.get_collection("users").find_one({
                "email_confirmation_token": token,
                "email_confirmation_expires": {"$gt": datetime.utcnow()}
            })
            
            if not user_doc:
                return False
            
            user = UserInDB(**user_doc)
            
            # Update user to confirmed
            await mongodb.get_collection("users").update_one(
                {"user_id": user.user_id},
                {
                    "$set": {
                        "is_active": True,
                        "email_confirmed": True,
                        "email_confirmation_token": None,
                        "email_confirmation_expires": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Send welcome email
            try:
                email_service.send_welcome_email(user.email, user.username)
            except Exception as e:
                logger.error(f"Error sending welcome email: {e}")
            
            logger.info(f"Email confirmed for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming email: {e}")
            return False
    
    async def resend_confirmation_email(self, email: str) -> bool:
        """Resend confirmation email."""
        try:
            await self._ensure_mongodb_connected()
            
            user = await self.get_user_by_email(email)
            if not user:
                return False
            
            if user.email_confirmed:
                return False  # Already confirmed
            
            # Generate new confirmation token
            confirmation_token = email_service.generate_confirmation_token()
            confirmation_expires = datetime.utcnow() + timedelta(hours=24)
            
            # Update user with new token
            await mongodb.get_collection("users").update_one(
                {"user_id": user.user_id},
                {
                    "$set": {
                        "email_confirmation_token": confirmation_token,
                        "email_confirmation_expires": confirmation_expires,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Send confirmation email
            email_sent = email_service.send_confirmation_email(
                user.email, 
                user.username, 
                confirmation_token
            )
            
            if email_sent:
                logger.info(f"Confirmation email resent to: {email}")
                return True
            else:
                logger.error(f"Failed to resend confirmation email to: {email}")
                return False
                
        except Exception as e:
            logger.error(f"Error resending confirmation email: {e}")
            return False
    
    async def register_user(self, user_create: UserCreate) -> User:
        """Register a new user (alias for create_user)."""
        return await self.create_user(user_create)
    
    def _user_to_response(self, user: UserInDB) -> UserResponse:
        """Convert UserInDB to UserResponse for API responses."""
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )

# Global auth service instance
auth_service = AuthService() 