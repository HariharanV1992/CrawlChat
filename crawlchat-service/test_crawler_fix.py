#!/usr/bin/env python3
"""
Test script to verify the crawler service fix
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the common module to path
sys.path.insert(0, str(Path(__file__).parent))

def test_advanced_crawler_import():
    """Test that AdvancedCrawler can be imported and has the correct methods."""
    try:
        from common.src.services.crawler_service import get_advanced_crawler
        AdvancedCrawler = get_advanced_crawler()
        
        if AdvancedCrawler is None:
            print("❌ AdvancedCrawler is None")
            return False
        
        print("✅ AdvancedCrawler imported successfully")
        
        # Check __init__ signature
        import inspect
        init_signature = inspect.signature(AdvancedCrawler.__init__)
        init_params = list(init_signature.parameters.keys())
        
        print(f"✅ AdvancedCrawler __init__ parameters: {init_params}")
        
        # Verify it's the lambda-service version (should have api_key, not base_url)
        if 'base_url' in init_params:
            print("❌ AdvancedCrawler has base_url parameter (crawler-service version)")
            return False
        
        if 'api_key' in init_params:
            print("✅ AdvancedCrawler has api_key parameter (lambda-service version)")
        else:
            print("❌ AdvancedCrawler missing api_key parameter")
            return False
        
        # Check for crawl_url method
        if hasattr(AdvancedCrawler, 'crawl_url'):
            print("✅ AdvancedCrawler has crawl_url method")
        else:
            print("❌ AdvancedCrawler missing crawl_url method")
            return False
        
        # Check that it doesn't have crawl method (which was causing the error)
        if hasattr(AdvancedCrawler, 'crawl'):
            print("⚠️  AdvancedCrawler has crawl method (this might cause confusion)")
        else:
            print("✅ AdvancedCrawler correctly doesn't have crawl method")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing AdvancedCrawler: {e}")
        return False

def test_crawler_instantiation():
    """Test that AdvancedCrawler can be instantiated with the correct parameters."""
    try:
        from common.src.services.crawler_service import get_advanced_crawler
        AdvancedCrawler = get_advanced_crawler()
        
        if AdvancedCrawler is None:
            print("❌ AdvancedCrawler is None")
            return False
        
        # Test instantiation with api_key parameter
        api_key = "test_key"
        crawler = AdvancedCrawler(api_key=api_key)
        print("✅ AdvancedCrawler instantiated successfully with api_key")
        
        # Test instantiation with settings parameter
        settings = {"test": "value"}
        crawler2 = AdvancedCrawler(api_key=api_key, settings=settings)
        print("✅ AdvancedCrawler instantiated successfully with api_key and settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Error instantiating AdvancedCrawler: {e}")
        return False

def test_crawl_url_method():
    """Test that the crawl_url method exists and has the expected signature."""
    try:
        from common.src.services.crawler_service import get_advanced_crawler
        AdvancedCrawler = get_advanced_crawler()
        
        if AdvancedCrawler is None:
            print("❌ AdvancedCrawler is None")
            return False
        
        # Check crawl_url method signature
        import inspect
        crawl_url_signature = inspect.signature(AdvancedCrawler.crawl_url)
        crawl_url_params = list(crawl_url_signature.parameters.keys())
        
        print(f"✅ crawl_url method parameters: {crawl_url_params}")
        
        # Should have url as first parameter
        if 'url' in crawl_url_params:
            print("✅ crawl_url method has url parameter")
        else:
            print("❌ crawl_url method missing url parameter")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking crawl_url method: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing AdvancedCrawler Import and Configuration")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_advanced_crawler_import),
        ("Instantiation Test", test_crawler_instantiation),
        ("Method Test", test_crawl_url_method),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The crawler fix should work.")
        return True
    else:
        print("⚠️  Some tests failed. The crawler may still have issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 