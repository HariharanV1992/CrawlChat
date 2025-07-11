#!/usr/bin/env python3
"""
Test script to verify the authentication flow
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://api.crawlchat.site"
LOGIN_DATA = {
    "email": "harito2do@gmail.com",
    "password": "password123"
}

def test_auth_flow():
    """Test the complete authentication flow"""
    print("🔐 Testing Authentication Flow")
    print("=" * 50)
    
    # Step 1: Test login
    print("\n1. Testing Login...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=LOGIN_DATA,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {login_response.status_code}")
        print(f"   Response Headers: {dict(login_response.headers)}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"   ✅ Login successful!")
            print(f"   Access Token: {login_data.get('access_token', 'N/A')[:20]}...")
            print(f"   User ID: {login_data.get('user', {}).get('user_id', 'N/A')}")
            
            access_token = login_data.get('access_token')
            user_id = login_data.get('user', {}).get('user_id')
            
            if not access_token or not user_id:
                print("   ❌ Missing access_token or user_id in response")
                return False
                
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 2: Test token verification
    print("\n2. Testing Token Verification...")
    try:
        verify_response = requests.get(
            f"{BASE_URL}/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"   Status Code: {verify_response.status_code}")
        print(f"   Response Headers: {dict(verify_response.headers)}")
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print(f"   ✅ Token verification successful!")
            print(f"   Valid: {verify_data.get('valid', 'N/A')}")
            print(f"   User: {verify_data.get('user', 'N/A')}")
            
            if not verify_data.get('valid'):
                print("   ❌ Token marked as invalid")
                return False
                
        else:
            print(f"   ❌ Token verification failed: {verify_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Token verification error: {e}")
        return False
    
    # Step 3: Test /me endpoint
    print("\n3. Testing /me endpoint...")
    try:
        me_response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"   Status Code: {me_response.status_code}")
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"   ✅ /me endpoint successful!")
            print(f"   User: {me_data}")
            
        else:
            print(f"   ❌ /me endpoint failed: {me_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ /me endpoint error: {e}")
        return False
    
    # Step 4: Test chat page access
    print("\n4. Testing Chat Page Access...")
    try:
        chat_response = requests.get(
            f"{BASE_URL}/chat",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"   Status Code: {chat_response.status_code}")
        print(f"   Content Type: {chat_response.headers.get('content-type', 'N/A')}")
        
        if chat_response.status_code == 200:
            print(f"   ✅ Chat page accessible!")
            if "text/html" in chat_response.headers.get('content-type', ''):
                print(f"   ✅ HTML content received")
            else:
                print(f"   ⚠️  Unexpected content type")
                
        else:
            print(f"   ❌ Chat page access failed: {chat_response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Chat page access error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Authentication flow test completed successfully!")
    return True

def test_browser_simulation():
    """Simulate browser behavior"""
    print("\n🌐 Testing Browser Simulation")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Get login page
    print("\n1. Getting login page...")
    try:
        login_page = session.get(f"{BASE_URL}/login")
        print(f"   Status Code: {login_page.status_code}")
        print(f"   Content Type: {login_page.headers.get('content-type', 'N/A')}")
        
        if login_page.status_code == 200:
            print(f"   ✅ Login page accessible")
        else:
            print(f"   ❌ Login page failed: {login_page.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Login page error: {e}")
        return False
    
    # Step 2: Login
    print("\n2. Logging in...")
    try:
        login_response = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=LOGIN_DATA,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {login_response.status_code}")
        print(f"   Cookies: {dict(session.cookies)}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"   ✅ Login successful!")
            print(f"   Access Token: {login_data.get('access_token', 'N/A')[:20]}...")
            
            # Store token in session headers for subsequent requests
            session.headers.update({"Authorization": f"Bearer {login_data.get('access_token')}"})
            
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 3: Access chat page with session
    print("\n3. Accessing chat page with session...")
    try:
        chat_response = session.get(f"{BASE_URL}/chat")
        
        print(f"   Status Code: {chat_response.status_code}")
        print(f"   Content Type: {chat_response.headers.get('content-type', 'N/A')}")
        print(f"   Content Length: {len(chat_response.content)}")
        
        if chat_response.status_code == 200:
            print(f"   ✅ Chat page accessible with session!")
            if "text/html" in chat_response.headers.get('content-type', ''):
                print(f"   ✅ HTML content received")
                # Check if it's the login page (redirected)
                if "login" in chat_response.text.lower() or "sign in" in chat_response.text.lower():
                    print(f"   ⚠️  Redirected to login page")
                    return False
                else:
                    print(f"   ✅ Chat page content received")
            else:
                print(f"   ⚠️  Unexpected content type")
                
        else:
            print(f"   ❌ Chat page access failed: {chat_response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Chat page access error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Browser simulation test completed successfully!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Authentication Flow Tests")
    print("=" * 60)
    
    # Test 1: Direct API flow
    success1 = test_auth_flow()
    
    # Test 2: Browser simulation
    success2 = test_browser_simulation()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Direct API Flow: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Browser Simulation: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Authentication flow is working correctly.")
    else:
        print("\n🔧 Some tests failed. Check the output above for details.") 