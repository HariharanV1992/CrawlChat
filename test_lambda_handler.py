#!/usr/bin/env python3
"""
Test script for Lambda handler
"""

import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_lambda_handler():
    """Test the Lambda handler locally."""
    try:
        # Set Lambda environment variable
        os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-function'
        
        # Import the handler
        from lambda_handler import handler
        print("✅ Successfully imported Lambda handler")
        
        # Create a test event
        test_event = {
            "version": "2.0",
            "routeKey": "GET /health",
            "rawPath": "/health",
            "rawQueryString": "",
            "headers": {
                "accept": "*/*",
                "content-length": "0",
                "host": "lambda-url.ap-south-1.on.aws",
                "user-agent": "curl/7.68.0"
            },
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "api-id",
                "domainName": "lambda-url.ap-south-1.on.aws",
                "domainPrefix": "lambda-url",
                "http": {
                    "method": "GET",
                    "path": "/health",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "curl/7.68.0"
                },
                "requestId": "id",
                "routeKey": "GET /health",
                "stage": "$default",
                "time": "12/Mar/2020:19:03:58 +0000",
                "timeEpoch": 1583348638390
            },
            "body": "",
            "isBase64Encoded": False
        }
        
        # Test the handler
        print("Testing handler with health check endpoint...")
        response = handler(test_event, {})
        
        print(f"✅ Handler executed successfully")
        print(f"Status Code: {response.get('statusCode', 'N/A')}")
        print(f"Response: {json.dumps(response, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda handler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lambda_handler()
    sys.exit(0 if success else 1) 