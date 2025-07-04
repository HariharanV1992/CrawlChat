#!/usr/bin/env python3
"""
Direct test and fix for password hash issue.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the lambda-function directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lambda-function"))

from src.core.database import mongodb
from src.services.auth_service import AuthService

async def test_and_fix_password():
    """Test and fix password hash directly."""
    try:
        print("🔧 Testing and fixing password hash...")
        
        # Connect to MongoDB
        await mongodb.connect()
        print("✅ Connected to MongoDB")
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Find the specific user
        user = await mongodb.get_collection("users").find_one({"email": "harito2do@gmail.com"})
        
        if not user:
            print("❌ User harito2do@gmail.com not found!")
            return
        
        print(f"✅ Found user: {user.get('username', 'Unknown')}")
        print(f"📧 Email: {user.get('email')}")
        
        # Check current password hash
        current_hash = user.get("hashed_password", "")
        print(f"🔍 Current hash: {current_hash[:50]}...")
        
        # Force fix the password hash (regardless of current format)
        print("🔧 Forcing password hash fix...")
        new_hash = auth_service.get_password_hash("password123")
        
        # Update the user
        result = await mongodb.get_collection("users").update_one(
            {"email": "harito2do@gmail.com"},
            {"$set": {"hashed_password": new_hash, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            print("✅ Password hash fixed successfully!")
            print("🔑 New password: password123")
            print(f"🆕 New hash: {new_hash[:50]}...")
        else:
            print("❌ Failed to update password hash")
            return
        
        # Test login with new password
        print("\n🧪 Testing login...")
        test_user = await auth_service.authenticate_user("harito2do@gmail.com", "password123")
        
        if test_user:
            print("✅ Login test successful!")
            print("🎉 Password hash fix completed!")
        else:
            print("❌ Login test failed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await mongodb.disconnect()

if __name__ == "__main__":
    asyncio.run(test_and_fix_password()) 