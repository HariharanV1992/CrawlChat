"""
Crawler API router for integration with main FastAPI application
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
import os
import sys

# Add the crawler modules to path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, '..'))

try:
    from crawler.advanced_crawler import AdvancedCrawler
    from config.crawler_config import CrawlerConfig
except ImportError as e:
    logger.error(f"Failed to import crawler modules: {e}")
    # Create dummy classes for fallback
    class AdvancedCrawler:
        def __init__(self, api_key):
            self.api_key = api_key
        def crawl_url(self, url, **kwargs):
            return {"success": False, "error": "Crawler not available"}
        def close(self):
            pass
    
    class CrawlerConfig:
        SCRAPINGBEE_API_KEY = None
        @staticmethod
        def get_crawl_config(**kwargs):
            return {"error": "Config not available"}
        @staticmethod
        def get_scrapingbee_params(**kwargs):
            return {"error": "Config not available"}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])

@router.get("/health")
async def crawler_health():
    """Health check for crawler service."""
    try:
        # Check if ScrapingBee API key is available
        api_key = CrawlerConfig.SCRAPINGBEE_API_KEY
        if not api_key:
            return {"status": "unhealthy", "error": "SCRAPINGBEE_API_KEY not configured"}
        
        return {"status": "healthy", "message": "Crawler service is ready"}
    except Exception as e:
        logger.error(f"Crawler health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.post("/crawl")
async def crawl_url(
    url: str = Query(..., description="URL to crawl"),
    render_js: bool = Query(True, description="Enable JavaScript rendering"),
    max_documents: int = Query(5, description="Maximum documents to download"),
    max_pages: int = Query(10, description="Maximum pages to crawl")
):
    """Simple crawl endpoint for testing."""
    try:
        logger.info(f"Starting crawl for URL: {url}")
        
        # Get API key
        api_key = CrawlerConfig.SCRAPINGBEE_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="SCRAPINGBEE_API_KEY not configured")
        
        # Initialize crawler
        crawler = AdvancedCrawler(api_key=api_key)
        
        # Configure crawler
        crawler_config = CrawlerConfig.get_crawl_config(
            max_documents=max_documents,
            max_pages=max_pages
        )
        
        # Get ScrapingBee parameters
        scrapingbee_params = CrawlerConfig.get_scrapingbee_params(
            render_js=render_js
        )
        
        # Perform crawl
        result = crawler.crawl_url(url, **scrapingbee_params)
        
        # Clean up
        crawler.close()
        
        logger.info(f"Crawl completed for URL: {url}")
        return {
            "success": result.get('success', False),
            "url": url,
            "result": result,
            "config": crawler_config
        }
        
    except Exception as e:
        logger.error(f"Crawl failed for URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")

@router.get("/config")
async def get_crawler_config():
    """Get crawler configuration."""
    try:
        return {
            "scrapingbee_configured": bool(CrawlerConfig.SCRAPINGBEE_API_KEY),
            "default_config": CrawlerConfig.get_crawl_config(),
            "default_scrapingbee_params": CrawlerConfig.get_scrapingbee_params()
        }
    except Exception as e:
        logger.error(f"Failed to get crawler config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}") 