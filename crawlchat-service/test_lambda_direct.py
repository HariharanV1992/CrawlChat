#!/usr/bin/env python3
"""
Test script to invoke the Lambda function directly.
This will help us understand if the Lambda function itself is working.
"""

import boto3
import json
import sys

def test_lambda_direct():
    """Test the Lambda function directly."""
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event for health check
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
    
    try:
        print("🔍 Testing Lambda function directly...")
        print(f"   Function: crawlchat-api-function")
        print(f"   Event: {json.dumps(test_event, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName='crawlchat-api-function',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        print(f"   Status Code: {response['StatusCode']}")
        
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read())
            print(f"   ✅ Lambda executed successfully!")
            print(f"   Response: {json.dumps(payload, indent=2)}")
            return True
        else:
            print(f"   ❌ Lambda execution failed")
            print(f"   Error: {response}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error invoking Lambda: {e}")
        return False

def test_lambda_with_auth():
    """Test the Lambda function with auth endpoint."""
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event for auth endpoint
    test_event = {
        "httpMethod": "POST",
        "path": "/api/v1/auth/login",
        "headers": {
            "Content-Type": "application/json"
        },
        "queryStringParameters": None,
        "body": json.dumps({
            "email": "admin@crawlchat.site",
            "password": "admin123"
        }),
        "isBase64Encoded": False
    }
    
    try:
        print("\n🔐 Testing Lambda function with auth endpoint...")
        print(f"   Event: {json.dumps(test_event, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName='crawlchat-api-function',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        print(f"   Status Code: {response['StatusCode']}")
        
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read())
            print(f"   ✅ Lambda executed successfully!")
            print(f"   Response: {json.dumps(payload, indent=2)}")
            return True
        else:
            print(f"   ❌ Lambda execution failed")
            print(f"   Error: {response}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error invoking Lambda: {e}")
        return False

def main():
    """Main function."""
    print("🚀 CrawlChat Lambda Direct Test")
    print("=" * 40)
    
    # Test health endpoint
    health_success = test_lambda_direct()
    
    # Test auth endpoint
    auth_success = test_lambda_with_auth()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    print(f"   Health Endpoint: {'✅ Passed' if health_success else '❌ Failed'}")
    print(f"   Auth Endpoint: {'✅ Passed' if auth_success else '❌ Failed'}")
    
    if health_success and auth_success:
        print("\n✅ Lambda function is working correctly!")
        print("💡 The issue is with API Gateway configuration.")
        print("\n🔧 Next steps:")
        print("   1. Check API Gateway integration")
        print("   2. Verify Lambda permissions")
        print("   3. Check API Gateway deployment")
    else:
        print("\n❌ Lambda function has issues.")
        print("💡 Check the Lambda function configuration and logs.")

if __name__ == "__main__":
    main() 