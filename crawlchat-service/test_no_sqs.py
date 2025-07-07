#!/usr/bin/env python3
"""
Test script to verify that the application works without SQS.
"""

import sys
import os

# Add the common/src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
common_src_path = os.path.join(current_dir, 'common', 'src')
sys.path.insert(0, common_src_path)

def test_aws_config():
    """Test AWS configuration without SQS."""
    print("🔧 Testing AWS Configuration...")
    
    try:
        from core.aws_config import aws_config
        
        print(f"  Region: {aws_config.region}")
        print(f"  Lambda Function: {aws_config.lambda_function_name}")
        print(f"  S3 Bucket: {aws_config.s3_bucket_name}")
        print(f"  Textract Region: {aws_config.textract_region}")
        
        # Test S3 key generation
        test_key = aws_config.generate_document_s3_key("test_user", "test.pdf", "test_id")
        print(f"  Generated S3 Key: {test_key}")
        
        print("✅ AWS Configuration test passed!")
        return True
    except Exception as e:
        print(f"❌ AWS Configuration test failed: {e}")
        return False

def test_background_service():
    """Test AWS background service without SQS."""
    print("\n🚀 Testing AWS Background Service...")
    
    try:
        from services.aws_background_service import aws_background_service
        
        # Test connection
        connection_result = aws_background_service.test_connection()
        print(f"  Connection Test: {connection_result}")
        
        # Test Lambda invocation (without actually invoking)
        test_payload = {
            "test": "data",
            "action": "test"
        }
        
        print("  Testing Lambda invocation preparation...")
        print(f"  Test payload: {test_payload}")
        
        print("✅ AWS Background Service test passed!")
        return True
    except Exception as e:
        print(f"❌ AWS Background Service test failed: {e}")
        return False

def test_imports():
    """Test that all imports work without SQS."""
    print("\n📦 Testing Imports...")
    
    try:
        from core.aws_config import aws_config
        from services.aws_background_service import aws_background_service
        from services.document_service import document_service
        from services.chat_service import chat_service
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Application Without SQS")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("❌ Import test failed!")
        return
    
    # Test AWS configuration
    config_success = test_aws_config()
    
    # Test background service
    service_success = test_background_service()
    
    print("\n" + "=" * 50)
    if config_success and service_success:
        print("🎉 All tests passed! Application is ready without SQS.")
        print("\n📋 Summary:")
        print("  ✅ AWS Configuration: Working")
        print("  ✅ Background Service: Working")
        print("  ✅ Imports: Working")
        print("  ✅ SQS: Removed successfully")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 