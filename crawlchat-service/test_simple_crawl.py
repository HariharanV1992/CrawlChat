#!/usr/bin/env python3
"""
Simple test script to test basic ScrapingBee functionality
"""

import os
import requests
import json

def test_direct_scrapingbee():
    """Test direct ScrapingBee API call."""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not set")
        return False
    
    print("🧪 Testing Direct ScrapingBee API")
    print("=" * 40)
    
    # Test with simple parameters
    url = "https://httpbin.org/ip"
    params = {
        "api_key": api_key,
        "url": url,
        "render_js": "false",  # No JS rendering
        "premium_proxy": "false",
        "stealth_proxy": "false"
    }
    
    try:
        response = requests.get("https://app.scrapingbee.com/api/v1/", params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ Direct ScrapingBee API call successful")
            return True
        else:
            print(f"❌ Direct ScrapingBee API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct ScrapingBee API call: {e}")
        return False

def test_simple_crawler():
    """Test simple crawler without progressive strategy."""
    try:
        from common.src.services.crawler_service import get_advanced_crawler
        
        AdvancedCrawler = get_advanced_crawler()
        if not AdvancedCrawler:
            print("❌ AdvancedCrawler not available")
            return False
        
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            print("❌ SCRAPINGBEE_API_KEY not set")
            return False
        
        print("\n🧪 Testing Simple Crawler")
        print("=" * 40)
        
        # Create crawler
        crawler = AdvancedCrawler(api_key=api_key)
        
        # Test with a simple URL and render_js=False
        result = crawler.crawl_url(
            "https://httpbin.org/ip", 
            content_type="generic",
            render_js=False,  # Disable JavaScript rendering
            timeout=30000,    # 30 second timeout
            wait=0,           # No additional wait
            block_resources=True  # Block resources for speed
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Status Code: {result.get('status_code')}")
        print(f"Content Length: {result.get('content_length', 0)}")
        print(f"Error: {result.get('error', 'None')}")
        
        if result.get('success'):
            print("✅ Simple crawler test successful")
            return True
        else:
            print("❌ Simple crawler test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple crawler test: {e}")
        return False

def test_with_render_js_true():
    """Test crawler with JavaScript rendering enabled."""
    try:
        from common.src.services.crawler_service import get_advanced_crawler
        
        AdvancedCrawler = get_advanced_crawler()
        if not AdvancedCrawler:
            print("❌ AdvancedCrawler not available")
            return False
        
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            print("❌ SCRAPINGBEE_API_KEY not set")
            return False
        
        print("\n🧪 Testing Crawler with JavaScript Rendering")
        print("=" * 40)
        
        # Create crawler
        crawler = AdvancedCrawler(api_key=api_key)
        
        # Test with JavaScript rendering enabled
        result = crawler.crawl_url(
            "https://httpbin.org/ip", 
            content_type="generic",
            render_js=True,   # Enable JavaScript rendering
            timeout=30000,    # 30 second timeout
            wait=2000,        # Wait 2 seconds after page load
            block_resources=True  # Block resources for speed
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Status Code: {result.get('status_code')}")
        print(f"Content Length: {result.get('content_length', 0)}")
        print(f"Error: {result.get('error', 'None')}")
        
        if result.get('success'):
            print("✅ JavaScript rendering test successful")
            return True
        else:
            print("❌ JavaScript rendering test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in JavaScript rendering test: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing ScrapingBee Integration")
    print("=" * 50)
    
    test1_passed = test_direct_scrapingbee()
    test2_passed = test_simple_crawler()
    test3_passed = test_with_render_js_true()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed and test3_passed:
        print("✅ All tests passed! ScrapingBee integration is working.")
    else:
        print("❌ Some tests failed. There may be configuration issues.")
    
    return test1_passed and test2_passed and test3_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 