#!/usr/bin/env python3
"""
Test script to check all API endpoints and identify issues.
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any

# Configuration
BASE_URL = "https://txhpnybb5pp52vkn3o64arj5ne0aqyay.lambda-url.ap-south-1.on.aws"  # Actual Lambda function URL
API_BASE = f"{BASE_URL}/api/v1"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """Test a single endpoint."""
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:500] if response.text else None,
                "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def test_auth_endpoints(self):
        """Test authentication endpoints."""
        self.log("🔐 Testing Authentication Endpoints")
        self.log("=" * 50)
        
        # Test login
        self.log("Testing user login...")
        login_data = {
            "email": "harito2do@gmail.com",
            "password": "password123"
        }
        
        login_result = self.test_endpoint("POST", "/auth/login", login_data)
        self.log(f"Login: {login_result.get('status_code', 'ERROR')}")
        
        if login_result.get('status_code') == 200:
            self.log("✅ Login successful")
            # Extract token for other tests
            if login_result.get('json') and 'access_token' in login_result['json']:
                self.auth_token = login_result['json']['access_token']
                self.log(f"✅ Auth token obtained: {self.auth_token[:20]}...")
        else:
            self.log(f"❌ Login failed: {login_result}")
    
    def test_crawler_endpoints(self):
        """Test crawler endpoints."""
        self.log("🕷️ Testing Crawler Endpoints")
        self.log("=" * 50)
        
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        
        # Test create crawl task
        self.log("Testing create crawl task...")
        crawl_data = {
            "url": "https://httpbin.org/html",
            "max_documents": 2,
            "max_pages": 3,
            "max_workers": 1,
            "delay": 1.0,
            "total_timeout": 60,
            "page_timeout": 30,
            "request_timeout": 10
        }
        
        create_result = self.test_endpoint("POST", "/crawler/tasks", crawl_data, headers)
        self.log(f"Create task: {create_result.get('status_code', 'ERROR')}")
        
        if create_result.get('status_code') == 200:
            self.log("✅ Task creation successful")
            task_id = create_result.get('json', {}).get('task_id')
            if task_id:
                self.log(f"✅ Task ID: {task_id}")
                
                # Test get task status
                self.log("Testing get task status...")
                status_result = self.test_endpoint("GET", f"/crawler/tasks/{task_id}", headers=headers)
                self.log(f"Get status: {status_result.get('status_code', 'ERROR')}")
                
                if status_result.get('status_code') == 200:
                    self.log("✅ Get status successful")
                    status_data = status_result.get('json', {})
                    self.log(f"✅ Task status: {status_data.get('status', 'unknown')}")
                else:
                    self.log(f"❌ Get status failed: {status_result}")
                
                # Test start task
                self.log("Testing start task...")
                start_result = self.test_endpoint("POST", f"/crawler/tasks/{task_id}/start", headers=headers)
                self.log(f"Start task: {start_result.get('status_code', 'ERROR')}")
                
                if start_result.get('status_code') == 200:
                    self.log("✅ Start task successful")
                else:
                    self.log(f"❌ Start task failed: {start_result}")
                
                # Wait a bit and check status again
                self.log("Waiting 5 seconds and checking status...")
                time.sleep(5)
                
                status_result2 = self.test_endpoint("GET", f"/crawler/tasks/{task_id}", headers=headers)
                if status_result2.get('status_code') == 200:
                    status_data2 = status_result2.get('json', {})
                    self.log(f"✅ Updated status: {status_data2.get('status', 'unknown')}")
                    self.log(f"✅ Pages crawled: {status_data2.get('pages_crawled', 0)}")
                    self.log(f"✅ Documents downloaded: {status_data2.get('documents_downloaded', 0)}")
                else:
                    self.log(f"❌ Status check failed: {status_result2}")
                
                # Test cancel task
                self.log("Testing cancel task...")
                cancel_result = self.test_endpoint("POST", f"/crawler/tasks/{task_id}/cancel", headers=headers)
                self.log(f"Cancel task: {cancel_result.get('status_code', 'ERROR')}")
                
                if cancel_result.get('status_code') == 200:
                    self.log("✅ Cancel task successful")
                else:
                    self.log(f"❌ Cancel task failed: {cancel_result}")
                
        else:
            self.log(f"❌ Task creation failed: {create_result}")
        
        # Test list tasks
        self.log("Testing list tasks...")
        list_result = self.test_endpoint("GET", "/crawler/tasks", headers=headers)
        self.log(f"List tasks: {list_result.get('status_code', 'ERROR')}")
        
        if list_result.get('status_code') == 200:
            self.log("✅ List tasks successful")
            tasks = list_result.get('json', {}).get('tasks', [])
            self.log(f"✅ Found {len(tasks)} tasks")
        else:
            self.log(f"❌ List tasks failed: {list_result}")
    
    def test_document_endpoints(self):
        """Test document endpoints."""
        self.log("📄 Testing Document Endpoints")
        self.log("=" * 50)
        
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        
        # Test list documents
        self.log("Testing list documents...")
        list_result = self.test_endpoint("GET", "/documents", headers=headers)
        self.log(f"List documents: {list_result.get('status_code', 'ERROR')}")
        
        if list_result.get('status_code') == 200:
            self.log("✅ List documents successful")
            documents = list_result.get('json', {}).get('documents', [])
            self.log(f"✅ Found {len(documents)} documents")
        else:
            self.log(f"❌ List documents failed: {list_result}")
    
    def test_chat_endpoints(self):
        """Test chat endpoints."""
        self.log("💬 Testing Chat Endpoints")
        self.log("=" * 50)
        
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        
        # Test start chat session
        self.log("Testing start chat session...")
        chat_data = {
            "document_id": "test_doc_123"
        }
        
        start_result = self.test_endpoint("POST", "/chat/start", chat_data, headers)
        self.log(f"Start chat: {start_result.get('status_code', 'ERROR')}")
        
        if start_result.get('status_code') == 200:
            self.log("✅ Start chat successful")
            session_id = start_result.get('json', {}).get('session_id')
            if session_id:
                self.log(f"✅ Session ID: {session_id}")
                
                # Test send message
                self.log("Testing send message...")
                message_data = {
                    "session_id": session_id,
                    "message": "Hello, this is a test message"
                }
                
                message_result = self.test_endpoint("POST", "/chat/message", message_data, headers)
                self.log(f"Send message: {message_result.get('status_code', 'ERROR')}")
                
                if message_result.get('status_code') == 200:
                    self.log("✅ Send message successful")
                else:
                    self.log(f"❌ Send message failed: {message_result}")
        else:
            self.log(f"❌ Start chat failed: {start_result}")
    
    def test_health_endpoints(self):
        """Test health and status endpoints."""
        self.log("🏥 Testing Health Endpoints")
        self.log("=" * 50)
        
        # Test health check
        self.log("Testing health check...")
        health_result = self.test_endpoint("GET", "/health")
        self.log(f"Health check: {health_result.get('status_code', 'ERROR')}")
        
        if health_result.get('status_code') == 200:
            self.log("✅ Health check successful")
        else:
            self.log(f"❌ Health check failed: {health_result}")
        
        # Test root endpoint
        self.log("Testing root endpoint...")
        root_result = self.test_endpoint("GET", "/")
        self.log(f"Root endpoint: {root_result.get('status_code', 'ERROR')}")
        
        if root_result.get('status_code') == 200:
            self.log("✅ Root endpoint successful")
        else:
            self.log(f"❌ Root endpoint failed: {root_result}")
    
    def run_all_tests(self):
        """Run all API tests."""
        self.log("🚀 Starting API Endpoint Tests")
        self.log("=" * 60)
        
        try:
            self.test_health_endpoints()
            self.test_auth_endpoints()
            self.test_crawler_endpoints()
            self.test_document_endpoints()
            self.test_chat_endpoints()
            
            self.log("✅ All tests completed!")
            
        except Exception as e:
            self.log(f"❌ Test suite failed: {e}", "ERROR")

def main():
    """Main test function."""
    print("🔧 API Endpoint Tester")
    print("=" * 60)
    
    # Check if base URL is provided
    base_url = os.getenv("API_BASE_URL", BASE_URL)
    if base_url != BASE_URL:
        print(f"Using custom base URL: {base_url}")
    
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 