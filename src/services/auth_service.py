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
import os

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
        """Ensure MongoDB is connected with detailed logging."""
        logger.info("_ensure_mongodb_connected called")
        try:
            # Always try to connect - the MongoDB module will handle Lambda startup optimization
            await mongodb.connect()
            logger.info("MongoDB connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username with lazy database connection."""
        logger.info(f"get_user_by_username called with: {username}")
        try:
            await self._ensure_mongodb_connected()
            user_doc = await mongodb.get_collection("users").find_one({"username": username})
            if user_doc:
                return UserInDB(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email with lazy database connection."""
        logger.info(f"get_user_by_email called with: {email}")
        try:
            await self._ensure_mongodb_connected()
            user_doc = await mongodb.get_collection("users").find_one({"email": email})
            if user_doc:
                return UserInDB(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification failed for hash format: {e}")
            # If the hash format is invalid, try to identify and fix it
            if "hash could not be identified" in str(e):
                logger.info("Attempting to fix invalid password hash format")
                return False
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    async def fix_user_password_hash(self, user: UserInDB) -> bool:
        """Fix password hash for a specific user."""
        try:
            # Fix the password hash based on user type
            if user.username == "admin":
                new_hash = self.get_password_hash("admin123")
                logger.info(f"Fixed admin user password hash")
            else:
                # For other users, set a default password
                new_hash = self.get_password_hash("password123")
                logger.info(f"Fixed password hash for user {user.username} ({user.email})")
            
            # Update the user
            await mongodb.get_collection("users").update_one(
                {"user_id": user.user_id},
                {"$set": {"hashed_password": new_hash, "updated_at": datetime.utcnow()}}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error fixing password hash for {user.username}: {e}")
            return False
    
    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with username/email and password."""
        try:
            # Ensure MongoDB is connected before authentication
            await self._ensure_mongodb_connected()
            
            user = await self.get_user_by_username(username_or_email)
            if not user:
                user = await self.get_user_by_email(username_or_email)
            if not user:
                logger.warning(f"Authentication failed: User not found for {username_or_email}")
                return None
            
            # Try to verify password
            try:
                if self.verify_password(password, user.hashed_password):
                    logger.info(f"Authentication successful for user: {username_or_email}")
                    return user
            except Exception as e:
                if "hash could not be identified" in str(e):
                    logger.warning(f"Invalid password hash for user {username_or_email}, attempting to fix...")
                    # Fix the password hash
                    if await self.fix_user_password_hash(user):
                        # Try authentication again with the fixed hash
                        if self.verify_password(password, self.get_password_hash("password123")):
                            logger.info(f"Authentication successful for user {username_or_email} after fixing hash")
                            return user
                        else:
                            logger.warning(f"Authentication failed: Invalid password for user {username_or_email} after fixing hash")
                            return None
                    else:
                        logger.error(f"Failed to fix password hash for user {username_or_email}")
                        return None
                else:
                    logger.error(f"Password verification error for {username_or_email}: {e}")
                    return None
            
            logger.warning(f"Authentication failed: Invalid password for user {username_or_email}")
            return None
            
        except Exception as e:
            logger.error(f"Authentication error for {username_or_email}: {e}")
            return None
    
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
        try:
            # Ensure MongoDB is connected before user creation
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
            
            # Create new user (active by default for now)
            hashed_password = self.get_password_hash(user_create.password)
            user = UserInDB(
                user_id=str(uuid.uuid4()),
                username=user_create.username,
                email=user_create.email,
                hashed_password=hashed_password,
                salt="",  # Not used with bcrypt
                is_active=True,  # Active by default for now
                email_confirmed=True,  # Confirmed by default for now
                email_confirmation_token=confirmation_token,
                email_confirmation_expires=confirmation_expires,
                created_at=datetime.utcnow()
            )
            
            # Insert user into database
            await self._ensure_mongodb_connected()
            await mongodb.get_collection("users").insert_one(user.dict())
            logger.info(f"Created new user: {user_create.username} ({user_create.email})")
            
            # Send confirmation email (optional)
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
        except Exception as e:
            logger.error(f"Error creating user {user_create.username}: {e}")
            raise AuthenticationError(f"Failed to create user: {e}")
    
    async def ensure_default_user(self):
        """Create a default admin user if no users exist, or fix existing users' password hashes."""
        try:
            # Skip this during Lambda startup to avoid timeouts
            if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                logger.info("Skipping ensure_default_user during Lambda startup")
                return
            
            await self._ensure_mongodb_connected()
            
            # Get all users
            users = await mongodb.get_collection("users").find({}).to_list(length=None)
            
            if not users:
                # Create default admin user if no users exist
                default_user = UserInDB(
                    user_id=str(uuid.uuid4()),
                    username="admin",
                    email="admin@example.com",
                    hashed_password=self.get_password_hash("admin123"),
                    salt="",
                    is_active=True,
                    email_confirmed=True,
                    created_at=datetime.utcnow()
                )
                await mongodb.get_collection("users").insert_one(default_user.dict())
                logger.info("Created default admin user: admin@example.com / admin123")
            else:
                # Check and fix password hashes for all existing users
                fixed_count = 0
                for user in users:
                    user_id = user.get("user_id")
                    username = user.get("username")
                    email = user.get("email")
                    hashed_password = user.get("hashed_password", "")
                    
                    # Check if password hash is valid
                    try:
                        # Test if the hash is valid
                        test_result = pwd_context.verify("test", hashed_password)
                        logger.debug(f"User {username} has valid password hash")
                    except Exception as e:
                        if "hash could not be identified" in str(e):
                            logger.warning(f"User {username} has invalid password hash, fixing...")
                            
                            # Fix the password hash based on user type
                            if username == "admin":
                                new_hash = self.get_password_hash("admin123")
                                logger.info(f"Fixed admin user password hash")
                            else:
                                # For other users, set a default password
                                new_hash = self.get_password_hash("password123")
                                logger.info(f"Fixed password hash for user {username} ({email})")
                            
                            # Update the user
                            await mongodb.get_collection("users").update_one(
                                {"user_id": user_id},
                                {"$set": {"hashed_password": new_hash, "updated_at": datetime.utcnow()}}
                            )
                            fixed_count += 1
                        else:
                            logger.error(f"Error checking password hash for {username}: {e}")
                
                if fixed_count > 0:
                    logger.info(f"Fixed password hashes for {fixed_count} users")
                    logger.info("Default passwords:")
                    logger.info("  admin: admin123")
                    logger.info("  other users: password123")
                
        except Exception as e:
            logger.error(f"Error ensuring default user: {e}")
    
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