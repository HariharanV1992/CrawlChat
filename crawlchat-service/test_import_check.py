#!/usr/bin/env python3
"""
Script to test crawler router import and verify all paths work correctly
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import_paths():
    """Test all possible import paths for crawler router"""
    print("🔍 Testing Crawler Router Import Paths")
    print("=" * 50)
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Test possible paths
    possible_paths = [
        os.path.join(current_dir, 'crawler-service', 'src'),  # From crawlchat-service root
        os.path.join(current_dir, '..', 'crawler-service', 'src'),  # From lambda-service
        os.path.join('/var/task', 'crawler-service', 'src'),  # Lambda container
        os.path.join(os.getcwd(), 'crawler-service', 'src'),  # Current working directory
    ]
    
    print("\n📁 Testing path existence:")
    for i, path in enumerate(possible_paths, 1):
        exists = os.path.exists(path)
        print(f"  {i}. {path}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
        
        if exists:
            try:
                files = os.listdir(path)
                print(f"     Files: {files}")
            except Exception as e:
                print(f"     Error listing files: {e}")
    
    # Test import logic
    print("\n🔧 Testing import logic:")
    crawler_path = None
    for path in possible_paths:
        if os.path.exists(path):
            crawler_path = path
            print(f"✅ Found crawler path: {crawler_path}")
            break
    
    if not crawler_path:
        print("❌ No crawler path found!")
        return False
    
    # Test adding to sys.path
    print(f"\n📦 Adding to sys.path: {crawler_path}")
    sys.path.insert(0, crawler_path)
    print(f"✅ Added to sys.path. Current sys.path[0]: {sys.path[0]}")
    
    # Test importing crawler router
    print("\n🚀 Testing crawler router import:")
    try:
        from crawler.crawler_router import router as crawler_router
        print("✅ Successfully imported crawler router!")
        
        # Test router properties
        print(f"✅ Router tags: {crawler_router.tags}")
        print(f"✅ Router prefix: {crawler_router.prefix}")
        print(f"✅ Number of routes: {len(crawler_router.routes)}")
        
        # List all routes
        print("\n📋 Router endpoints:")
        for route in crawler_router.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', set())
                print(f"  {route.path} - Methods: {methods}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI integration"""
    print("\n🔗 Testing FastAPI Integration")
    print("=" * 50)
    
    try:
        from fastapi import FastAPI
        from crawler.crawler_router import router as crawler_router
        
        app = FastAPI()
        app.include_router(crawler_router, prefix="/api/v1/crawler")
        
        print("✅ FastAPI app created successfully")
        print(f"✅ Router included with prefix: /api/v1/crawler")
        
        # Check final routes
        print("\n🌐 Final API routes:")
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', set())
                print(f"  {route.path} - Methods: {methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Crawler Router Import Test")
    print("=" * 50)
    
    # Test 1: Import paths
    import_success = test_import_paths()
    
    # Test 2: FastAPI integration
    if import_success:
        fastapi_success = test_fastapi_integration()
    else:
        fastapi_success = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Import Test: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"FastAPI Test: {'✅ PASSED' if fastapi_success else '❌ FAILED'}")
    
    if import_success and fastapi_success:
        print("\n🎉 All tests passed! The crawler router should work correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 