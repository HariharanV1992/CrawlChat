#!/usr/bin/env python3
"""
Script to create a default user for testing CrawlChat.
This can be run locally or in Lambda to ensure there's always a test user available.
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.src.services.auth_service import AuthService
from common.src.models.auth import UserInDB
from common.src.core.database import mongodb

async def create_default_user():
    """Create a default user for testing."""
    try:
        print("🔧 Creating default user for CrawlChat...")
        
        # Initialize services
        auth_service = AuthService()
        
        # Connect to MongoDB
        await mongodb.connect()
        print("✅ Connected to MongoDB")
        
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email("harito2do@gmail.com")
        if existing_user:
            print(f"⚠️  User already exists: {existing_user.email}")
            
            # Fix password hash if needed
            try:
                # Test current password
                if auth_service.verify_password("password123", existing_user.hashed_password):
                    print("✅ User password is working correctly")
                    print(f"   Email: {existing_user.email}")
                    print(f"   Password: password123")
                    return
                else:
                    print("🔧 Fixing user password hash...")
                    await auth_service.fix_user_password_hash(existing_user)
                    print("✅ Password hash fixed")
                    print(f"   Email: {existing_user.email}")
                    print(f"   Password: password123")
                    return
            except Exception as e:
                print(f"🔧 Fixing corrupted password hash: {e}")
                await auth_service.fix_user_password_hash(existing_user)
                print("✅ Password hash fixed")
                print(f"   Email: {existing_user.email}")
                print(f"   Password: password123")
                return
        
        # Create new default user
        default_user = UserInDB(
            user_id=str(uuid.uuid4()),
            username="harito2do",
            email="harito2do@gmail.com",
            hashed_password=auth_service.get_password_hash("password123"),
            salt="",
            is_active=True,
            email_confirmed=True,
            created_at=datetime.utcnow()
        )
        
        # Insert user into database
        await mongodb.get_collection("users").insert_one(default_user.dict())
        
        print("✅ Default user created successfully!")
        print(f"   Email: {default_user.email}")
        print(f"   Password: password123")
        print(f"   Username: {default_user.username}")
        
    except Exception as e:
        print(f"❌ Error creating default user: {e}")
        raise
    finally:
        # Disconnect from MongoDB
        await mongodb.disconnect()
        print("✅ Disconnected from MongoDB")

async def list_users():
    """List all users in the database."""
    try:
        print("👥 Listing all users...")
        
        # Connect to MongoDB
        await mongodb.connect()
        print("✅ Connected to MongoDB")
        
        # Get all users
        users = await mongodb.get_collection("users").find({}).to_list(length=None)
        
        if not users:
            print("📭 No users found in database")
        else:
            print(f"📋 Found {len(users)} users:")
            for user in users:
                print(f"   - {user.get('email', 'N/A')} (username: {user.get('username', 'N/A')})")
                print(f"     Active: {user.get('is_active', False)}")
                print(f"     Email Confirmed: {user.get('email_confirmed', False)}")
                print()
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        raise
    finally:
        # Disconnect from MongoDB
        await mongodb.disconnect()
        print("✅ Disconnected from MongoDB")

async def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        await list_users()
    else:
        await create_default_user()
        print("\n🎉 You can now log in with:")
        print("   Email: harito2do@gmail.com")
        print("   Password: password123")

if __name__ == "__main__":
    asyncio.run(main()) 