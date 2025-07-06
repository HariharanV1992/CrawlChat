#!/usr/bin/env python3
"""
Simple test to debug import issues
"""

import sys
import os
from pathlib import Path

def test_path():
    """Test the current path setup."""
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Check if src directory exists
    lambda_src = Path("lambda-service/src").resolve()
    if lambda_src.exists():
        print(f"✅ Lambda src exists: {lambda_src}")
        print(f"Lambda src contents: {list(lambda_src.iterdir())}")
    else:
        print(f"❌ Lambda src does not exist: {lambda_src}")
    
    # Try to add to path and import
    try:
        sys.path.insert(0, str(lambda_src))
        print(f"Added {lambda_src} to path")
        print(f"New Python path: {sys.path}")
        
        # Try to import
        import src.core.config
        print("✅ Successfully imported src.core.config")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    test_path() 