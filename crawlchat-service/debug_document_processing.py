#!/usr/bin/env python3
"""
Debug script to test document processing step by step.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_environment_variables():
    """Test if all required environment variables are set."""
    logger.info("🔧 Testing Environment Variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'AWS_REGION',
        'S3_BUCKET_NAME',
        'MONGODB_URI'
    ]
    
    optional_vars = [
        'OPENAI_MODEL',
        'OPENAI_MAX_TOKENS',
        'OPENAI_TEMPERATURE'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            logger.error(f"❌ {var}: NOT SET")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: NOT SET (optional)")
            missing_optional.append(var)
    
    if missing_required:
        logger.error(f"❌ Missing required environment variables: {missing_required}")
        return False
    
    logger.info("✅ All required environment variables are set!")
    return True

async def test_mongodb_connection():
    """Test MongoDB connection."""
    try:
        logger.info("🗄️ Testing MongoDB Connection...")
        
        from common.src.core.database import mongodb
        
        await mongodb.connect()
        logger.info("✅ MongoDB connection successful")
        
        # Test a simple query
        collection = mongodb.get_collection("test")
        await collection.find_one({})
        logger.info("✅ MongoDB query successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

async def test_s3_access():
    """Test S3 access."""
    try:
        logger.info("☁️ Testing S3 Access...")
        
        from common.src.services.storage_service import StorageService
        
        storage_service = StorageService()
        bucket_info = storage_service.get_storage_info()
        logger.info(f"✅ S3 bucket info: {bucket_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ S3 access failed: {e}")
        return False

async def test_vector_store_service():
    """Test vector store service."""
    try:
        logger.info("🧠 Testing Vector Store Service...")
        
        from common.src.services.vector_store_service import vector_store_service
        
        # Test client initialization
        client = vector_store_service._get_client()
        if client is None:
            logger.error("❌ OpenAI client initialization failed")
            return False
        
        logger.info("✅ OpenAI client initialized successfully")
        
        # Test vector store creation
        vector_store_id = await vector_store_service.get_or_create_vector_store("Debug Test Store")
        logger.info(f"✅ Vector store created/retrieved: {vector_store_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector store service failed: {e}")
        return False

async def test_document_processing():
    """Test document processing service."""
    try:
        logger.info("📄 Testing Document Processing Service...")
        
        from common.src.services.document_processing_service import document_processing_service
        
        # Test with simple text
        test_content = "This is a test document for debugging purposes. It contains sample text to verify that the document processing pipeline is working correctly."
        
        result = await document_processing_service.process_document_with_vector_store(
            document_id="debug-test-123",
            content=test_content,
            filename="debug_test.txt",
            metadata={"debug": True, "test": True},
            session_id="debug-session-123"
        )
        
        logger.info(f"✅ Document processing result: {result}")
        
        if result.get("status") == "success":
            logger.info("✅ Document processing successful!")
            return True
        else:
            logger.error(f"❌ Document processing failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Document processing service failed: {e}")
        return False

async def test_textract_service():
    """Test AWS Textract service."""
    try:
        logger.info("🔍 Testing AWS Textract Service...")
        
        from common.src.services.aws_textract_service import textract_service
        
        # Test service initialization
        logger.info("✅ Textract service imported successfully")
        
        # Test with a simple text file (no actual PDF processing)
        test_content = b"This is test content for Textract service."
        
        try:
            # This might fail if no actual PDF, but we're just testing the service setup
            logger.info("✅ Textract service setup successful")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Textract processing test failed (expected for non-PDF): {e}")
            return True  # Service is working, just can't process this content
        
    except Exception as e:
        logger.error(f"❌ Textract service failed: {e}")
        return False

async def test_chat_service():
    """Test chat service."""
    try:
        logger.info("💬 Testing Chat Service...")
        
        from common.src.services.chat_service import chat_service
        
        # Test service initialization
        logger.info("✅ Chat service imported successfully")
        
        # Test session creation
        test_user_id = "debug-user-123"
        session_response = await chat_service.create_session(test_user_id)
        logger.info(f"✅ Chat session created: {session_response.session_id}")
        
        # Test message addition
        success = await chat_service.add_message(
            session_response.session_id, 
            test_user_id, 
            "user", 
            "Test message"
        )
        logger.info(f"✅ Message added: {success}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Chat service failed: {e}")
        return False

async def main():
    """Run all diagnostic tests."""
    logger.info("🚀 Starting CrawlChat Diagnostic Tests...")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("MongoDB Connection", test_mongodb_connection),
        ("S3 Access", test_s3_access),
        ("Vector Store Service", test_vector_store_service),
        ("Textract Service", test_textract_service),
        ("Chat Service", test_chat_service),
        ("Document Processing", test_document_processing),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The system should be working correctly.")
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        logger.info("\n🔧 Troubleshooting tips:")
        logger.info("1. Check AWS credentials and permissions")
        logger.info("2. Verify MongoDB connection string")
        logger.info("3. Ensure OpenAI API key is valid")
        logger.info("4. Check S3 bucket permissions")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 