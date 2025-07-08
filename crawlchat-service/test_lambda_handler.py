#!/usr/bin/env python3
"""
Test script to verify Lambda handler can be imported and called correctly.
"""

import os
import sys
import json
from pathlib import Path

# Add the lambda-service to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service"))

def test_handler_import():
    """Test that the handler can be imported correctly."""
    print("🧪 Testing Lambda Handler Import")
    print("=" * 50)
    
    try:
        # Import the handler
        from lambda_handler import handler, lambda_handler
        
        print("✅ Successfully imported handler and lambda_handler")
        print(f"   handler type: {type(handler)}")
        print(f"   lambda_handler type: {type(lambda_handler)}")
        
        # Test that they are the same function
        if handler == lambda_handler:
            print("✅ handler and lambda_handler are the same function")
        else:
            print("❌ handler and lambda_handler are different functions")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_handler_call():
    """Test that the handler can be called with a simple event."""
    print("\n🧪 Testing Lambda Handler Call")
    print("=" * 50)
    
    try:
        from lambda_handler import handler
        
        # Create a simple test event
        test_event = {
            "url": "https://httpbin.org/html",
            "content_type": "generic",
            "country_code": "in"
        }
        
        print(f"📝 Test event: {json.dumps(test_event, indent=2)}")
        
        # Call the handler (this will fail without API key, but should not crash)
        try:
            result = handler(test_event, None)
            print(f"✅ Handler called successfully")
            print(f"   Status code: {result.get('statusCode')}")
            print(f"   Body: {result.get('body', '')[:200]}...")
        except Exception as e:
            if "SCRAPINGBEE_API_KEY not configured" in str(e):
                print("✅ Handler called successfully (expected error without API key)")
            else:
                print(f"❌ Handler call failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Handler call test failed: {e}")
        return False

def test_module_structure():
    """Test that the module structure is correct."""
    print("\n🧪 Testing Module Structure")
    print("=" * 50)
    
    try:
        import lambda_handler
        
        # Check if handler function exists
        if hasattr(lambda_handler, 'handler'):
            print("✅ handler function exists in module")
        else:
            print("❌ handler function missing from module")
            return False
        
        # Check if lambda_handler function exists
        if hasattr(lambda_handler, 'lambda_handler'):
            print("✅ lambda_handler function exists in module")
        else:
            print("❌ lambda_handler function missing from module")
            return False
        
        # Check if they are the same
        if lambda_handler.handler == lambda_handler.lambda_handler:
            print("✅ handler and lambda_handler are the same function")
        else:
            print("❌ handler and lambda_handler are different functions")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Module structure test failed: {e}")
        return False

def main():
    """Run all Lambda handler tests."""
    print("🔧 Lambda Handler Test Suite")
    print("Testing Lambda handler import and functionality")
    print("=" * 80)
    
    tests = [
        ("Handler Import", test_handler_import),
        ("Module Structure", test_module_structure),
        ("Handler Call", test_handler_call),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Lambda handler is working correctly.")
        print("✅ The handler function is properly exported")
        print("✅ Lambda should be able to find and call the handler")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 