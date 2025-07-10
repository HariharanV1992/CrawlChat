#!/usr/bin/env python3
"""
Test script for both local and Lambda deployments
"""

import requests
import json
import time
import sys
import os

# Configuration
LAMBDA_API_URL = "https://urzb15oej0.execute-api.ap-south-1.amazonaws.com/prod"
LOCAL_API_URL = "http://localhost:8000"

def test_endpoint(base_url, endpoint, method="GET", data=None, description=""):
    """Test a single endpoint."""
    url = f"{base_url}{endpoint}"
    print(f"\n🧪 Testing {description}: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            headers = {"Content-Type": "application/json"} if data else {}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Success")
            return True
        else:
            print("❌ Failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_local_deployment():
    """Test local deployment."""
    print("\n" + "="*50)
    print("🏠 LOCAL DEPLOYMENT TESTING")
    print("="*50)
    
    # Test basic endpoints
    test_endpoint(LOCAL_API_URL, "/health", description="Health Check")
    test_endpoint(LOCAL_API_URL, "/api/v1/crawler/health", description="Crawler Health")
    
    # Test crawler task creation
    task_data = {
        "url": "https://example.com",
        "max_doc_count": 1
    }
    test_endpoint(LOCAL_API_URL, "/api/v1/crawler/tasks", method="POST", data=task_data, description="Create Crawl Task")
    
    # Test documents endpoint
    test_endpoint(LOCAL_API_URL, "/api/v1/documents/", description="Get Documents")

def test_lambda_deployment():
    """Test Lambda deployment."""
    print("\n" + "="*50)
    print("☁️ LAMBDA DEPLOYMENT TESTING")
    print("="*50)
    
    # Test basic endpoints
    test_endpoint(LAMBDA_API_URL, "/health", description="Health Check")
    test_endpoint(LAMBDA_API_URL, "/api/v1/crawler/health", description="Crawler Health")
    
    # Test crawler task creation
    task_data = {
        "url": "https://example.com",
        "max_doc_count": 1
    }
    test_endpoint(LAMBDA_API_URL, "/api/v1/crawler/tasks", method="POST", data=task_data, description="Create Crawl Task")
    
    # Test documents endpoint
    test_endpoint(LAMBDA_API_URL, "/api/v1/documents/", description="Get Documents")

def main():
    """Main test function."""
    print("🚀 CrawlChat Deployment Testing")
    print("="*50)
    
    # Check if local server is running
    try:
        response = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Local server is running")
            test_local_deployment()
        else:
            print("❌ Local server is not responding properly")
    except:
        print("❌ Local server is not running")
    
    # Always test Lambda
    test_lambda_deployment()
    
    print("\n" + "="*50)
    print("📋 TESTING COMPLETE")
    print("="*50)
    print("\nTo start local server:")
    print("cd crawlchat-service && python3 test_crawler_server.py")
    print("\nTo test Lambda directly:")
    print("aws lambda invoke --function-name crawlchat-crawler-function --payload '{\"url\": \"https://example.com\", \"max_doc_count\": 1}' --region ap-south-1 response.json")

if __name__ == "__main__":
    main() 