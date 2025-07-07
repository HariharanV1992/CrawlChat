#!/usr/bin/env python3
"""
Test script to verify completion message handling.
"""

import asyncio
import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.chat_service import chat_service
from common.src.core.database import mongodb
from common.src.core.config import config

async def test_completion_messages():
    """Test completion message handling."""
    
    print("🧪 Testing Completion Message Handling")
    print("=" * 50)
    
    try:
        # Setup database connection
        await mongodb.connect()
        print("✅ Database connected")
        
        # Test user ID
        test_user_id = "test-user-completion"
        test_session_id = "test-session-completion"
        
        # Create a test session
        print(f"📝 Creating test session: {test_session_id}")
        session_data = {
            "session_id": test_session_id,
            "user_id": test_user_id,
            "document_count": 3,
            "crawl_tasks": ["test-crawl-task"],
            "uploaded_documents": ["test-uploaded-doc"],
            "messages": [
                {
                    "role": "system",
                    "content": "📄 Linked 3 documents to this session. Processing documents in background...",
                    "timestamp": "2025-01-08T00:00:00Z",
                    "session_id": test_session_id
                }
            ],
            "processing_status": "processing",
            "created_at": "2025-01-08T00:00:00Z",
            "updated_at": "2025-01-08T00:00:00Z"
        }
        
        # Insert test session
        await mongodb.get_collection("chat_sessions").insert_one(session_data)
        print("✅ Test session created")
        
        # Test 1: Check for missing completion message
        print("\n🔍 Test 1: Checking for missing completion message...")
        result = await chat_service.check_and_add_missing_completion_message(test_session_id, test_user_id)
        print(f"Result: {result}")
        
        # Get updated messages
        messages = await chat_service.get_session_messages(test_session_id, test_user_id)
        print(f"Messages after check: {len(messages)}")
        for msg in messages:
            print(f"  - {msg.role}: {msg.content[:50]}...")
        
        # Test 2: Force completion message
        print("\n🔍 Test 2: Forcing completion message...")
        result = await chat_service.force_completion_message(test_session_id, test_user_id)
        print(f"Result: {result}")
        
        # Get updated messages again
        messages = await chat_service.get_session_messages(test_session_id, test_user_id)
        print(f"Messages after force: {len(messages)}")
        for msg in messages:
            print(f"  - {msg.role}: {msg.content[:50]}...")
        
        # Test 3: Check processing status
        print("\n🔍 Test 3: Checking processing status...")
        status = await chat_service.check_processing_status(test_session_id, test_user_id)
        print(f"Status: {status}")
        
        print("\n✅ All completion message tests completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            await mongodb.get_collection("chat_sessions").delete_one({"session_id": test_session_id})
            print("🧹 Test session cleaned up")
        except:
            pass
        
        await mongodb.disconnect()
        print("🔌 Database disconnected")

if __name__ == "__main__":
    asyncio.run(test_completion_messages()) 