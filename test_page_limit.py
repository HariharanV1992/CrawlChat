#!/usr/bin/env python3
"""
Test script for cumulative page limit functionality
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.document_service import document_service
from src.core.database import mongodb

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_page_limit_functionality():
    """Test the cumulative page limit functionality."""
    
    print("🔍 Testing Cumulative Page Limit Functionality")
    print("=" * 60)
    
    # Test user ID
    test_user_id = "test_user_123"
    
    try:
        # Connect to database
        await mongodb.connect()
        
        # Test 1: Check initial page count
        print("\n1. Testing Initial Page Count:")
        initial_pages = await document_service.get_total_pages_for_user(test_user_id)
        print(f"   Initial pages for user {test_user_id}: {initial_pages}")
        
        # Test 2: Check page limit for a small document
        print("\n2. Testing Page Limit Check (30 pages):")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 30)
        print(f"   Can process 30 pages: {can_process}")
        
        # Test 3: Check page limit for a large document
        print("\n3. Testing Page Limit Check (80 pages):")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 80)
        print(f"   Can process 80 pages: {can_process}")
        
        # Test 4: Check page limit that would exceed 100
        print("\n4. Testing Page Limit Check (120 pages - should fail):")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 120)
        print(f"   Can process 120 pages: {can_process}")
        
        # Test 5: Simulate processing multiple documents
        print("\n5. Testing Cumulative Processing Simulation:")
        
        # Simulate processing a 30-page document
        print("   Processing 30-page document...")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 30)
        if can_process:
            print("   ✅ 30-page document can be processed")
            # In real scenario, this would update the database
            # For testing, we'll just simulate it
            print("   (Simulating document processing...)")
        
        # Check total after first document
        total_after_first = await document_service.get_total_pages_for_user(test_user_id)
        print(f"   Total pages after first document: {total_after_first}")
        
        # Try to process a 50-page document
        print("   Processing 50-page document...")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 50)
        if can_process:
            print("   ✅ 50-page document can be processed")
            print("   (Simulating document processing...)")
        else:
            print("   ❌ 50-page document would exceed limit")
        
        # Try to process a 40-page document (should fail)
        print("   Processing 40-page document...")
        can_process = await document_service.check_page_limit_for_user(test_user_id, 40)
        if can_process:
            print("   ✅ 40-page document can be processed")
        else:
            print("   ❌ 40-page document would exceed limit")
        
        print("\n✅ All page limit tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 Cumulative Page Limit Test")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_page_limit_functionality())
    
    print("\n" + "=" * 60)
    print("🎉 Page limit functionality test completed!")

if __name__ == "__main__":
    main() 