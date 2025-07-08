#!/usr/bin/env python3
"""
Test script to find and test the direct API Gateway URL.
Since the custom domain isn't working, we'll try to find the direct API Gateway endpoint.
"""

import requests
import json
import sys
import subprocess

def find_api_gateway_url():
    """Try to find the API Gateway URL using AWS CLI."""
    try:
        print("🔍 Searching for API Gateway URLs...")
        
        # Try to list API Gateways
        result = subprocess.run([
            'aws', 'apigateway', 'get-rest-apis',
            '--region', 'ap-south-1'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            apis = data.get('items', [])
            
            for api in apis:
                if 'crawlchat' in api.get('name', '').lower():
                    api_id = api['id']
                    api_name = api['name']
                    print(f"   Found API: {api_name} (ID: {api_id})")
                    
                    # Try different stage names
                    stages = ['prod', 'dev', 'test', 'stage']
                    for stage in stages:
                        url = f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/{stage}"
                        print(f"   Trying: {url}")
                        
                        try:
                            response = requests.get(f"{url}/health", timeout=5)
                            if response.status_code != 404:
                                print(f"   ✅ Found working endpoint: {url}")
                                return url
                        except:
                            continue
        else:
            print(f"   ❌ AWS CLI error: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return None

def test_api_gateway_url(base_url):
    """Test the API Gateway URL with crawler requests."""
    if not base_url:
        return False
    
    # Test health endpoint
    try:
        print(f"\n🏥 Testing API Gateway Health")
        print(f"   URL: {base_url}/health")
        
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400 and "URL is required" in response.text:
            print(f"   ✅ API Gateway is working (expects crawler requests)")
            return True
        else:
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    return False

def test_crawler_request(base_url):
    """Test a crawler request to the API Gateway."""
    if not base_url:
        return False
    
    data = {
        "url": "https://httpbin.org/html",
        "content_type": "generic",
        "take_screenshot": False,
        "download_file": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n🕷️ Testing Crawler Request")
        print(f"   URL: {base_url}")
        print(f"   Target: {data['url']}")
        
        response = requests.post(base_url, json=data, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Crawl successful!")
            print(f"   Success: {result.get('success', False)}")
            return True
        else:
            print(f"   ❌ Crawl failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function."""
    print("🚀 CrawlChat API Gateway Discovery")
    print("=" * 40)
    
    # Find API Gateway URL
    api_url = find_api_gateway_url()
    
    if not api_url:
        print("\n❌ Could not find API Gateway URL.")
        print("\n💡 Manual steps:")
        print("   1. Go to AWS Console → API Gateway")
        print("   2. Find your CrawlChat API")
        print("   3. Note the Invoke URL (format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage})")
        print("   4. Use that URL for testing")
        return
    
    # Test the API Gateway
    if test_api_gateway_url(api_url):
        if test_crawler_request(api_url):
            print(f"\n✅ API Gateway is working correctly!")
            print(f"\n💡 Use this URL for API calls: {api_url}")
            print(f"   Example: curl -X POST {api_url} -H 'Content-Type: application/json' -d '{{\"url\": \"https://example.com\"}}'")
        else:
            print(f"\n❌ Crawler request failed.")
    else:
        print(f"\n❌ API Gateway health check failed.")

if __name__ == "__main__":
    main() 