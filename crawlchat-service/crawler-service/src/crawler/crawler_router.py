"""
Crawler API router for integration with main FastAPI application
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from typing import Dict, Any, List
import os
import sys
import uuid
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Import real crawler modules
try:
    from .advanced_crawler import AdvancedCrawler
    logger.info("Successfully imported AdvancedCrawler")
except ImportError as e:
    logger.warning(f"Failed to import AdvancedCrawler: {e}")
    # Try absolute import as fallback
    try:
        from advanced_crawler import AdvancedCrawler
        logger.info("Successfully imported AdvancedCrawler with absolute import")
    except ImportError as e2:
        logger.warning(f"Failed to import AdvancedCrawler with absolute import: {e2}")
        # Create dummy class for fallback
        class AdvancedCrawler:
            def __init__(self, api_key):
                self.api_key = api_key
            def crawl_url(self, url, **kwargs):
                return {"success": False, "error": "Crawler not available"}
            def close(self):
                pass

# In-memory task storage (in production, use database)
TASK_STORAGE = {}

router = APIRouter(tags=["crawler"])

@router.get("/health")
async def crawler_health():
    """Health check for crawler service."""
    try:
        # Check if ScrapingBee API key is available
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not api_key:
            return {"status": "unhealthy", "error": "SCRAPINGBEE_API_KEY not configured"}
        
        return {"status": "healthy", "message": "Crawler service is ready", "api_key_configured": bool(api_key)}
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
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="SCRAPINGBEE_API_KEY not configured")
        
        # Initialize crawler
        crawler = AdvancedCrawler(api_key=api_key)
        
        # Configure crawler parameters
        crawler_params = {
            "render_js": render_js,
            "max_documents": max_documents,
            "max_pages": max_pages
        }
        
        # Perform crawl
        result = crawler.crawl_url(url, **crawler_params)
        
        # Clean up
        crawler.close()
        
        logger.info(f"Crawl completed for URL: {url}")
        return {
            "success": result.get('success', False),
            "url": url,
            "result": result,
            "config": crawler_params
        }
        
    except Exception as e:
        logger.error(f"Crawl failed for URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")

@router.get("/config")
async def get_crawler_config():
    """Get crawler configuration."""
    try:
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        return {
            "scrapingbee_configured": bool(api_key),
            "default_config": {
                "render_js": True,
                "max_documents": 5,
                "max_pages": 10
            }
        }
    except Exception as e:
        logger.error(f"Failed to get crawler config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

@router.post("/tasks")
async def create_task(request_data: Dict[str, Any] = Body(...)):
    """Create a new crawler task."""
    try:
        task_id = str(uuid.uuid4())
        
        # Extract task parameters
        url = request_data.get("url", "")
        max_documents = request_data.get("max_documents", 5)
        max_pages = request_data.get("max_pages", 10)
        render_js = request_data.get("render_js", True)
        
        # Create task record
        task = {
            "task_id": task_id,
            "url": url,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "config": {
                "max_documents": max_documents,
                "max_pages": max_pages,
                "render_js": render_js
            },
            "progress": {
                "documents_found": 0,
                "pages_crawled": 0,
                "documents_processed": 0
            },
            "result": None,
            "error": None
        }
        
        # Store task
        TASK_STORAGE[task_id] = task
        
        logger.info(f"Created crawler task: {task_id} for URL: {url}")
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created successfully",
            "url": url
        }
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    """Start a crawler task."""
    try:
        if task_id not in TASK_STORAGE:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = TASK_STORAGE[task_id]
        if task["status"] in ["running", "completed", "failed"]:
            return {
                "task_id": task_id,
                "status": task["status"],
                "message": f"Task is already {task['status']}"
            }
        
        # Update task status
        task["status"] = "running"
        task["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting crawler task: {task_id}")
        
        # Start crawling in background
        asyncio.create_task(run_crawl_task(task_id))
        
        return {
            "task_id": task_id,
            "status": "running",
            "message": "Task started successfully"
        }
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")

async def run_crawl_task(task_id: str):
    """Run the actual crawling task in background."""
    try:
        task = TASK_STORAGE[task_id]
        url = task["url"]
        config = task["config"]
        
        logger.info(f"Running crawl task {task_id} for URL: {url}")
        
        # Get API key
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not api_key:
            task["status"] = "failed"
            task["error"] = "SCRAPINGBEE_API_KEY not configured"
            task["updated_at"] = datetime.utcnow().isoformat()
            return
        
        # Initialize crawler
        crawler = AdvancedCrawler(api_key=api_key)
        
        try:
            # Perform crawl
            result = crawler.crawl_url(url, **config)
            
            # Update task with results
            task["status"] = "completed" if result.get("success", False) else "failed"
            task["result"] = result
            task["error"] = result.get("error") if not result.get("success", False) else None
            task["progress"]["documents_found"] = result.get("documents_found", 0)
            task["progress"]["pages_crawled"] = result.get("pages_crawled", 0)
            task["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Crawl task {task_id} completed with status: {task['status']}")
            
        finally:
            crawler.close()
            
    except Exception as e:
        logger.error(f"Crawl task {task_id} failed: {e}")
        task["status"] = "failed"
        task["error"] = str(e)
        task["updated_at"] = datetime.utcnow().isoformat()

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status."""
    try:
        if task_id not in TASK_STORAGE:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = TASK_STORAGE[task_id]
        logger.info(f"Getting status for task: {task_id} - Status: {task['status']}")
        
        return {
            "task_id": task_id,
            "status": task["status"],
            "url": task["url"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
            "progress": task["progress"],
            "config": task["config"],
            "result": task["result"],
            "error": task["error"]
        }
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")

@router.get("/tasks")
async def list_tasks():
    """List all crawler tasks."""
    try:
        logger.info("Listing crawler tasks")
        
        tasks = []
        for task_id, task in TASK_STORAGE.items():
            tasks.append({
                "task_id": task_id,
                "status": task["status"],
                "url": task["url"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "progress": task["progress"]
            })
        
        # Sort by creation date (newest first)
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

logger.info("Crawler router created with real functionality:")
for route in router.routes:
    if hasattr(route, 'path'):
        logger.info(f"  {route.path} - Methods: {getattr(route, 'methods', 'N/A')}") 