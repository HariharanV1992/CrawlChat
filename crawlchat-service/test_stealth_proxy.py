#!/usr/bin/env python3
"""
Test script for stealth_proxy parameter in AdvancedCrawler
"""

import os
import sys
import time
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_stealth_proxy():
    """Test the stealth_proxy parameter functionality."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URL
    test_url = "https://example.com"
    
    print(f"\n🌐 Testing Stealth Proxy Parameter")
    print("=" * 60)
    print("⚠️  WARNING: Stealth proxy costs 75 credits per request!")
    print("=" * 60)
    
    # Test 1: Standard proxy (baseline)
    print("\n📋 Test 1: Standard proxy (baseline)")
    print("-" * 40)
    start_time = time.time()
    try:
        result1 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=False,
            stealth_proxy=False
        )
        crawl_time1 = time.time() - start_time
        
        print(f"   ✅ Status: {result1['status_code']}")
        print(f"   ⏱️  Time: {crawl_time1:.2f}s")
        print(f"   📏 Content length: {result1.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~1 credit (with JS)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time1 = None
        result1 = {'success': False}
    
    # Test 2: Premium proxy
    print("\n📋 Test 2: Premium proxy")
    print("-" * 40)
    start_time = time.time()
    try:
        result2 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=True,
            stealth_proxy=False
        )
        crawl_time2 = time.time() - start_time
        
        print(f"   ✅ Status: {result2['status_code']}")
        print(f"   ⏱️  Time: {crawl_time2:.2f}s")
        print(f"   📏 Content length: {result2.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~25 credits (premium + JS)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time2 = None
        result2 = {'success': False}
    
    # Test 3: Stealth proxy
    print("\n📋 Test 3: Stealth proxy (75 credits)")
    print("-" * 40)
    start_time = time.time()
    try:
        result3 = crawler.crawl_url(
            url=test_url,
            render_js=True,  # Required for stealth proxy
            premium_proxy=False,
            stealth_proxy=True
        )
        crawl_time3 = time.time() - start_time
        
        print(f"   ✅ Status: {result3['status_code']}")
        print(f"   ⏱️  Time: {crawl_time3:.2f}s")
        print(f"   📏 Content length: {result3.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~75 credits (stealth + JS)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time3 = None
        result3 = {'success': False}
    
    # Test 4: Stealth proxy with country code
    print("\n📋 Test 4: Stealth proxy + US location")
    print("-" * 40)
    start_time = time.time()
    try:
        result4 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=False,
            stealth_proxy=True,
            country_code="us"
        )
        crawl_time4 = time.time() - start_time
        
        print(f"   ✅ Status: {result4['status_code']}")
        print(f"   ⏱️  Time: {crawl_time4:.2f}s")
        print(f"   📏 Content length: {result4.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~75 credits (stealth + JS + US)")
        print(f"   🌍 Location: US")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time4 = None
        result4 = {'success': False}
    
    # Test 5: Stealth proxy without JS (should fail)
    print("\n📋 Test 5: Stealth proxy without JS (should fail)")
    print("-" * 40)
    try:
        result5 = crawler.crawl_url(
            url=test_url,
            render_js=False,  # This should cause an error
            stealth_proxy=True
        )
        print(f"   ❌ Unexpected success: {result5['status_code']}")
    except ValueError as e:
        print(f"   ✅ Expected error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    # Performance comparison
    print(f"\n📊 Performance Comparison:")
    print("=" * 60)
    if crawl_time1:
        print(f"Standard proxy:     {crawl_time1:.2f}s (1 credit)")
    if crawl_time2:
        print(f"Premium proxy:      {crawl_time2:.2f}s (25 credits)")
    if crawl_time3:
        print(f"Stealth proxy:      {crawl_time3:.2f}s (75 credits)")
    if crawl_time4:
        print(f"Stealth + US:       {crawl_time4:.2f}s (75 credits)")
    
    # Success rate comparison
    print(f"\n📈 Success Rate:")
    print(f"   Standard proxy:     {'✅' if result1.get('success', False) else '❌'}")
    print(f"   Premium proxy:      {'✅' if result2.get('success', False) else '❌'}")
    print(f"   Stealth proxy:      {'✅' if result3.get('success', False) else '❌'}")
    print(f"   Stealth + US:       {'✅' if result4.get('success', False) else '❌'}")
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use stealth_proxy=True for the hardest-to-scrape sites")
    print("   - Stealth proxy costs 75 credits per request")
    print("   - Requires render_js=True (JavaScript rendering)")
    print("   - Can be combined with country_code for geolocation")
    print("   - Not supported: infinite_scroll, custom headers, timeout, evaluate_results")
    print("   - Use only when standard and premium proxies fail")
    print("   - Beta feature - may have limitations")

if __name__ == "__main__":
    test_stealth_proxy() 