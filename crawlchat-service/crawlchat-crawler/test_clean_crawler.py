#!/usr/bin/env python3
"""
Simple test script for the clean crawler
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from crawler.advanced_crawler import AdvancedCrawler
        from crawler.enhanced_scrapingbee_manager import EnhancedScrapingBeeManager
        from crawler.proxy_manager import ProxyManager
        from crawler.file_downloader import FileDownloader
        from crawler.utils import clean_filename, get_file_extension
        from config.crawler_config import CrawlerConfig
        
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration."""
    try:
        from config.crawler_config import CrawlerConfig
        
        # Test ScrapingBee params
        params = CrawlerConfig.get_scrapingbee_params()
        assert 'render_js' in params
        assert 'window_width' in params
        
        # Test crawl config
        config = CrawlerConfig.get_crawl_config()
        assert 'max_documents' in config
        assert 'max_pages' in config
        
        print("✅ Configuration working correctly")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_crawler_initialization():
    """Test crawler initialization (without API key)."""
    try:
        from crawler.advanced_crawler import AdvancedCrawler
        
        # This should fail gracefully without API key
        try:
            crawler = AdvancedCrawler(api_key="test")
            print("✅ Crawler initialization test passed")
            return True
        except Exception as e:
            if "API key" in str(e) or "invalid" in str(e).lower():
                print("✅ Crawler initialization test passed (expected API key error)")
                return True
            else:
                print(f"❌ Unexpected error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Crawler test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Clean Crawler Structure")
    print("=" * 40)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Crawler Initialization", test_crawler_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Clean crawler is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 