#!/usr/bin/env python3
"""
Test script for own_proxy parameter in AdvancedCrawler
"""

import os
import sys
import time
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_own_proxy():
    """Test the own_proxy parameter functionality."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URL
    test_url = "https://example.com"
    
    # Example proxy configurations (these are examples - replace with real proxies)
    proxy_examples = [
        {
            "name": "HTTP Proxy with Auth",
            "proxy": "http://username:password@proxy.example.com:8080",
            "description": "HTTP proxy with authentication"
        },
        {
            "name": "HTTPS Proxy with Auth",
            "proxy": "https://user:pass@secure-proxy.com:3128",
            "description": "HTTPS proxy with authentication"
        },
        {
            "name": "SOCKS5 Proxy",
            "proxy": "socks5://proxyuser:proxypass@socks.example.com:1080",
            "description": "SOCKS5 proxy with authentication"
        },
        {
            "name": "Simple HTTP Proxy",
            "proxy": "http://proxy.example.com:8080",
            "description": "HTTP proxy without authentication"
        },
        {
            "name": "Default Port Proxy",
            "proxy": "http://user:pass@proxy.example.com",
            "description": "Uses default port 1080"
        }
    ]
    
    print(f"\n🌐 Testing Own Proxy Parameter")
    print("=" * 60)
    print("⚠️  NOTE: These are example proxy configurations")
    print("   Replace with your actual proxy servers for real testing")
    print("=" * 60)
    
    # Test 1: Standard ScrapingBee proxy (baseline)
    print("\n📋 Test 1: Standard ScrapingBee proxy (baseline)")
    print("-" * 40)
    start_time = time.time()
    try:
        result1 = crawler.crawl_url(
            url=test_url,
            render_js=True,
            own_proxy=None  # Use ScrapingBee's proxy
        )
        crawl_time1 = time.time() - start_time
        
        print(f"   ✅ Status: {result1['status_code']}")
        print(f"   ⏱️  Time: {crawl_time1:.2f}s")
        print(f"   📏 Content length: {result1.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~1 credit (with JS)")
        print(f"   🌐 Proxy: ScrapingBee default")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time1 = None
        result1 = {'success': False}
    
    # Test own proxy examples
    for i, proxy_config in enumerate(proxy_examples, 2):
        print(f"\n📋 Test {i}: {proxy_config['name']}")
        print("-" * 40)
        print(f"   📝 {proxy_config['description']}")
        print(f"   🔗 Proxy: {proxy_config['proxy']}")
        
        start_time = time.time()
        try:
            result = crawler.crawl_url(
                url=test_url,
                render_js=True,
                own_proxy=proxy_config['proxy']
            )
            crawl_time = time.time() - start_time
            
            print(f"   ✅ Status: {result['status_code']}")
            print(f"   ⏱️  Time: {crawl_time:.2f}s")
            print(f"   📏 Content length: {result.get('content_length', 0)} chars")
            print(f"   💰 Cost: ~1 credit (own proxy)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   💡 This is expected if the proxy server is not real")
        
        time.sleep(1)  # Brief delay between requests
    
    # Test own proxy with other features
    print(f"\n📋 Test: Own Proxy with JavaScript Features")
    print("-" * 40)
    test_proxy = "http://user:pass@proxy.example.com:8080"
    print(f"   🔗 Proxy: {test_proxy}")
    
    try:
        result = crawler.crawl_url(
            url=test_url,
            render_js=True,
            own_proxy=test_proxy,
            block_ads=True,
            block_resources=True,
            window_width=1920,
            window_height=1080,
            wait=2000
        )
        
        print(f"   ✅ Status: {result['status_code']}")
        print(f"   📏 Content length: {result.get('content_length', 0)} chars")
        print(f"   🎯 Features: JS rendering, ad blocking, viewport size, wait time")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   💡 This is expected if the proxy server is not real")
    
    # Test own proxy without JavaScript
    print(f"\n📋 Test: Own Proxy without JavaScript")
    print("-" * 40)
    try:
        result = crawler.crawl_url(
            url=test_url,
            render_js=False,
            own_proxy=test_proxy
        )
        
        print(f"   ✅ Status: {result['status_code']}")
        print(f"   📏 Content length: {result.get('content_length', 0)} chars")
        print(f"   💰 Cost: ~1 credit (own proxy, no JS)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   💡 This is expected if the proxy server is not real")
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use own_proxy to use your own proxy servers")
    print("   - Format: protocol://username:password@host:port")
    print("   - Supported protocols: http, https, socks5")
    print("   - Default port is 1080 if not specified")
    print("   - Works with all ScrapingBee features (JS, blocking, etc.)")
    print("   - Cost is same as standard proxy (~1 credit with JS)")
    print("   - Useful for using your own proxy pool or specific servers")
    print("\n🔧 Example Proxy Formats:")
    print("   HTTP:  http://user:pass@proxy.com:8080")
    print("   HTTPS: https://user:pass@secure-proxy.com:3128")
    print("   SOCKS5: socks5://user:pass@socks.com:1080")
    print("   Simple: http://proxy.com:8080")

if __name__ == "__main__":
    test_own_proxy() 