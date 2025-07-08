#!/usr/bin/env python3
"""
Test script for API login functionality.
Use this when the web interface is not accessible due to DNS issues.
"""

import requests
import json
import sys

def test_api_login(email, password):
    """Test API login functionality."""
    url = "https://api.crawlchat.site/api/v1/auth/login"
    
    data = {
        "email": email,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🔐 Testing API Login")
        print(f"   URL: {url}")
        print(f"   Email: {email}")
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token: {result.get('access_token', 'N/A')[:20]}...")
            print(f"   User: {result.get('user', {}).get('username', 'N/A')}")
            print(f"   Expires in: {result.get('expires_in', 'N/A')} seconds")
            return result
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return None

def test_api_health():
    """Test API health endpoint."""
    url = "https://api.crawlchat.site/health"
    
    try:
        print(f"\n🏥 Testing API Health")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ API is healthy")
            return True
        else:
            print(f"   ❌ API health check failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function."""
    print("🚀 CrawlChat API Login Test")
    print("=" * 40)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API is not accessible. Check your deployment.")
        return
    
    # Test with default credentials
    print("\n📋 Testing with default credentials:")
    
    # Try admin user
    admin_result = test_api_login("admin@crawlchat.site", "admin123")
    
    if admin_result:
        print("\n✅ Admin login successful!")
        print("   You can now use the API with the returned token.")
        print("\n💡 Next steps:")
        print("   1. Use the token in Authorization header: Bearer <token>")
        print("   2. Access API endpoints at https://api.crawlchat.site/api/v1/...")
        print("   3. Fix DNS to make web interface accessible")
    else:
        print("\n❌ Login failed. Check your credentials or deployment.")
        print("\n💡 Try creating a user first or check the deployment logs.")

if __name__ == "__main__":
    main() 