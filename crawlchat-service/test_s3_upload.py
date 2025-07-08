#!/usr/bin/env python3
"""
Test script to check S3 upload functionality.
"""

import asyncio
import logging
from common.src.services.storage_service import get_storage_service
from common.src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_s3_upload():
    """Test S3 upload functionality."""
    
    logger.info("Testing S3 upload functionality...")
    
    # Get storage service
    storage_service = get_storage_service()
    
    # Check if S3 is configured
    storage_info = storage_service.get_storage_info()
    logger.info(f"Storage info: {storage_info}")
    
    if not storage_info['s3_configured']:
        logger.error("S3 is not configured!")
        return
    
    logger.info(f"S3 bucket: {storage_info['s3_bucket']}")
    
    # Create a test file
    test_content = b"This is a test file for S3 upload functionality."
    test_s3_key = "test_upload/test_file.txt"
    
    try:
        # Upload test file
        logger.info(f"Uploading test file to S3: {test_s3_key}")
        result = await storage_service.upload_file_from_bytes(test_content, test_s3_key, "text/plain")
        logger.info(f"Upload successful: {result}")
        
        # Verify the file exists
        logger.info("Verifying file exists in S3...")
        file_content = await storage_service.get_file_content(test_s3_key)
        if file_content:
            logger.info(f"File verification successful: {len(file_content)} bytes")
        else:
            logger.error("File verification failed!")
            
    except Exception as e:
        logger.error(f"S3 upload test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_s3_upload()) 