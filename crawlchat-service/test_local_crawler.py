#!/usr/bin/env python3
"""
Local test script to simulate SQS handler and test crawler functionality
"""

import asyncio
import json
import os
import sys

# Add the common module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.src.services.crawler_service import crawler_service
from common.src.core.database import mongodb

async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("=== TESTING MONGODB CONNECTION ===")
    try:
        # Initialize database connection
        await mongodb.connect()
        print("✅ MongoDB connected successfully")
        
        # Test getting a collection
        collection = mongodb.get_collection("tasks")
        print("✅ Database collection access successful")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def test_crawler_service():
    """Test crawler service functionality"""
    print("\n=== TESTING CRAWLER SERVICE ===")
    try:
        # Test getting task status (this is what the SQS handler does)
        task_id = "test-task-id"
        task = await crawler_service.get_task_status(task_id)
        print(f"✅ Task status retrieved: {task}")
        return True
    except Exception as e:
        print(f"❌ Crawler service test failed: {e}")
        return False

async def test_sqs_handler_simulation():
    """Simulate the SQS handler logic"""
    print("\n=== SIMULATING SQS HANDLER ===")
    try:
        # Simulate SQS message
        sqs_message = {
            "task_id": "a5bc5858-9abc-44d7-954d-7df786c745d3",
            "user_id": "7320c5a4-8865-468c-a851-5edc3ad445e2"
        }
        
        print(f"Processing SQS message: {sqs_message}")
        
        # Extract task_id
        task_id = sqs_message["task_id"]
        print(f"Task ID: {task_id}")
        
        # Fetch task from database (this is what was failing in Lambda)
        task = await crawler_service.get_task_status(task_id)
        print(f"✅ Fetched task from DB: {task}")
        
        if task:
            print(f"Task URL: {task.url}")
            print(f"Task status: {task.status}")
            print(f"Max documents: {task.max_documents}")
            print(f"Max pages: {task.max_pages}")
            
            # Test running the crawl task
            print("\n=== TESTING CRAWL EXECUTION ===")
            result = await crawler_service._run_crawl_task(task)
            print(f"✅ Crawl task completed: {result}")
        else:
            print("❌ Task not found in database")
            
        return True
    except Exception as e:
        print(f"❌ SQS handler simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting local crawler test...")
    
    # Test 1: MongoDB connection
    db_ok = await test_mongodb_connection()
    
    if not db_ok:
        print("❌ Cannot proceed without MongoDB connection")
        return
    
    # Test 2: Crawler service
    crawler_ok = await test_crawler_service()
    
    # Test 3: SQS handler simulation
    sqs_ok = await test_sqs_handler_simulation()
    
    print("\n=== TEST SUMMARY ===")
    print(f"MongoDB Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Crawler Service: {'✅ PASS' if crawler_ok else '❌ FAIL'}")
    print(f"SQS Handler: {'✅ PASS' if sqs_ok else '❌ FAIL'}")
    
    if db_ok and crawler_ok and sqs_ok:
        print("\n🎉 All tests passed! The crawler should work in Lambda.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    asyncio.run(main()) 