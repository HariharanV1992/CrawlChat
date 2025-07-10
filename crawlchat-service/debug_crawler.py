#!/usr/bin/env python3
"""
Debug script to see exactly what's happening with ScrapingBee requests
"""

import os
import requests
import json

def debug_scrapingbee_request():
    """Debug a ScrapingBee request to see what's happening."""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not set")
        return False
    
    print("🔍 Debugging ScrapingBee Request")
    print("=" * 50)
    
    # Test with the exact same parameters as our crawler
    url = "https://httpbin.org/ip"
    params = {
        "api_key": api_key,
        "url": url,
        "render_js": "false",
        "premium_proxy": "false",
        "stealth_proxy": "false",
        "block_resources": "true",
        "timeout": "30000",
        "wait": "0",
        "country_code": "in",
        "block_ads": "true",
        "wait_browser": "domcontentloaded",
        "device": "desktop"
    }
    
    print("📤 Request Parameters:")
    for key, value in params.items():
        if key == "api_key":
            print(f"  {key}: {value[:10]}...{value[-10:]}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n📡 Making request to: https://app.scrapingbee.com/api/v1/")
    print(f"🎯 Target URL: {url}")
    
    try:
        response = requests.get("https://app.scrapingbee.com/api/v1/", params=params, timeout=60)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n📥 Response Body (first 500 chars):")
        print(response.text[:500])
        
        if response.status_code == 200:
            print("\n✅ Request successful!")
            return True
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        return False

def debug_with_different_params():
    """Test with different parameter combinations."""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not set")
        return False
    
    print("\n🔍 Testing Different Parameter Combinations")
    print("=" * 50)
    
    # Test 1: Minimal parameters
    print("\n🧪 Test 1: Minimal parameters")
    params1 = {
        "api_key": api_key,
        "url": "https://httpbin.org/ip",
        "render_js": "false"
    }
    
    try:
        response1 = requests.get("https://app.scrapingbee.com/api/v1/", params=params1, timeout=30)
        print(f"Status: {response1.status_code}")
        print(f"Success: {response1.status_code == 200}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With premium proxy
    print("\n🧪 Test 2: With premium proxy")
    params2 = {
        "api_key": api_key,
        "url": "https://httpbin.org/ip",
        "render_js": "false",
        "premium_proxy": "true"
    }
    
    try:
        response2 = requests.get("https://app.scrapingbee.com/api/v1/", params=params2, timeout=30)
        print(f"Status: {response2.status_code}")
        print(f"Success: {response2.status_code == 200}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: With stealth proxy
    print("\n🧪 Test 3: With stealth proxy")
    params3 = {
        "api_key": api_key,
        "url": "https://httpbin.org/ip",
        "render_js": "false",
        "stealth_proxy": "true"
    }
    
    try:
        response3 = requests.get("https://app.scrapingbee.com/api/v1/", params=params3, timeout=30)
        print(f"Status: {response3.status_code}")
        print(f"Success: {response3.status_code == 200}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run debug tests."""
    print("🔍 ScrapingBee Debug Session")
    print("=" * 60)
    
    debug_scrapingbee_request()
    debug_with_different_params()

if __name__ == "__main__":
    main() 