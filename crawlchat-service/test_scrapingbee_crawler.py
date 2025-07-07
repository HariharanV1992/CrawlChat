#!/usr/bin/env python3
"""
Test script to demonstrate ScrapingBee integration with different proxy configurations.
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

async def test_basic_scrapingbee():
    """Test basic ScrapingBee with default settings."""
    print("🔧 Testing Basic ScrapingBee Configuration...")
    
    config = CrawlConfig(
        scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
        scrapingbee_options={
            "render_js": True,
            "country_code": "us",
            "premium_proxy": False,  # Use standard proxies
        },
        use_proxy=True,
        max_pages=2,
        max_documents=1,
        max_workers=2,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/headers", config)
    
    try:
        await crawler.crawl()
        print("✅ Basic ScrapingBee test completed!")
    except Exception as e:
        print(f"❌ Basic ScrapingBee test failed: {e}")

async def test_premium_proxy():
    """Test ScrapingBee with premium proxies."""
    print("\n🚀 Testing Premium Proxy Configuration...")
    
    config = CrawlConfig(
        scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
        scrapingbee_options={
            "premium_proxy": True,
            "country_code": "us",
            "render_js": True,
        },
        use_proxy=True,
        max_pages=1,
        max_documents=1,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/ip", config)
    
    try:
        await crawler.crawl()
        print("✅ Premium proxy test completed!")
    except Exception as e:
        print(f"❌ Premium proxy test failed: {e}")

async def test_stealth_proxy():
    """Test ScrapingBee with stealth proxies."""
    print("\n🕵️ Testing Stealth Proxy Configuration...")
    
    config = CrawlConfig(
        scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
        scrapingbee_options={
            "stealth_proxy": True,
            "country_code": "de",  # Germany
            "render_js": True,
        },
        use_proxy=True,
        max_pages=1,
        max_documents=1,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/ip", config)
    
    try:
        await crawler.crawl()
        print("✅ Stealth proxy test completed!")
    except Exception as e:
        print(f"❌ Stealth proxy test failed: {e}")

async def test_geolocation():
    """Test ScrapingBee with different geolocations."""
    print("\n🌍 Testing Geolocation Configuration...")
    
    countries = ["us", "in", "gb", "de", "jp"]
    
    for country in countries:
        print(f"  Testing {country.upper()} location...")
        
        config = CrawlConfig(
            scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
            scrapingbee_options={
                "premium_proxy": True,
                "country_code": country,
                "render_js": True,
            },
            use_proxy=True,
            max_pages=1,
            max_documents=1,
            single_page_mode=True
        )
        
        crawler = AdvancedCrawler("https://httpbin.org/ip", config)
        
        try:
            await crawler.crawl()
            print(f"    ✅ {country.upper()} test completed!")
        except Exception as e:
            print(f"    ❌ {country.upper()} test failed: {e}")

async def test_own_proxy():
    """Test ScrapingBee with your own proxy."""
    print("\n🔑 Testing Own Proxy Configuration...")
    
    config = CrawlConfig(
        scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
        scrapingbee_options={
            "own_proxy": "https://username:password@your-proxy-host:port",  # Replace with your proxy
            "render_js": True,
        },
        use_proxy=True,
        max_pages=1,
        max_documents=1,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/ip", config)
    
    try:
        await crawler.crawl()
        print("✅ Own proxy test completed!")
    except Exception as e:
        print(f"❌ Own proxy test failed: {e}")

async def test_advanced_features():
    """Test ScrapingBee with advanced features."""
    print("\n⚡ Testing Advanced Features...")
    
    config = CrawlConfig(
        scrapingbee_api_key="YOUR_SCRAPINGBEE_API_KEY",  # Replace with your key
        scrapingbee_options={
            "premium_proxy": True,
            "country_code": "us",
            "render_js": True,
            "wait": 2000,  # Wait 2 seconds for JS to load
            "block_ads": True,  # Block ads
            "block_resources": False,  # Load images and CSS
            "window_width": 1920,
            "window_height": 1080,
            "device": "desktop",
        },
        use_proxy=True,
        max_pages=1,
        max_documents=1,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/user-agent", config)
    
    try:
        await crawler.crawl()
        print("✅ Advanced features test completed!")
    except Exception as e:
        print(f"❌ Advanced features test failed: {e}")

async def test_no_proxy():
    """Test without proxy (direct connection)."""
    print("\n🌐 Testing Direct Connection (No Proxy)...")
    
    config = CrawlConfig(
        use_proxy=False,
        max_pages=1,
        max_documents=1,
        single_page_mode=True
    )
    
    crawler = AdvancedCrawler("https://httpbin.org/ip", config)
    
    try:
        await crawler.crawl()
        print("✅ Direct connection test completed!")
    except Exception as e:
        print(f"❌ Direct connection test failed: {e}")

def print_configuration_guide():
    """Print a guide for configuring ScrapingBee."""
    print("\n" + "="*60)
    print("📋 ScrapingBee Configuration Guide")
    print("="*60)
    
    print("\n🔑 Basic Configuration:")
    print("  config = CrawlConfig(")
    print("      scrapingbee_api_key='YOUR_API_KEY',")
    print("      scrapingbee_options={")
    print("          'render_js': True,")
    print("          'country_code': 'us',")
    print("          'premium_proxy': False,")
    print("      },")
    print("      use_proxy=True")
    print("  )")
    
    print("\n🚀 Premium Proxy:")
    print("  scrapingbee_options={")
    print("      'premium_proxy': True,")
    print("      'country_code': 'us',")
    print("  }")
    
    print("\n🕵️ Stealth Proxy:")
    print("  scrapingbee_options={")
    print("      'stealth_proxy': True,")
    print("      'country_code': 'de',")
    print("  }")
    
    print("\n🌍 Geolocation Options:")
    print("  'country_code': 'us'  # United States")
    print("  'country_code': 'in'  # India")
    print("  'country_code': 'gb'  # United Kingdom")
    print("  'country_code': 'de'  # Germany")
    print("  'country_code': 'jp'  # Japan")
    
    print("\n🔑 Own Proxy:")
    print("  scrapingbee_options={")
    print("      'own_proxy': 'https://user:pass@host:port',")
    print("  }")
    
    print("\n⚡ Advanced Features:")
    print("  scrapingbee_options={")
    print("      'wait': 2000,           # Wait 2 seconds")
    print("      'block_ads': True,      # Block advertisements")
    print("      'block_resources': False, # Load images/CSS")
    print("      'window_width': 1920,   # Browser width")
    print("      'window_height': 1080,  # Browser height")
    print("      'device': 'desktop',    # or 'mobile'")
    print("  }")
    
    print("\n💰 Cost Information:")
    print("  - Standard proxy: 1-5 credits")
    print("  - Premium proxy: 10-25 credits")
    print("  - Stealth proxy: 75 credits")
    print("  - AI features: +5 credits")

async def main():
    """Run all tests."""
    print("🧪 ScrapingBee Integration Test Suite")
    print("="*50)
    
    # Check if API key is provided
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        print("⚠️  No SCRAPINGBEE_API_KEY environment variable found!")
        print("   Set it with: export SCRAPINGBEE_API_KEY='your_api_key'")
        print("   Or replace 'YOUR_SCRAPINGBEE_API_KEY' in the script")
        print("\n📋 Configuration Guide:")
        print_configuration_guide()
        return
    
    print(f"✅ Using ScrapingBee API key: {api_key[:10]}...")
    
    # Run tests
    await test_no_proxy()
    await test_basic_scrapingbee()
    await test_premium_proxy()
    await test_stealth_proxy()
    await test_geolocation()
    await test_advanced_features()
    
    print("\n" + "="*50)
    print("🎉 All tests completed!")
    print("\n💡 Tips:")
    print("  - Premium proxies work better for difficult sites")
    print("  - Stealth proxies are best for very hard sites")
    print("  - Use geolocation to match your target audience")
    print("  - Monitor your credit usage in ScrapingBee dashboard")

if __name__ == "__main__":
    asyncio.run(main()) 