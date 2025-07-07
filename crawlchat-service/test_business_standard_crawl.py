#!/usr/bin/env python3
"""
Test script for crawling Business Standard with ScrapingBee.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the common module to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from crawler.advanced_crawler import AdvancedCrawler
from models.crawler import CrawlConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_business_standard_crawl():
    """Test crawling Business Standard for IDFC First Bank articles."""
    print("\n=== Business Standard Crawl Test ===")
    
    # Configuration for Business Standard crawling
    config = CrawlConfig(
        max_documents=10,
        max_pages=20,
        max_workers=3,
        delay=0.2,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=True,
        retry=3
    )
    
    # Initialize crawler with Business Standard specific settings
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/business_standard_crawl",
        max_depth=2,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='news'  # Use news site type for better handling
    )
    
    # Target URL - Business Standard search for IDFC First Bank
    url = "https://www.business-standard.com/search?q=IDFC+First+Bank"
    
    try:
        print(f"🚀 Starting crawl of: {url}")
        print(f"📊 Configuration: {config.max_pages} pages, {config.max_documents} documents")
        
        results = await crawler.crawl(url)
        
        print(f"\n✅ Crawl completed successfully!")
        print(f"📁 Files downloaded: {len(results.get('downloaded_files', []))}")
        print(f"📊 Crawling stats: {results.get('crawling_stats', {})}")
        
        # Show downloaded files
        if results.get('downloaded_files'):
            print("\n📄 Downloaded files:")
            for file_path in results['downloaded_files']:
                print(f"  - {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Crawl failed: {e}")
        logger.error(f"Crawl error: {e}", exc_info=True)
        return False

async def test_business_standard_article():
    """Test crawling a specific Business Standard article."""
    print("\n=== Business Standard Article Test ===")
    
    config = CrawlConfig(
        max_documents=5,
        max_pages=5,
        max_workers=2,
        delay=0.3,
        use_proxy=True,
        proxy_api_key="your_scrapingbee_api_key_here",
        render=True,
        retry=2
    )
    
    crawler = AdvancedCrawler(
        api_key=config.proxy_api_key,
        output_dir="/tmp/business_standard_article",
        max_depth=1,
        max_pages=config.max_pages,
        delay=config.delay,
        site_type='news'
    )
    
    # Example article URL (replace with actual article)
    url = "https://www.business-standard.com/article/companies/idfc-first-bank-q4-results"
    
    try:
        print(f"🚀 Starting article crawl: {url}")
        
        results = await crawler.crawl(url)
        
        print(f"✅ Article crawl completed!")
        print(f"📁 Files downloaded: {len(results.get('downloaded_files', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Article crawl failed: {e}")
        return False

async def main():
    """Run Business Standard crawling tests."""
    print("🚀 Starting Business Standard Crawling Tests")
    print("=" * 60)
    
    # Check if API key is provided
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        print("⚠️  No SCRAPINGBEE_API_KEY environment variable found.")
        print("💡 Set your API key: export SCRAPINGBEE_API_KEY='your_key_here'")
        print("   Or replace 'your_scrapingbee_api_key_here' in the code with your actual key.")
        print("\n📝 Configuration Guide:")
        print("1. Get your ScrapingBee API key from: https://www.scrapingbee.com/")
        print("2. Set environment variable: export SCRAPINGBEE_API_KEY='your_key'")
        print("3. Run: python test_business_standard_crawl.py")
        return
    
    print(f"✅ Using ScrapingBee API key: {api_key[:10]}...")
    
    # Update configs with actual API key
    global config
    config = CrawlConfig(
        max_documents=10,
        max_pages=20,
        max_workers=3,
        delay=0.2,
        use_proxy=True,
        proxy_api_key=api_key,
        render=True,
        retry=3
    )
    
    tests = [
        test_business_standard_crawl,
        test_business_standard_article
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All Business Standard tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📁 Check the following directories for downloaded files:")
    print("  - /tmp/business_standard_crawl/")
    print("  - /tmp/business_standard_article/")

if __name__ == "__main__":
    asyncio.run(main()) 