#!/usr/bin/env python3
"""
Test script to demonstrate ScrapingBee integration with different proxy configurations.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the common module to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from crawler.advanced_crawler import AdvancedCrawler
from models.crawler import CrawlConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_scrapingbee():
    """Test basic ScrapingBee functionality."""
    print("\n=== Basic ScrapingBee Test ===")
    
    config = CrawlConfig(
        max_documents=5,
        max_pages=10,
        max_workers=2,
        delay=0.1,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=False,
        retry=3
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_basic",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/ip"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Basic test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

async def test_premium_proxy():
    """Test premium proxy functionality."""
    print("\n=== Premium Proxy Test ===")
    
    config = CrawlConfig(
        max_documents=3,
        max_pages=5,
        max_workers=1,
        delay=0.2,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=True,
        retry=2
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_premium",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/headers"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Premium proxy test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Premium proxy test failed: {e}")
        return False

async def test_stealth_mode():
    """Test stealth mode functionality."""
    print("\n=== Stealth Mode Test ===")
    
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.3,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=True,
        retry=1
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_stealth",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/user-agent"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Stealth mode test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Stealth mode test failed: {e}")
        return False

async def test_geolocation():
    """Test geolocation functionality."""
    print("\n=== Geolocation Test ===")
    
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.2,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=False,
        retry=2
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_geo",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/ip"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Geolocation test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Geolocation test failed: {e}")
        return False

async def test_own_proxy():
    """Test own proxy functionality."""
    print("\n=== Own Proxy Test ===")
    
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.2,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=False,
        retry=2
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_own_proxy",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/ip"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Own proxy test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Own proxy test failed: {e}")
        return False

async def test_advanced_features():
    """Test advanced ScrapingBee features."""
    print("\n=== Advanced Features Test ===")
    
    config = CrawlConfig(
        max_documents=3,
        max_pages=5,
        max_workers=2,
        delay=0.1,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=True,
        retry=3
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/test_advanced",
        max_depth=2,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/html"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ Advanced features test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ Advanced features test failed: {e}")
        return False

async def test_no_proxy():
    """Test without proxy functionality."""
    print("\n=== No Proxy Test ===")
    
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.1,
        use_proxy=False,
        proxy_api_key=None,
        render=False,
        retry=1
    )
    
    crawler = AdvancedCrawler(
        api_key="",
        output_dir="/tmp/test_no_proxy",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/ip"
    
    try:
        results = await crawler.crawl(url)
        print(f"✅ No proxy test completed: {len(results.get('downloaded_files', []))} files downloaded")
        return True
    except Exception as e:
        print(f"❌ No proxy test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting ScrapingBee Crawler Tests")
    print("=" * 50)
    
    tests = [
        test_basic_scrapingbee,
        test_premium_proxy,
        test_stealth_mode,
        test_geolocation,
        test_own_proxy,
        test_advanced_features,
        test_no_proxy
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Configuration Guide:")
    print("To use these tests with your ScrapingBee API key:")
    print("1. Replace 'your_scrapingbee_api_key_here' with your actual API key")
    print("2. Run: python test_scrapingbee_crawler.py")
    print("3. Check the /tmp/test_* directories for downloaded files")

if __name__ == "__main__":
    asyncio.run(main()) 