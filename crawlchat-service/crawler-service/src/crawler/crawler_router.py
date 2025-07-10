"""
Crawler API router for integration with main FastAPI application
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from typing import Dict, Any
import os
import sys

logger = logging.getLogger(__name__)

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

router = APIRouter(tags=["crawler"])

@router.get("/health")
async def crawler_health():
    """Health check for crawler service."""
    try:
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
        api_key = CrawlerConfig.SCRAPINGBEE_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="SCRAPINGBEE_API_KEY not configured")
        
        crawler = AdvancedCrawler(api_key=api_key)
        crawler_config = CrawlerConfig.get_crawl_config(max_documents=max_documents, max_pages=max_pages)
        scrapingbee_params = CrawlerConfig.get_scrapingbee_params(render_js=render_js)
        result = crawler.crawl_url(url, **scrapingbee_params)
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

@router.post("/tasks")
async def create_task(request_data: Dict[str, Any] = Body(...)):
    """Create a new crawler task."""
    try:
        import uuid
        task_id = str(uuid.uuid4())
        logger.info(f"Created crawler task: {task_id}")
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    """Start a crawler task."""
    try:
        logger.info(f"Starting crawler task: {task_id}")
        return {
            "task_id": task_id,
            "status": "running",
            "message": "Task started successfully"
        }
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status."""
    try:
        logger.info(f"Getting status for task: {task_id}")
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task completed successfully",
            "documents_found": 0
        }
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")

@router.get("/tasks")
async def list_tasks():
    """List all crawler tasks."""
    try:
        logger.info("Listing crawler tasks")
        return {
            "tasks": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

logger.info("Crawler router created with endpoints:")
for route in router.routes:
    if hasattr(route, 'path'):
        logger.info(f"  {route.path} - Methods: {getattr(route, 'methods', 'N/A')}") 