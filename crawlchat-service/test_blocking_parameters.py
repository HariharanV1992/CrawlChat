#!/usr/bin/env python3
"""
Test script for block_ads and block_resources parameters in AdvancedCrawler
"""

import os
import sys
import time
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_blocking_parameters():
    """Test the new block_ads and block_resources parameters."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URL (a simple page that might have ads)
    test_url = "https://example.com"
    
    print(f"\n🌐 Testing URL: {test_url}")
    print("=" * 60)
    
    # Test 1: Default settings (block_resources=True, block_ads=False)
    print("\n📋 Test 1: Default settings")
    print("   - block_resources: True (default)")
    print("   - block_ads: False (default)")
    
    start_time = time.time()
    result1 = crawler.crawl_url(
        url=test_url,
        render_js=True,
        block_resources=True,  # Block images and CSS
        block_ads=False       # Don't block ads
    )
    crawl_time1 = time.time() - start_time
    
    print(f"   ✅ Status: {result1['status_code']}")
    print(f"   ⏱️  Time: {crawl_time1:.2f}s")
    print(f"   📏 Content length: {result1.get('content_length', 0)} chars")
    
    # Test 2: Block ads
    print("\n📋 Test 2: Block ads")
    print("   - block_resources: True")
    print("   - block_ads: True")
    
    start_time = time.time()
    result2 = crawler.crawl_url(
        url=test_url,
        render_js=True,
        block_resources=True,
        block_ads=True      # Block ads
    )
    crawl_time2 = time.time() - start_time
    
    print(f"   ✅ Status: {result2['status_code']}")
    print(f"   ⏱️  Time: {crawl_time2:.2f}s")
    print(f"   📏 Content length: {result2.get('content_length', 0)} chars")
    
    # Test 3: Allow all resources (no blocking)
    print("\n📋 Test 3: Allow all resources")
    print("   - block_resources: False")
    print("   - block_ads: False")
    
    start_time = time.time()
    result3 = crawler.crawl_url(
        url=test_url,
        render_js=True,
        block_resources=False,  # Allow images and CSS
        block_ads=False        # Don't block ads
    )
    crawl_time3 = time.time() - start_time
    
    print(f"   ✅ Status: {result3['status_code']}")
    print(f"   ⏱️  Time: {crawl_time3:.2f}s")
    print(f"   📏 Content length: {result3.get('content_length', 0)} chars")
    
    # Test 4: Block everything (max speed)
    print("\n📋 Test 4: Block everything (max speed)")
    print("   - block_resources: True")
    print("   - block_ads: True")
    
    start_time = time.time()
    result4 = crawler.crawl_url(
        url=test_url,
        render_js=True,
        block_resources=True,  # Block images and CSS
        block_ads=True        # Block ads
    )
    crawl_time4 = time.time() - start_time
    
    print(f"   ✅ Status: {result4['status_code']}")
    print(f"   ⏱️  Time: {crawl_time4:.2f}s")
    print(f"   📏 Content length: {result4.get('content_length', 0)} chars")
    
    # Test 5: No JavaScript rendering (blocking parameters ignored)
    print("\n📋 Test 5: No JavaScript rendering")
    print("   - render_js: False")
    print("   - block_resources: True (ignored)")
    print("   - block_ads: True (ignored)")
    
    start_time = time.time()
    result5 = crawler.crawl_url(
        url=test_url,
        render_js=False,      # No JavaScript rendering
        block_resources=True, # This will be ignored
        block_ads=True        # This will be ignored
    )
    crawl_time5 = time.time() - start_time
    
    print(f"   ✅ Status: {result5['status_code']}")
    print(f"   ⏱️  Time: {crawl_time5:.2f}s")
    print(f"   📏 Content length: {result5.get('content_length', 0)} chars")
    
    # Performance comparison
    print("\n📊 Performance Comparison:")
    print("=" * 60)
    print(f"Default settings:     {crawl_time1:.2f}s")
    print(f"Block ads:           {crawl_time2:.2f}s")
    print(f"Allow all resources: {crawl_time3:.2f}s")
    print(f"Block everything:    {crawl_time4:.2f}s")
    print(f"No JavaScript:       {crawl_time5:.2f}s")
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use block_ads=True to avoid scraping ads (faster)")
    print("   - Use block_resources=True to block images/CSS (faster)")
    print("   - These parameters only work when render_js=True")
    print("   - For maximum speed: block_ads=True + block_resources=True")
    print("   - For complete content: block_ads=False + block_resources=False")

if __name__ == "__main__":
    test_blocking_parameters() 