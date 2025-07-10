#!/usr/bin/env python3
"""
Test script for premium_proxy parameter in AdvancedCrawler
"""

import os
import sys
import time
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_premium_proxy():
    """Test the premium_proxy parameter functionality."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URLs - some that might benefit from premium proxies
    test_urls = [
        "https://example.com",  # Basic test
        "https://www.google.com",  # Search engine (often blocked)
        "https://www.amazon.com",  # E-commerce (can be challenging)
    ]
    
    print(f"\n🌐 Testing Premium Proxy Parameter")
    print("=" * 60)
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n📋 Test {i}: {test_url}")
        print("-" * 40)
        
        # Test 1: Standard proxy (default)
        print("   🔄 Standard proxy (default)")
        start_time = time.time()
        result1 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=False  # Standard proxy
        )
        crawl_time1 = time.time() - start_time
        
        print(f"   ✅ Status: {result1['status_code']}")
        print(f"   ⏱️  Time: {crawl_time1:.2f}s")
        print(f"   📏 Content length: {result1.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~1 credit (with JS)")
        
        # Test 2: Premium proxy
        print("\n   🔄 Premium proxy")
        start_time = time.time()
        result2 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=True  # Premium proxy
        )
        crawl_time2 = time.time() - start_time
        
        print(f"   ✅ Status: {result2['status_code']}")
        print(f"   ⏱️  Time: {crawl_time2:.2f}s")
        print(f"   📏 Content length: {result2.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~25 credits (with JS)")
        
        # Test 3: Premium proxy without JavaScript
        print("\n   🔄 Premium proxy (no JavaScript)")
        start_time = time.time()
        result3 = crawler.crawl_url(
            url=test_url,
            render_js=False,
            premium_proxy=True  # Premium proxy, no JS
        )
        crawl_time3 = time.time() - start_time
        
        print(f"   ✅ Status: {result3['status_code']}")
        print(f"   ⏱️  Time: {crawl_time3:.2f}s")
        print(f"   📏 Content length: {result3.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~10 credits (no JS)")
        
        # Performance comparison
        print(f"\n📊 Performance Comparison for {test_url}:")
        print(f"   Standard proxy:     {crawl_time1:.2f}s")
        print(f"   Premium proxy:      {crawl_time2:.2f}s")
        print(f"   Premium (no JS):    {crawl_time3:.2f}s")
        
        # Success rate comparison
        success1 = result1.get('success', False)
        success2 = result2.get('success', False)
        success3 = result3.get('success', False)
        
        print(f"\n📈 Success Rate:")
        print(f"   Standard proxy:     {'✅' if success1 else '❌'}")
        print(f"   Premium proxy:      {'✅' if success2 else '❌'}")
        print(f"   Premium (no JS):    {'✅' if success3 else '❌'}")
        
        if i < len(test_urls):
            print("\n" + "="*60)
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use premium_proxy=True for hard-to-scrape sites")
    print("   - Premium proxies cost 25 credits with JavaScript, 10 without")
    print("   - Recommended for: search engines, social networks, e-commerce")
    print("   - Standard proxies are sufficient for most regular websites")
    print("   - Premium proxies are rarely blocked and more reliable")

if __name__ == "__main__":
    test_premium_proxy() 