#!/usr/bin/env python3
"""
Test script to verify unified storage service functionality.
"""

import asyncio
import logging
from common.src.services.unified_storage_service import unified_storage_service
from common.src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_unified_storage():
    """Test unified storage service functionality."""
    
    logger.info("Testing unified storage service...")
    
    # Check storage configuration
    storage_info = unified_storage_service.get_storage_info()
    logger.info(f"Storage info: {storage_info}")
    
    if not storage_info['s3_configured']:
        logger.error("S3 is not configured!")
        return
    
    # Test user document upload
    logger.info("\n=== Testing User Document Upload ===")
    test_content = b"This is a test document for unified storage service."
    test_filename = "test_document.txt"
    test_user_id = "test_user_123"
    
    try:
        result = await unified_storage_service.upload_user_document(
            file_content=test_content,
            filename=test_filename,
            user_id=test_user_id,
            content_type="text/plain"
        )
        
        logger.info(f"Upload successful: {result}")
        s3_key = result["s3_key"]
        
        # Test file retrieval
        logger.info("\n=== Testing File Retrieval ===")
        retrieved_content = await unified_storage_service.get_file_content(s3_key)
        
        if retrieved_content:
            logger.info(f"Retrieved content: {len(retrieved_content)} bytes")
            if retrieved_content == test_content:
                logger.info("✅ Content integrity verified!")
            else:
                logger.error("❌ Content integrity check failed!")
        else:
            logger.error("❌ Failed to retrieve file content!")
        
        # Test crawled content upload
        logger.info("\n=== Testing Crawled Content Upload ===")
        crawled_content = "This is crawled content from a website."
        crawled_filename = "crawled_page.html"
        task_id = "test_task_456"
        
        crawled_result = await unified_storage_service.upload_crawled_content(
            content=crawled_content,
            filename=crawled_filename,
            task_id=task_id,
            user_id=test_user_id,
            metadata={
                "source_url": "https://example.com",
                "crawl_depth": 1
            }
        )
        
        logger.info(f"Crawled content upload successful: {crawled_result}")
        
        # Test file deletion
        logger.info("\n=== Testing File Deletion ===")
        delete_success = await unified_storage_service.delete_file(s3_key)
        if delete_success:
            logger.info("✅ File deletion successful!")
        else:
            logger.error("❌ File deletion failed!")
        
        # Verify deletion
        retrieved_after_delete = await unified_storage_service.get_file_content(s3_key)
        if not retrieved_after_delete:
            logger.info("✅ File deletion verified!")
        else:
            logger.error("❌ File still exists after deletion!")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_storage()) 