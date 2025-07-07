#!/usr/bin/env python3
"""
Simple test script to verify crawler functionality.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from crawler.advanced_crawler import AdvancedCrawler
from models.crawler import CrawlConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_crawl():
    """Test crawling a simple page."""
    print("\n=== Simple Crawl Test ===")
    
    # Configuration for simple crawling
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.1,
        use_proxy=False,  # No proxy for simple test
        proxy_api_key=None,
        render=False,
        retry=1
    )
    
    # Test with a simple, reliable URL
    url = "https://httpbin.org/html"
    
    try:
        print(f"🚀 Starting crawl of: {url}")
        print(f"📊 Configuration: {config.max_pages} pages, {config.max_documents} documents")
        
        crawler = AdvancedCrawler(
            api_key="",  # No API key for simple test
            base_url=url,
            output_dir="/tmp/simple_test",
            max_depth=1,
            max_pages=config.max_pages,
            delay=config.delay,
            site_type='generic'
        )
        
        results = await crawler.crawl(url)
        
        print(f"\n✅ Crawl completed!")
        print(f"📁 Files downloaded: {len(results.get('downloaded_files', []))}")
        print(f"📊 Crawling stats: {results.get('crawling_stats', {})}")
        
        # Show downloaded files
        if results.get('downloaded_files'):
            print("\n📄 Downloaded files:")
            for file_path in results['downloaded_files']:
                print(f"  - {file_path}")
        else:
            print("\n⚠️  No files were downloaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Crawl failed: {e}")
        logger.error(f"Crawl error: {e}", exc_info=True)
        return False

async def test_with_proxy():
    """Test crawling with ScrapingBee proxy."""
    print("\n=== Proxy Crawl Test ===")
    
    # Get API key from environment
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        print("⚠️  No SCRAPINGBEE_API_KEY environment variable found.")
        print("💡 Set your API key: export SCRAPINGBEE_API_KEY='your_key_here'")
        return False
    
    config = CrawlConfig(
        max_documents=2,
        max_pages=3,
        max_workers=1,
        delay=0.2,
        use_proxy=True,
        proxy_api_key=api_key,
        render=True,
        retry=2
    )
    
    crawler = AdvancedCrawler(
        api_key=api_key,
        base_url="https://httpbin.org/ip",
        output_dir="/tmp/proxy_test",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='generic'
    )
    
    url = "https://httpbin.org/ip"
    
    try:
        print(f"🚀 Starting proxy crawl of: {url}")
        
        results = await crawler.crawl(url)
        
        print(f"✅ Proxy crawl completed!")
        print(f"📁 Files downloaded: {len(results.get('downloaded_files', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Proxy crawl failed: {e}")
        return False

async def main():
    """Run simple crawl tests."""
    print("🚀 Starting Simple Crawler Tests")
    print("=" * 50)
    
    tests = [
        test_simple_crawl,
        test_with_proxy
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
    
    print("\n📁 Check the following directories for downloaded files:")
    print("  - /tmp/simple_test/")
    print("  - /tmp/proxy_test/")

if __name__ == "__main__":
    asyncio.run(main()) 