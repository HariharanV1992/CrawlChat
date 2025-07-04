#!/usr/bin/env python3
"""
Simple test to check if Lambda handler can start
"""

import os
import sys

# Set Lambda environment
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-function'

try:
    # Test basic imports
    print("Testing basic imports...")
    import fastapi
    import mangum
    print("✅ FastAPI and Mangum imports successful")
    
    # Test if we can import the main app
    print("Testing main app import...")
    from main import app
    print("✅ Main app import successful")
    
    # Test if we can create the handler
    print("Testing handler creation...")
    from lambda_handler import handler
    print("✅ Lambda handler creation successful")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 