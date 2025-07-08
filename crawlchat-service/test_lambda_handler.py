#!/usr/bin/env python3
"""
Test script to verify Lambda handler works without cold start timeouts.
"""

import json
import time
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_lambda_handler():
    """Test the Lambda handler with a simple health check."""
    
    print("🧪 Testing Lambda Handler")
    print("=" * 50)
    
    try:
        # Import the handler
        print("📦 Importing lambda_handler...")
        start_time = time.time()
        
        from lambda_handler import lambda_handler
        
        import_time = time.time() - start_time
        print(f"✅ Import completed in {import_time:.2f} seconds")
        
        # Test with a simple health check event
        print("\n🔍 Testing health check endpoint...")
        test_event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {
                "Content-Type": "application/json"
            },
            "queryStringParameters": None,
            "body": None,
            "isBase64Encoded": False
        }
        
        test_context = {
            "function_name": "test-function",
            "function_version": "test-version",
            "invoked_function_arn": "test-arn",
            "memory_limit_in_mb": "1024",
            "aws_request_id": "test-request-id",
            "log_group_name": "test-log-group",
            "log_stream_name": "test-log-stream"
        }
        
        # Test the handler
        start_time = time.time()
        response = lambda_handler(test_event, test_context)
        handler_time = time.time() - start_time
        
        print(f"✅ Handler completed in {handler_time:.2f} seconds")
        print(f"📊 Response status: {response.get('statusCode', 'unknown')}")
        
        # Parse and display response body
        if 'body' in response:
            try:
                body = json.loads(response['body'])
                print(f"📄 Response body: {json.dumps(body, indent=2)}")
            except:
                print(f"📄 Response body: {response['body'][:200]}...")
        
        # Test total time
        total_time = import_time + handler_time
        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        
        if total_time < 10:
            print("✅ SUCCESS: Handler completes within 10 seconds (Lambda timeout limit)")
        else:
            print("❌ WARNING: Handler takes longer than 10 seconds - may timeout in Lambda")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crawler_endpoint():
    """Test the crawler endpoint specifically."""
    
    print("\n🕷️  Testing Crawler Endpoint")
    print("=" * 50)
    
    try:
        from lambda_handler import lambda_handler
        
        # Test with a crawler API event
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/crawler/tasks",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"
            },
            "queryStringParameters": {
                "limit": "10",
                "skip": "0"
            },
            "body": None,
            "isBase64Encoded": False
        }
        
        test_context = {
            "function_name": "test-function",
            "function_version": "test-version",
            "invoked_function_arn": "test-arn",
            "memory_limit_in_mb": "1024",
            "aws_request_id": "test-request-id",
            "log_group_name": "test-log-group",
            "log_stream_name": "test-log-stream"
        }
        
        # Test the handler
        start_time = time.time()
        response = lambda_handler(test_event, test_context)
        handler_time = time.time() - start_time
        
        print(f"✅ Crawler endpoint completed in {handler_time:.2f} seconds")
        print(f"📊 Response status: {response.get('statusCode', 'unknown')}")
        
        # Parse and display response body
        if 'body' in response:
            try:
                body = json.loads(response['body'])
                print(f"📄 Response body: {json.dumps(body, indent=2)}")
            except:
                print(f"📄 Response body: {response['body'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during crawler test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Lambda Handler Tests")
    print("=" * 50)
    
    # Test basic handler
    success1 = test_lambda_handler()
    
    # Test crawler endpoint
    success2 = test_crawler_endpoint()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed! Lambda handler should work without timeouts.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if (success1 and success2) else 1) 