#!/usr/bin/env python3
"""
List all Lambda functions to identify the container-based one.
"""

import boto3
import os

def list_lambdas():
    """List all Lambda functions."""
    
    print("📋 Listing all Lambda functions...")
    
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    try:
        lambda_client = boto3.client("lambda", region_name=region)
        
        response = lambda_client.list_functions()
        
        for function in response['Functions']:
            print(f"📦 Function: {function['FunctionName']}")
            print(f"   Runtime: {function.get('Runtime', 'Container')}")
            print(f"   Package Type: {function.get('PackageType', 'Unknown')}")
            print(f"   Handler: {function.get('Handler', 'N/A')}")
            print(f"   Timeout: {function.get('Timeout', 'N/A')}")
            print(f"   Memory: {function.get('MemorySize', 'N/A')} MB")
            print("---")
            
    except Exception as e:
        print(f"❌ Error listing functions: {e}")

if __name__ == "__main__":
    list_lambdas() 