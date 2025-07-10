#!/usr/bin/env python3
"""
Test script for country_code parameter in AdvancedCrawler
"""

import os
import sys
import time
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_country_code():
    """Test the country_code parameter functionality."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URL
    test_url = "https://example.com"
    
    # Popular country codes to test
    countries = [
        ("in", "India (default)"),
        ("us", "United States"),
        ("gb", "United Kingdom"),
        ("de", "Germany"),
        ("br", "Brazil"),
        ("mx", "Mexico"),
        ("ru", "Russia"),
        ("ca", "Canada"),
        ("au", "Australia"),
        ("jp", "Japan"),
    ]
    
    print(f"\n🌐 Testing Country Code Parameter")
    print("=" * 60)
    print(f"Test URL: {test_url}")
    print("=" * 60)
    
    results = []
    
    for country_code, country_name in countries:
        print(f"\n📋 Testing: {country_name} ({country_code})")
        print("-" * 40)
        
        start_time = time.time()
        result = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=False,  # Use standard proxy to test country codes
            country_code=country_code
        )
        crawl_time = time.time() - start_time
        
        print(f"   ✅ Status: {result['status_code']}")
        print(f"   ⏱️  Time: {crawl_time:.2f}s")
        print(f"   📏 Content length: {result.get('content_length', 0)} chars")
        print(f"   🌍 Country: {country_code.upper()}")
        
        # Store results for comparison
        results.append({
            'country_code': country_code,
            'country_name': country_name,
            'status_code': result['status_code'],
            'crawl_time': crawl_time,
            'success': result.get('success', False),
            'content_length': result.get('content_length', 0)
        })
        
        # Brief delay between requests
        time.sleep(1)
    
    # Summary comparison
    print("\n📊 Country Code Performance Summary")
    print("=" * 60)
    print(f"{'Country':<15} {'Code':<5} {'Status':<8} {'Time':<8} {'Success':<8} {'Content':<10}")
    print("-" * 60)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{result['country_name']:<15} {result['country_code']:<5} {result['status_code']:<8} {result['crawl_time']:<8.2f} {status_icon:<8} {result['content_length']:<10}")
    
    # Premium proxy with country code test
    print("\n🔍 Testing Premium Proxy with Country Code")
    print("=" * 60)
    
    premium_countries = [
        ("us", "United States"),
        ("gb", "United Kingdom"),
        ("de", "Germany"),
    ]
    
    for country_code, country_name in premium_countries:
        print(f"\n📋 Premium Proxy: {country_name} ({country_code})")
        print("-" * 40)
        
        start_time = time.time()
        result = crawler.crawl_url(
            url=test_url,
            render_js=True,
            premium_proxy=True,  # Use premium proxy
            country_code=country_code
        )
        crawl_time = time.time() - start_time
        
        print(f"   ✅ Status: {result['status_code']}")
        print(f"   ⏱️  Time: {crawl_time:.2f}s")
        print(f"   📏 Content length: {result.get('content_length', 0)} chars")
        print(f"   🌍 Country: {country_code.upper()}")
        print(f"   💰 Cost: ~25 credits (premium + JS)")
        
        time.sleep(1)
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use country_code to access region-specific content")
    print("   - Combine with premium_proxy=True for hard-to-scrape sites")
    print("   - Popular codes: 'us', 'gb', 'de', 'in', 'br', 'mx', 'ru'")
    print("   - Default is 'in' (India)")
    print("   - Useful for avoiding geo-blocking")
    print("   - Premium proxies from specific countries cost 25 credits with JS")

if __name__ == "__main__":
    test_country_code() 