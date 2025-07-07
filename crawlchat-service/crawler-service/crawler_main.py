#!/usr/bin/env python3
"""
CrawlChat Crawler Service
High-performance web crawler for document extraction and processing.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from common.src.core.logging import setup_logging
from common.src.core.config import get_settings
from common.src.services.crawler_service import crawler_service
from src.crawler.advanced_crawler import AdvancedCrawler
from models.crawler import CrawlConfig

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    """Main crawler service entry point."""
    try:
        logger.info("🚀 Starting CrawlChat Crawler Service")
        
        # Initialize settings
        settings = get_settings()
        logger.info(f"Configuration loaded: {settings.model_dump()}")
        
        # Initialize crawler service
        await crawler_service.initialize()
        logger.info("✅ Crawler service initialized")
        
        # Keep the service running
        logger.info("🔄 Crawler service is running...")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Crawler service stopped by user")
    except Exception as e:
        logger.error(f"❌ Crawler service error: {e}")
        raise
    finally:
        # Cleanup
        await crawler_service.cleanup()
        logger.info("🧹 Crawler service cleanup completed")

if __name__ == "__main__":
    asyncio.run(main()) 