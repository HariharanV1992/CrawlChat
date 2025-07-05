#!/usr/bin/env python3
"""
Test template path in Lambda environment
"""

import os
import sys

def test_template_path():
    """Test if templates directory exists and is accessible."""
    print("Testing template paths...")
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if we're in Lambda
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        print("Running in Lambda environment")
    else:
        print("Running in local environment")
    
    # Test different template paths
    template_paths = [
        "templates",
        "/var/task/templates", 
        os.path.join(os.getcwd(), "templates"),
        os.path.join(os.path.dirname(__file__), "templates")
    ]
    
    for path in template_paths:
        exists = os.path.exists(path)
        print(f"Path '{path}': {'EXISTS' if exists else 'NOT FOUND'}")
        
        if exists:
            try:
                files = os.listdir(path)
                print(f"  Files in {path}: {files}")
                
                # Check for login.html specifically
                login_path = os.path.join(path, "login.html")
                if os.path.exists(login_path):
                    print(f"  ✅ login.html found at: {login_path}")
                else:
                    print(f"  ❌ login.html NOT found at: {login_path}")
                    
            except Exception as e:
                print(f"  Error listing {path}: {e}")
    
    # Test Jinja2Templates
    try:
        from fastapi.templating import Jinja2Templates
        
        print("\nTesting Jinja2Templates...")
        templates = Jinja2Templates(directory="/var/task/templates")
        print("✅ Jinja2Templates created successfully with /var/task/templates")
        
        # Try to get a template
        try:
            template = templates.get_template("login.html")
            print("✅ Template 'login.html' loaded successfully")
        except Exception as e:
            print(f"❌ Error loading template 'login.html': {e}")
            
    except Exception as e:
        print(f"❌ Error creating Jinja2Templates: {e}")

if __name__ == "__main__":
    test_template_path() 