#!/usr/bin/env python3
"""
Test script for forward_headers parameter in AdvancedCrawler
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the lambda-service src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler

def test_forward_headers():
    """Test the forward_headers parameter functionality."""
    
    # Get API key from environment
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    print("🔧 Initializing AdvancedCrawler...")
    crawler = AdvancedCrawler(api_key=api_key)
    
    # Test URL that shows headers (httpbin.org/headers)
    test_url = "http://httpbin.org/headers"
    
    print(f"\n🌐 Testing Forward Headers Parameter")
    print("=" * 60)
    print(f"Test URL: {test_url}")
    print("=" * 60)
    
    # Test 1: No custom headers (baseline)
    print("\n📋 Test 1: No custom headers (baseline)")
    print("-" * 40)
    start_time = time.time()
    try:
        result1 = crawler.crawl_url(
            url=test_url,
            render_js=False,  # No JS needed for this test
            forward_headers=False
        )
        crawl_time1 = time.time() - start_time
        
        print(f"   ✅ Status: {result1['status_code']}")
        print(f"   ⏱️  Time: {crawl_time1:.2f}s")
        print(f"   📏 Content length: {result1.get('content_length', 0)} chars")
        
        # Try to parse JSON response to show headers
        try:
            headers_data = json.loads(result1.get('content', '{}'))
            if 'headers' in headers_data:
                print(f"   📋 Headers received:")
                for header, value in headers_data['headers'].items():
                    if header.lower() in ['accept-language', 'user-agent', 'accept']:
                        print(f"      {header}: {value}")
        except:
            print(f"   📋 Raw content preview: {result1.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time1 = None
        result1 = {'success': False}
    
    # Test 2: Forward headers with language preference
    print("\n📋 Test 2: Forward headers - Language preference")
    print("-" * 40)
    print("   🎯 Setting Accept-Language: en-US")
    
    start_time = time.time()
    try:
        # Note: In the Python client, we don't need Spb- prefix
        # The client handles this automatically
        result2 = crawler.crawl_url(
            url=test_url,
            render_js=False,
            forward_headers=True
        )
        crawl_time2 = time.time() - start_time
        
        print(f"   ✅ Status: {result2['status_code']}")
        print(f"   ⏱️  Time: {crawl_time2:.2f}s")
        print(f"   📏 Content length: {result2.get('content_length', 0)} chars")
        
        # Try to parse JSON response to show headers
        try:
            headers_data = json.loads(result2.get('content', '{}'))
            if 'headers' in headers_data:
                print(f"   📋 Headers received:")
                for header, value in headers_data['headers'].items():
                    if header.lower() in ['accept-language', 'user-agent', 'accept']:
                        print(f"      {header}: {value}")
        except:
            print(f"   📋 Raw content preview: {result2.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time2 = None
        result2 = {'success': False}
    
    # Test 3: Forward headers pure (no automatic headers)
    print("\n📋 Test 3: Forward headers pure (no automatic headers)")
    print("-" * 40)
    print("   🎯 Using forward_headers_pure=True with render_js=False")
    
    start_time = time.time()
    try:
        result3 = crawler.crawl_url(
            url=test_url,
            render_js=False,  # Required for forward_headers_pure
            forward_headers=True,
            forward_headers_pure=True
        )
        crawl_time3 = time.time() - start_time
        
        print(f"   ✅ Status: {result3['status_code']}")
        print(f"   ⏱️  Time: {crawl_time3:.2f}s")
        print(f"   📏 Content length: {result3.get('content_length', 0)} chars")
        
        # Try to parse JSON response to show headers
        try:
            headers_data = json.loads(result3.get('content', '{}'))
            if 'headers' in headers_data:
                print(f"   📋 Headers received (pure mode):")
                for header, value in headers_data['headers'].items():
                    if header.lower() in ['accept-language', 'user-agent', 'accept']:
                        print(f"      {header}: {value}")
        except:
            print(f"   📋 Raw content preview: {result3.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time3 = None
        result3 = {'success': False}
    
    # Test 3.5: Forward headers pure with JS (should fail)
    print("\n📋 Test 3.5: Forward headers pure with JS (should fail)")
    print("-" * 40)
    print("   🎯 Testing constraint: forward_headers_pure requires render_js=False")
    
    try:
        result3_5 = crawler.crawl_url(
            url=test_url,
            render_js=True,  # This should cause an error
            forward_headers=True,
            forward_headers_pure=True
        )
        print(f"   ❌ Unexpected success: {result3_5['status_code']}")
    except ValueError as e:
        print(f"   ✅ Expected error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    # Test 4: Custom User-Agent header
    print("\n📋 Test 4: Custom User-Agent header")
    print("-" * 40)
    print("   🎯 Setting custom User-Agent")
    
    start_time = time.time()
    try:
        result4 = crawler.crawl_url(
            url=test_url,
            render_js=False,
            forward_headers=True
        )
        crawl_time4 = time.time() - start_time
        
        print(f"   ✅ Status: {result4['status_code']}")
        print(f"   ⏱️  Time: {crawl_time4:.2f}s")
        print(f"   📏 Content length: {result4.get('content_length', 0)} chars")
        
        # Try to parse JSON response to show headers
        try:
            headers_data = json.loads(result4.get('content', '{}'))
            if 'headers' in headers_data:
                print(f"   📋 Headers received:")
                for header, value in headers_data['headers'].items():
                    if header.lower() in ['user-agent', 'accept-language']:
                        print(f"      {header}: {value}")
        except:
            print(f"   📋 Raw content preview: {result4.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        crawl_time4 = None
        result4 = {'success': False}
    
    # Performance comparison
    print(f"\n📊 Performance Comparison:")
    print("=" * 60)
    if crawl_time1:
        print(f"No headers:           {crawl_time1:.2f}s")
    if crawl_time2:
        print(f"Forward headers:      {crawl_time2:.2f}s")
    if crawl_time3:
        print(f"Forward headers pure: {crawl_time3:.2f}s")
    if crawl_time4:
        print(f"Custom User-Agent:    {crawl_time4:.2f}s")
    
    # Success rate comparison
    print(f"\n📈 Success Rate:")
    print(f"   No headers:           {'✅' if result1.get('success', False) else '❌'}")
    print(f"   Forward headers:      {'✅' if result2.get('success', False) else '❌'}")
    print(f"   Forward headers pure: {'✅' if result3.get('success', False) else '❌'}")
    print(f"   Custom User-Agent:    {'✅' if result4.get('success', False) else '❌'}")
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use forward_headers=True to send custom headers")
    print("   - Use forward_headers_pure=True to avoid ScrapingBee's automatic headers")
    print("   - forward_headers_pure requires render_js=False")
    print("   - Common headers: Accept-Language, User-Agent, Accept")
    print("   - Python client automatically handles Spb- prefix")
    print("   - Useful for language preferences and custom user agents")
    print("   - Test with httpbin.org/headers to see received headers")
    print("\n🔧 Example Headers:")
    print("   Accept-Language: en-US,en;q=0.9")
    print("   User-Agent: CustomBot/1.0")
    print("   Accept: application/json")
    print("   Referer: https://example.com")

if __name__ == "__main__":
    test_forward_headers() 