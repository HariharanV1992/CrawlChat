#!/usr/bin/env python3
"""
Test script to crawl Business Standard for IDFC First Bank articles using ScrapingBee.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the crawler-service/src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
crawler_src_path = os.path.join(current_dir, 'crawler-service', 'src')
sys.path.insert(0, crawler_src_path)

from crawler.advanced_crawler import AdvancedCrawler, CrawlConfig

async def crawl_business_standard():
    """Crawl Business Standard for IDFC First Bank articles."""
    print("📰 Crawling Business Standard for IDFC First Bank Articles")
    print("="*60)
    
    # ScrapingBee API key
    api_key = "W9GZ5T0DYMJFB2Y7MATVWN0NGQRUTFKJLTU0DY6HJH2D01RE1YNG1FBX4951CO9WQD4OKD5O62ICX31O"
    
    # Target URL
    target_url = "https://www.business-standard.com/advance-search?keyword=idfcfirstbank"
    
    print(f"🔑 Using ScrapingBee API key: {api_key[:10]}...")
    print(f"🎯 Target URL: {target_url}")
    
    # Configuration optimized for news websites
    config = CrawlConfig(
        scrapingbee_api_key=api_key,
        scrapingbee_options={
            "premium_proxy": True,      # Use premium proxies for news sites
            "country_code": "in",       # Use India-based proxies
            "render_js": True,          # Enable JavaScript rendering
            "wait": 3000,               # Wait 3 seconds for content to load
            "block_ads": True,          # Block advertisements
            "block_resources": False,   # Load images and CSS
            "window_width": 1920,       # Desktop viewport
            "window_height": 1080,
            "device": "desktop",
            "session_id": 123,          # Use same session for consistency
        },
        use_proxy=True,
        max_pages=5,                    # Crawl 5 pages as requested
        max_documents=10,               # Download up to 10 documents
        max_workers=3,                  # Use 3 concurrent workers
        delay=2.0,                      # 2 second delay between requests
        single_page_mode=False,         # Enable multi-page crawling
        request_timeout=60,             # 60 second timeout per request
        page_timeout=120,               # 2 minute timeout per page
    )
    
    print("\n⚙️ Configuration:")
    print(f"   - Max pages: {config.max_pages}")
    print(f"   - Max documents: {config.max_documents}")
    print(f"   - Workers: {config.max_workers}")
    print(f"   - Delay: {config.delay}s")
    print(f"   - Proxy: Premium (India)")
    print(f"   - JavaScript: Enabled")
    
    # Create crawler
    crawler = AdvancedCrawler(target_url, config)
    
    print("\n🚀 Starting crawl...")
    print("-" * 40)
    
    try:
        await crawler.crawl()
        
        print("\n" + "="*60)
        print("✅ Crawl completed successfully!")
        print("="*60)
        
        # Print statistics
        print(f"\n📊 Crawl Statistics:")
        print(f"   - Pages crawled: {crawler.pages_crawled}")
        print(f"   - Documents downloaded: {crawler.documents_downloaded}")
        print(f"   - Requests made: {crawler.stats['requests_made']}")
        print(f"   - Requests failed: {crawler.stats['requests_failed']}")
        print(f"   - Bytes downloaded: {crawler.stats['bytes_downloaded']:,}")
        
        if crawler.proxy_manager:
            proxy_stats = crawler.proxy_manager.get_stats()
            print(f"\n🌐 Proxy Statistics:")
            print(f"   - Proxy requests: {proxy_stats['proxy_requests']}")
            print(f"   - Proxy failures: {proxy_stats['proxy_failures']}")
            print(f"   - Success rate: {proxy_stats['success_rate']}%")
        
        print(f"\n📁 Output directory: {crawler.output_dir}")
        print(f"💾 Files saved locally and uploaded to S3 (if configured)")
        
    except Exception as e:
        print(f"\n❌ Crawl failed: {e}")
        import traceback
        traceback.print_exc()

async def test_different_configurations():
    """Test different ScrapingBee configurations for the same URL."""
    print("\n🧪 Testing Different Configurations")
    print("="*50)
    
    api_key = "W9GZ5T0DYMJFB2Y7MATVWN0NGQRUTFKJLTU0DY6HJH2D01RE1YNG1FBX4951CO9WQD4OKD5O62ICX31O"
    target_url = "https://www.business-standard.com/advance-search?keyword=idfcfirstbank"
    
    configurations = [
        {
            "name": "Basic (Standard Proxy)",
            "options": {
                "render_js": True,
                "country_code": "in",
                "premium_proxy": False,
            }
        },
        {
            "name": "Premium Proxy",
            "options": {
                "premium_proxy": True,
                "country_code": "in",
                "render_js": True,
                "wait": 2000,
            }
        },
        {
            "name": "Stealth Proxy",
            "options": {
                "stealth_proxy": True,
                "country_code": "in",
                "render_js": True,
                "wait": 5000,
            }
        }
    ]
    
    for i, config_info in enumerate(configurations, 1):
        print(f"\n{i}. Testing {config_info['name']}...")
        
        config = CrawlConfig(
            scrapingbee_api_key=api_key,
            scrapingbee_options=config_info["options"],
            use_proxy=True,
            max_pages=1,  # Just test 1 page per configuration
            max_documents=1,
            max_workers=1,
            delay=1.0,
            single_page_mode=True,
        )
        
        crawler = AdvancedCrawler(target_url, config)
        
        try:
            await crawler.crawl()
            print(f"   ✅ {config_info['name']} - Success!")
        except Exception as e:
            print(f"   ❌ {config_info['name']} - Failed: {e}")

async def main():
    """Main function."""
    print("🎯 Business Standard IDFC First Bank Crawler")
    print("="*60)
    
    # Main crawl
    await crawl_business_standard()
    
    # Uncomment to test different configurations
    # await test_different_configurations()
    
    print("\n🎉 All tests completed!")
    print("\n💡 Tips:")
    print("  - Check the output directory for downloaded files")
    print("  - Monitor your ScrapingBee credit usage")
    print("  - Adjust proxy settings if you encounter issues")
    print("  - Use stealth proxies for very difficult sites")

if __name__ == "__main__":
    asyncio.run(main()) 