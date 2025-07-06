#!/usr/bin/env python3
"""
Test script to verify the deployment setup.
"""

import os
import sys
import subprocess

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        # Test common package imports
        from common.src.core.config import config
        print("✓ Common config import successful")
        
        from common.src.core.database import mongodb
        print("✓ Common database import successful")
        
        from common.src.models.auth import User
        print("✓ Common models import successful")
        
        from common.src.services.storage_service import get_storage_service
        print("✓ Common services import successful")
        
        # Test lambda service imports
        sys.path.insert(0, 'lambda-service')
        from src.services.auth_service import auth_service
        print("✓ Lambda auth service import successful")
        
        from src.services.chat_service import chat_service
        print("✓ Lambda chat service import successful")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_template_files():
    """Test that template files exist."""
    print("\nTesting template files...")
    
    template_files = [
        "templates/chat.html",
        "templates/login.html", 
        "templates/register.html",
        "templates/crawler.html",
        "templates/confirm_email.html"
    ]
    
    all_exist = True
    for template in template_files:
        if os.path.exists(template):
            print(f"✓ {template} exists")
        else:
            print(f"❌ {template} missing")
            all_exist = False
    
    return all_exist

def test_static_files():
    """Test that static files exist."""
    print("\nTesting static files...")
    
    static_dirs = ["static/css", "static/js", "static/images"]
    
    all_exist = True
    for static_dir in static_dirs:
        if os.path.exists(static_dir):
            print(f"✓ {static_dir} exists")
        else:
            print(f"❌ {static_dir} missing")
            all_exist = False
    
    return all_exist

def test_requirements():
    """Test that requirements can be installed."""
    print("\nTesting requirements...")
    
    try:
        # Test installing common package
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "common"], 
                      check=True, capture_output=True)
        print("✓ Common package install successful")
        
        # Test lambda requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "lambda-service/requirements.txt"], 
                      check=True, capture_output=True)
        print("✓ Lambda requirements install successful")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Requirements install failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing CrawlChat deployment setup...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Template Files", test_template_files),
        ("Static Files", test_static_files),
        ("Requirements", test_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 