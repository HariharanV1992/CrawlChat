#!/usr/bin/env python3
"""
Test script to check if vector store service is working properly.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vector_store():
    """Test the vector store service."""
    try:
        logger.info("🧪 Testing Vector Store Service...")
        
        # Check environment variables
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("❌ OPENAI_API_KEY environment variable not found!")
            return False
        
        logger.info("✅ OPENAI_API_KEY found")
        
        # Import services
        from common.src.services.vector_store_service import vector_store_service
        from common.src.services.document_processing_service import document_processing_service
        
        # Test 1: Create vector store
        logger.info("📦 Testing vector store creation...")
        vector_store_id = await vector_store_service.get_or_create_vector_store("Test Store")
        logger.info(f"✅ Vector store created/retrieved: {vector_store_id}")
        
        # Test 2: Upload test content
        logger.info("📄 Testing content upload...")
        test_content = "This is a test document for vector store functionality. It contains sample text to verify that the embedding and search features are working correctly."
        test_filename = "test_document.txt"
        
        file_id = await vector_store_service.upload_text_to_vector_store(
            text=test_content,
            filename=test_filename,
            vector_store_id=vector_store_id
        )
        logger.info(f"✅ Content uploaded with file ID: {file_id}")
        
        # Test 3: Wait for processing and search
        logger.info("⏳ Waiting for vector store processing...")
        await asyncio.sleep(10)  # Wait for OpenAI to process the file
        
        # Test 4: Search
        logger.info("🔍 Testing search functionality...")
        search_results = await vector_store_service.search_vector_store(
            query="test document",
            vector_store_id=vector_store_id,
            max_results=5
        )
        
        logger.info(f"✅ Search completed. Found {len(search_results.get('results', []))} results")
        
        # Test 5: Document processing service
        logger.info("📋 Testing document processing service...")
        result = await document_processing_service.process_document_with_vector_store(
            document_id="test-doc-123",
            content="This is another test document for processing service.",
            filename="test_processing.txt",
            metadata={"test": True},
            session_id="test-session-123"
        )
        
        logger.info(f"✅ Document processing completed: {result.get('status')}")
        
        logger.info("🎉 All vector store tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector store test failed: {e}")
        return False

async def test_s3_access():
    """Test S3 access for document retrieval."""
    try:
        logger.info("☁️ Testing S3 access...")
        
        from common.src.services.storage_service import StorageService
        
        storage_service = StorageService()
        
        # Test S3 bucket access
        bucket_info = storage_service.get_storage_info()
        logger.info(f"✅ S3 bucket info: {bucket_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ S3 access test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Starting CrawlChat Service Tests...")
    
    # Test S3 access
    s3_ok = await test_s3_access()
    
    # Test vector store
    vector_ok = await test_vector_store()
    
    if s3_ok and vector_ok:
        logger.info("🎉 All tests passed! The services are working correctly.")
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
    
    return s3_ok and vector_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 