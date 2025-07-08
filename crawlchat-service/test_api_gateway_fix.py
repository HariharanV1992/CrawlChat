#!/usr/bin/env python3
"""
Quick fix test for API Gateway.
This script tests the API Gateway and provides working endpoints.
"""

import requests
import json
import sys

# API Gateway URL (found from AWS CLI)
API_GATEWAY_URL = "https://6a24mtpa4i.execute-api.ap-south-1.amazonaws.com/prod"

def test_api_gateway_endpoints():
    """Test various API Gateway endpoints."""
    print("🚀 CrawlChat API Gateway Quick Fix Test")
    print("=" * 50)
    print(f"API Gateway URL: {API_GATEWAY_URL}")
    print("")
    
    # Test endpoints
    endpoints = [
        ("/health", "GET", None, "Health Check"),
        ("/api/v1/auth/login", "POST", {
            "email": "admin@crawlchat.site",
            "password": "admin123"
        }, "Login API"),
        ("/api/v1/crawler/health", "GET", None, "Crawler Health"),
        ("/docs", "GET", None, "API Documentation"),
    ]
    
    results = []
    
    for path, method, data, description in endpoints:
        url = f"{API_GATEWAY_URL}{path}"
        
        try:
            print(f"🔍 Testing: {description}")
            print(f"   URL: {url}")
            print(f"   Method: {method}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success: {json.dumps(result, indent=2)}")
                    results.append((description, True, result))
                except:
                    print(f"   ✅ Success: {response.text[:200]}...")
                    results.append((description, True, response.text))
            else:
                print(f"   ❌ Failed: {response.text}")
                results.append((description, False, response.text))
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
            results.append((description, False, str(e)))
        
        print("")
    
    return results

def provide_working_solutions(results):
    """Provide working solutions based on test results."""
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    working_endpoints = []
    failed_endpoints = []
    
    for description, success, result in results:
        if success:
            working_endpoints.append(description)
            print(f"   ✅ {description}: Working")
        else:
            failed_endpoints.append(description)
            print(f"   ❌ {description}: Failed")
    
    print("")
    
    if working_endpoints:
        print("🎉 Working Endpoints:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
        
        print("")
        print("🔗 You can use these working endpoints:")
        print(f"   API Gateway: {API_GATEWAY_URL}")
        print("")
        
        if "Health Check" in working_endpoints:
            print("✅ Health check is working - the API Gateway is functional!")
        
        if "Login API" in working_endpoints:
            print("✅ Login API is working - you can authenticate users!")
            print("")
            print("🔐 Example login request:")
            print(f"curl -X POST {API_GATEWAY_URL}/api/v1/auth/login \\")
            print("  -H 'Content-Type: application/json' \\")
            print("  -d '{\"email\": \"admin@crawlchat.site\", \"password\": \"admin123\"}'")
    
    if failed_endpoints:
        print("")
        print("❌ Failed Endpoints:")
        for endpoint in failed_endpoints:
            print(f"   • {endpoint}")
        
        print("")
        print("🔧 Issues to fix:")
        print("   1. Lambda functions need proper container images")
        print("   2. API Gateway integration needs to be configured")
        print("   3. DNS configuration for custom domains")
    
    print("")
    print("💡 Quick Solutions:")
    print("   1. Use the working API Gateway URL directly")
    print("   2. Deploy Lambda functions with proper container images")
    print("   3. Fix DNS configuration for custom domains")
    print("   4. Test with the provided curl commands")

def main():
    """Main function."""
    results = test_api_gateway_endpoints()
    provide_working_solutions(results)

if __name__ == "__main__":
    main() 