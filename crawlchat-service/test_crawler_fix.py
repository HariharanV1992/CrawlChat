#!/usr/bin/env python3
"""
Test script to verify the crawler service fix for get_storage_service import.
"""

import sys
import os
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

def test_crawler_service_import():
    """Test that crawler service can be imported without errors."""
    try:
        print("Testing crawler service import...")
        from common.src.services.crawler_service import crawler_service
        print("✅ Crawler service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Crawler service import failed: {e}")
        return False

def test_storage_service_import():
    """Test that storage service can be imported without errors."""
    try:
        print("Testing storage service import...")
        from common.src.services.storage_service import get_storage_service
        storage_service = get_storage_service()
        print("✅ Storage service imported and instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Storage service import failed: {e}")
        return False

def test_crawler_service_methods():
    """Test that crawler service methods can be called without import errors."""
    try:
        print("Testing crawler service methods...")
        from common.src.services.crawler_service import crawler_service
        
        # Test that the service has the expected methods
        methods = [
            'create_crawl_task',
            'get_task_status', 
            'start_crawl_task',
            'get_crawl_status',
            'cancel_crawl_task',
            'delete_crawl_task'
        ]
        
        for method in methods:
            if hasattr(crawler_service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        print("✅ All crawler service methods are available")
        return True
        
    except Exception as e:
        print(f"❌ Crawler service method test failed: {e}")
        return False

def test_storage_service_methods():
    """Test that storage service methods can be called without errors."""
    try:
        print("Testing storage service methods...")
        from common.src.services.storage_service import get_storage_service
        
        storage_service = get_storage_service()
        
        # Test that the service has the expected methods
        methods = [
            'save_file',
            'get_file',
            'delete_file',
            'list_files',
            'get_file_info',
            'get_storage_info',
            'get_file_content'
        ]
        
        for method in methods:
            if hasattr(storage_service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        # Test get_storage_info method
        info = storage_service.get_storage_info()
        print(f"✅ Storage info: {info}")
        
        print("✅ All storage service methods are available")
        return True
        
    except Exception as e:
        print(f"❌ Storage service method test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing CrawlChat Crawler Service Fix")
    print("=" * 50)
    
    tests = [
        ("Storage Service Import", test_storage_service_import),
        ("Crawler Service Import", test_crawler_service_import),
        ("Storage Service Methods", test_storage_service_methods),
        ("Crawler Service Methods", test_crawler_service_methods),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The crawler service fix is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 