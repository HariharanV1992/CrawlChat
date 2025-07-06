#!/usr/bin/env python3
"""
Test script to verify Lambda template handling
"""

import json
import os
import sys

# Test event for Lambda
test_event = {
    "httpMethod": "GET",
    "path": "/login",
    "headers": {
        "Content-Type": "application/json"
    },
    "queryStringParameters": None,
    "body": None,
    "isBase64Encoded": False
}

def test_template_paths():
    """Test if template paths exist and are accessible"""
    print("=== Testing Template Paths ===")
    
    # Test different possible template paths
    template_paths = [
        "templates",
        "/var/task/templates", 
        os.path.join(os.getcwd(), "templates")
    ]
    
    for path in template_paths:
        exists = os.path.exists(path)
        print(f"Path '{path}': {'EXISTS' if exists else 'NOT FOUND'}")
        
        if exists:
            try:
                files = os.listdir(path)
                print(f"  Files: {files}")
                
                # Check for specific template files
                expected_templates = ["login.html", "register.html", "chat.html", "crawler.html"]
                for template in expected_templates:
                    template_file = os.path.join(path, template)
                    if os.path.exists(template_file):
                        print(f"  ✓ {template} found")
                    else:
                        print(f"  ✗ {template} missing")
                        
            except Exception as e:
                print(f"  Error listing {path}: {e}")
    
    print()

def test_lambda_handler():
    """Test the Lambda handler with a template request"""
    print("=== Testing Lambda Handler ===")
    
    try:
        # Import the handler
        from lambda_handler import handler
        print("✓ Lambda handler imported successfully")
        
        # Test the handler with login request
        print("Testing /login endpoint...")
        response = handler(test_event, None)
        
        print(f"Response status: {response.get('statusCode', 'N/A')}")
        print(f"Response headers: {response.get('headers', {})}")
        
        if response.get('statusCode') == 200:
            print("✓ Template served successfully")
        else:
            print(f"✗ Template serving failed: {response}")
            
    except Exception as e:
        print(f"✗ Error testing Lambda handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Lambda environment:", os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    print()
    
    test_template_paths()
    test_lambda_handler() 