#!/usr/bin/env python3
"""
Local test script for Lambda function
"""

import json
import sys
import os

# Add the lambda-service directory to the path
sys.path.insert(0, 'crawlchat-service/lambda-service')

def test_lambda_handler():
    """Test the Lambda handler locally"""
    
    # Import the handler
    from lambda_handler import lambda_handler
    
    # Test 1: Empty payload (should go to crawler handler)
    print("=== Test 1: Empty payload ===")
    try:
        result = lambda_handler({}, {})
        print(f"Status Code: {result.get('statusCode')}")
        print(f"Body: {result.get('body')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: API Gateway payload (should go to FastAPI)
    print("=== Test 2: API Gateway payload ===")
    api_gateway_event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {},
        "queryStringParameters": None,
        "body": None,
        "isBase64Encoded": False
    }
    
    try:
        result = lambda_handler(api_gateway_event, {})
        print(f"Status Code: {result.get('statusCode')}")
        print(f"Body: {result.get('body')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Crawler payload
    print("=== Test 3: Crawler payload ===")
    crawler_event = {
        "url": "https://example.com"
    }
    
    try:
        result = lambda_handler(crawler_event, {})
        print(f"Status Code: {result.get('statusCode')}")
        print(f"Body: {result.get('body')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_lambda_handler() 