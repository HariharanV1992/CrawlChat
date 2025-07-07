"""
Security utilities for password hashing and validation.
"""

import hashlib
import secrets
import string
from typing import Tuple

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash a password with a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt
    salted = password + salt
    
    # Hash using SHA-256
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash."""
    expected_hash, _ = hash_password(password, salt)
    return hashed == expected_hash

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def get_password_hash(password: str) -> str:
    """Get password hash using bcrypt."""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        # Fallback to SHA-256 if bcrypt is not available
        hashed, salt = hash_password(password)
        return f"{hashed}:{salt}" 