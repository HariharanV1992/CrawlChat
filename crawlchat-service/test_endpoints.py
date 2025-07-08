#!/usr/bin/env python3
"""
Test script to verify correct endpoint configuration and diagnose routing issues.
"""

import requests
import json
import sys

def test_endpoint(url, description):
    """Test an endpoint and return the result."""
    try:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            content = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"   Content Preview: {content}")
        else:
            print(f"   Error: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_endpoint(url, description):
    """Test an API endpoint with proper headers."""
    try:
        print(f"\n🔍 Testing API: {description}")
        print(f"   URL: {url}")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Error: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 CrawlChat Endpoint Test Suite")
    print("=" * 50)
    
    # Test main domain endpoints
    print("\n📋 Testing Main Domain (crawlchat.site):")
    main_domain_tests = [
        ("https://crawlchat.site/", "Root endpoint"),
        ("https://crawlchat.site/login", "Login page"),
        ("https://crawlchat.site/register", "Register page"),
        ("https://crawlchat.site/chat", "Chat interface"),
        ("https://crawlchat.site/crawler", "Crawler interface"),
        ("https://crawlchat.site/health", "Health check"),
    ]
    
    main_success = 0
    for url, desc in main_domain_tests:
        if test_endpoint(url, desc):
            main_success += 1
    
    # Test API domain endpoints
    print("\n📋 Testing API Domain (api.crawlchat.site):")
    api_domain_tests = [
        ("https://api.crawlchat.site/health", "API Health check"),
        ("https://api.crawlchat.site/api/v1/auth/login", "Auth API endpoint"),
        ("https://api.crawlchat.site/docs", "API Documentation"),
    ]
    
    api_success = 0
    for url, desc in api_domain_tests:
        if test_api_endpoint(url, desc):
            api_success += 1
    
    # Test crawler API specifically
    print("\n📋 Testing Crawler API:")
    crawler_tests = [
        ("https://api.crawlchat.site/api/v1/crawler/health", "Crawler health"),
    ]
    
    crawler_success = 0
    for url, desc in crawler_tests:
        if test_api_endpoint(url, desc):
            crawler_success += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Main Domain: {main_success}/{len(main_domain_tests)} passed")
    print(f"   API Domain: {api_success}/{len(api_domain_tests)} passed")
    print(f"   Crawler API: {crawler_success}/{len(crawler_tests)} passed")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if main_success == 0:
        print("   ❌ Main domain is not accessible - check DNS configuration")
        print("   💡 Expected: https://crawlchat.site should serve the main application")
    
    if api_success == 0:
        print("   ❌ API domain is not accessible - check DNS configuration")
        print("   💡 Expected: https://api.crawlchat.site should serve the API")
    
    if main_success > 0 and api_success > 0:
        print("   ✅ Both domains are working correctly")
        print("   💡 Use https://crawlchat.site/login for the login page")
        print("   💡 Use https://api.crawlchat.site for API calls")
    
    print("\n🔧 Quick Fix:")
    print("   If you're getting 'URL is required' error, you're hitting the crawler API.")
    print("   Try: https://crawlchat.site/login instead of https://api.crawlchat.site/login")

if __name__ == "__main__":
    main() 