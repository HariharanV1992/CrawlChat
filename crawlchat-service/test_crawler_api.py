#!/usr/bin/env python3
"""
Test script for crawler API functionality.
This tests the crawler Lambda function directly.
"""

import requests
import json
import sys

def test_crawler_api(url_to_crawl="https://example.com"):
    """Test the crawler API with a simple request."""
    api_url = "https://api.crawlchat.site"
    
    data = {
        "url": url_to_crawl,
        "content_type": "generic",
        "take_screenshot": False,
        "download_file": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🕷️ Testing Crawler API")
        print(f"   URL: {api_url}")
        print(f"   Target: {url_to_crawl}")
        
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Crawl successful!")
            print(f"   Success: {result.get('success', False)}")
            print(f"   URL: {result.get('url', 'N/A')}")
            
            # Show usage stats
            if 'usage_stats' in result:
                stats = result['usage_stats']
                print(f"   📊 Usage Stats:")
                print(f"      Total Requests: {stats.get('total_requests', 0)}")
                print(f"      Successful: {stats.get('successful_requests', 0)}")
                print(f"      Failed: {stats.get('failed_requests', 0)}")
                
                if 'cost_estimate' in stats:
                    cost = stats['cost_estimate']
                    print(f"      Total Cost: ${cost.get('total_cost', 0):.4f}")
                    print(f"      Credits Used: {cost.get('credits_used', 0)}")
            
            return result
        else:
            print(f"   ❌ Crawl failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return None

def test_crawler_health():
    """Test if the crawler endpoint is accessible."""
    api_url = "https://api.crawlchat.site"
    
    try:
        print(f"\n🏥 Testing Crawler Endpoint Accessibility")
        print(f"   URL: {api_url}")
        
        # Try a simple GET request
        response = requests.get(api_url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400 and "URL is required" in response.text:
            print(f"   ✅ Crawler endpoint is accessible (expects POST with URL)")
            return True
        else:
            print(f"   ❌ Unexpected response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function."""
    print("🚀 CrawlChat Crawler API Test")
    print("=" * 40)
    
    # Test endpoint accessibility
    if not test_crawler_health():
        print("\n❌ Crawler endpoint is not accessible.")
        return
    
    # Test with a simple URL
    print("\n📋 Testing crawler functionality:")
    result = test_crawler_api("https://httpbin.org/html")
    
    if result:
        print("\n✅ Crawler API is working correctly!")
        print("\n💡 The issue is that ALL requests to api.crawlchat.site are being routed to the crawler Lambda.")
        print("   This is a DNS/API Gateway configuration issue.")
        print("\n🔧 Solutions:")
        print("   1. Fix API Gateway routing to separate different endpoints")
        print("   2. Use different domains for different services")
        print("   3. Deploy the main application separately")
    else:
        print("\n❌ Crawler API test failed.")
        print("\n💡 Check your ScrapingBee API key and deployment configuration.")

if __name__ == "__main__":
    main() 