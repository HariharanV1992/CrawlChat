#!/usr/bin/env python3
"""
Test script to verify crawler cancel functionality
"""

import asyncio
import sys
import os

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common', 'src'))

from common.src.services.crawler_service import crawler_service
from common.src.models.crawler import CrawlTaskCreate, TaskStatus
from common.src.core.database import mongodb
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cancel_functionality():
    """Test the cancel functionality"""
    
    # Initialize database connection
    logger.info("Initializing database connection...")
    await mongodb.connect()
    
    try:
        # Create a test task
        logger.info("Creating test crawl task...")
        task = await crawler_service.create_crawl_task(
            url="https://example.com",
            user_id="test_user",
            crawl_config={
                "max_pages": 5,
                "max_documents": 3,
                "crawl_delay": 1
            }
        )
        
        if not task:
            logger.error("Failed to create test task")
            return
        
        task_id = task.task_id
        logger.info(f"Created task: {task_id}")
        
        # Start the task
        logger.info("Starting the task...")
        success = await crawler_service.start_crawl_task(task_id)
        if not success:
            logger.error("Failed to start task")
            return
        
        # Wait a bit for the task to start
        await asyncio.sleep(2)
        
        # Check task status
        task_status = await crawler_service.get_task_status(task_id)
        logger.info(f"Task status after start: {task_status.status if task_status else 'None'}")
        
        # Cancel the task
        logger.info("Cancelling the task...")
        cancel_success = await crawler_service.cancel_crawl_task(task_id)
        logger.info(f"Cancel result: {cancel_success}")
        
        # Check task status after cancellation
        await asyncio.sleep(1)
        task_status = await crawler_service.get_task_status(task_id)
        logger.info(f"Task status after cancel: {task_status.status if task_status else 'None'}")
        
        # Clean up
        logger.info("Cleaning up test task...")
        await crawler_service.delete_crawl_task(task_id, "test_user")
        
        logger.info("Test completed!")
        
    finally:
        # Close database connection
        await mongodb.close()

if __name__ == "__main__":
    asyncio.run(test_cancel_functionality()) 