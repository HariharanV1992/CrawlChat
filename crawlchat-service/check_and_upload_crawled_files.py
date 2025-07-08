#!/usr/bin/env python3
"""
Script to check for crawled files and upload them to S3 if they exist locally.
"""

import os
import asyncio
import logging
from pathlib import Path
from common.src.services.storage_service import get_storage_service
from common.src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_upload_crawled_files():
    """Check for crawled files and upload them to S3."""
    
    # Check the crawler output directory
    output_dir = "/tmp/crawled_data"
    logger.info(f"Checking for crawled files in: {output_dir}")
    
    if not os.path.exists(output_dir):
        logger.warning(f"Output directory {output_dir} does not exist")
        return
    
    # List all files in the output directory
    files_found = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            files_found.append(file_path)
            logger.info(f"Found file: {file_path}")
    
    if not files_found:
        logger.info("No crawled files found")
        return
    
    logger.info(f"Found {len(files_found)} files to upload")
    
    # Get storage service
    storage_service = get_storage_service()
    
    # Upload each file to S3
    uploaded_count = 0
    for file_path in files_found:
        try:
            # Create S3 key based on file path
            relative_path = os.path.relpath(file_path, output_dir)
            s3_key = f"crawled_documents/{relative_path}"
            
            logger.info(f"Uploading {file_path} to S3 key: {s3_key}")
            
            # Upload file
            success = await storage_service.upload_file(file_path, s3_key)
            if success:
                uploaded_count += 1
                logger.info(f"Successfully uploaded: {s3_key}")
            else:
                logger.error(f"Failed to upload: {file_path}")
                
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {e}")
    
    logger.info(f"Uploaded {uploaded_count} out of {len(files_found)} files to S3")

if __name__ == "__main__":
    asyncio.run(check_and_upload_crawled_files()) 