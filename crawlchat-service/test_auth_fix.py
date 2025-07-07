#!/usr/bin/env python3
"""
Test script to verify authentication is working correctly.
"""

import asyncio
import sys
import os

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.src.services.auth_service import AuthService
from common.src.core.database import mongodb

async def test_authentication():
    """Test authentication with the default user."""
    try:
        print("🧪 Testing authentication...")
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Connect to MongoDB
        await mongodb.connect()
        print("✅ Connected to MongoDB")
        
        # Test user lookup
        print("\n1. Testing user lookup...")
        user = await auth_service.get_user_by_email("harito2do@gmail.com")
        if user:
            print(f"✅ User found: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Active: {user.is_active}")
            print(f"   Email Confirmed: {user.email_confirmed}")
        else:
            print("❌ User not found")
            return
        
        # Test password verification
        print("\n2. Testing password verification...")
        test_passwords = ["password123", "wrongpassword", "admin123"]
        
        for password in test_passwords:
            try:
                is_valid = auth_service.verify_password(password, user.hashed_password)
                print(f"   Password '{password}': {'✅ Valid' if is_valid else '❌ Invalid'}")
            except Exception as e:
                print(f"   Password '{password}': ❌ Error - {e}")
        
        # Test authentication
        print("\n3. Testing authentication...")
        login_result = await auth_service.login_user("harito2do@gmail.com", "password123")
        if login_result:
            print("✅ Authentication successful!")
            print(f"   Access Token: {login_result.access_token[:50]}...")
            print(f"   Token Type: {login_result.token_type}")
            print(f"   Expires In: {login_result.expires_in} seconds")
            print(f"   User: {login_result.user.email}")
        else:
            print("❌ Authentication failed")
        
        # Test with wrong password
        print("\n4. Testing wrong password...")
        wrong_login = await auth_service.login_user("harito2do@gmail.com", "wrongpassword")
        if wrong_login:
            print("❌ Authentication should have failed with wrong password")
        else:
            print("✅ Correctly rejected wrong password")
        
        print("\n🎉 Authentication test completed!")
        
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        raise
    finally:
        await mongodb.disconnect()
        print("✅ Disconnected from MongoDB")

async def main():
    """Main function."""
    await test_authentication()

if __name__ == "__main__":
    asyncio.run(main()) 