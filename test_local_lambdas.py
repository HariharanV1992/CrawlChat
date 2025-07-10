#!/usr/bin/env python3
"""
Test script for local Lambda functions
"""

import requests
import json
import time
import sys

# Configuration
LAMBDA_API_URL = "http://localhost:9000"
CRAWLER_URL = "http://localhost:9001"

def test_health_endpoints():
    """Test health endpoints for both functions."""
    print("🧪 Testing health endpoints...")
    
    # Test Lambda API health
    try:
        response = requests.get(f"{LAMBDA_API_URL}/health", timeout=10)
        print(f"✅ Lambda API Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Lambda API Health failed: {e}")
    
    # Test Crawler health
    try:
        response = requests.get(f"{CRAWLER_URL}/health", timeout=10)
        print(f"✅ Crawler Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Crawler Health failed: {e}")

def test_crawler_endpoints():
    """Test crawler endpoints."""
    print("\n🧪 Testing crawler endpoints...")
    
    # Test crawler health via Lambda API
    try:
        response = requests.get(f"{LAMBDA_API_URL}/api/v1/crawler/health", timeout=10)
        print(f"✅ Crawler Health (via API): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Crawler Health (via API) failed: {e}")
    
    # Test task creation
    try:
        task_data = {
            "url": "https://example.com",
            "max_doc_count": 1
        }
        response = requests.post(f"{CRAWLER_URL}/tasks", json=task_data, timeout=10)
        print(f"✅ Task Creation: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            if task_id:
                print(f"📋 Task ID: {task_id}")
                
                # Test task status
                time.sleep(2)
                response = requests.get(f"{CRAWLER_URL}/tasks/{task_id}", timeout=10)
                print(f"✅ Task Status: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ Task creation failed: {e}")

def test_lambda_api_endpoints():
    """Test Lambda API endpoints."""
    print("\n🧪 Testing Lambda API endpoints...")
    
    # Test auth endpoints
    try:
        response = requests.get(f"{LAMBDA_API_URL}/api/v1/auth/verify", timeout=10)
        print(f"✅ Auth Verify: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Auth Verify failed: {e}")
    
    # Test chat endpoints
    try:
        response = requests.get(f"{LAMBDA_API_URL}/api/v1/chat/sessions", timeout=10)
        print(f"✅ Chat Sessions: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Chat Sessions failed: {e}")

def test_direct_lambda_invocation():
    """Test direct Lambda invocation format."""
    print("\n🧪 Testing direct Lambda invocation...")
    
    # Test Lambda API with direct invocation
    try:
        payload = {
            "httpMethod": "GET",
            "path": "/health"
        }
        response = requests.post(f"{LAMBDA_API_URL}/", json=payload, timeout=10)
        print(f"✅ Direct Lambda API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Direct Lambda API failed: {e}")
    
    # Test Crawler with direct invocation
    try:
        payload = {
            "url": "https://example.com",
            "max_doc_count": 1
        }
        response = requests.post(f"{CRAWLER_URL}/", json=payload, timeout=10)
        print(f"✅ Direct Crawler: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Direct Crawler failed: {e}")

def main():
    """Main test function."""
    print("🚀 Testing Local Lambda Functions")
    print("=" * 40)
    
    # Wait a moment for containers to be fully ready
    print("⏳ Waiting for containers to be ready...")
    time.sleep(5)
    
    # Run tests
    test_health_endpoints()
    test_crawler_endpoints()
    test_lambda_api_endpoints()
    test_direct_lambda_invocation()
    
    print("\n🎉 Testing completed!")
    print("\n📋 Service URLs:")
    print(f"  Lambda API: {LAMBDA_API_URL}")
    print(f"  Crawler: {CRAWLER_URL}")

if __name__ == "__main__":
    main() 