"""
Crawler API router for integration with main FastAPI application
"""

import logging
import json
import traceback
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from typing import Dict, Any, List
import os
import sys
import uuid
from datetime import datetime
import asyncio

# Setup logger first
logger = logging.getLogger(__name__)

# Import database modules
try:
    from common.src.core.database import mongodb
    from common.src.core.config import config
    logger.info("Successfully imported database modules")
except ImportError as e:
    logger.warning(f"Failed to import database modules: {e}")
    # Try alternative import paths
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common', 'src'))
        from core.database import mongodb
        from core.config import config
        logger.info("Successfully imported database modules with alternative path")
    except ImportError as e2:
        logger.warning(f"Failed to import database modules with alternative path: {e2}")
        mongodb = None
        config = None

# Import real crawler modules
try:
    from .advanced_crawler import AdvancedCrawler
    from .enhanced_crawler_service import EnhancedCrawlerService
    logger.info("Successfully imported AdvancedCrawler and EnhancedCrawlerService")
except ImportError as e:
    logger.warning(f"Failed to import crawler modules: {e}")
    # Try absolute import as fallback
    try:
        from advanced_crawler import AdvancedCrawler
        from enhanced_crawler_service import EnhancedCrawlerService
        logger.info("Successfully imported crawler modules with absolute import")
    except ImportError as e2:
        logger.warning(f"Failed to import crawler modules with absolute import: {e2}")
        # Create dummy classes for fallback
        class AdvancedCrawler:
            def __init__(self, api_key):
                self.api_key = api_key
            def crawl_url(self, url, **kwargs):
                return {"success": False, "error": "Crawler not available"}
            def close(self):
                pass
        
        class EnhancedCrawlerService:
            def __init__(self, api_key):
                self.api_key = api_key
            def crawl_with_max_docs(self, url, max_doc_count=1):
                return {"success": False, "error": "Enhanced crawler not available"}

# Database task storage - will be initialized when needed
TASK_STORAGE = {}  # Fallback in-memory storage

# Database functions for task persistence
async def ensure_database_connection():
    """Ensure MongoDB connection is established."""
    if mongodb is None:
        logger.warning("MongoDB not available, using in-memory storage")
        return False
    
    try:
        if mongodb.db is None:
            await mongodb.connect()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False

async def save_task_to_db(task_data: Dict[str, Any]) -> bool:
    """Save task to database."""
    if not await ensure_database_connection():
        return False
    
    try:
        collection = mongodb.db.crawler_tasks
        result = await collection.replace_one(
            {"task_id": task_data["task_id"]},
            task_data,
            upsert=True
        )
        logger.info(f"Task {task_data['task_id']} saved to database: {result.modified_count} modified, {result.upserted_id} upserted")
        return True
    except Exception as e:
        logger.error(f"Failed to save task to database: {e}")
        return False

async def get_task_from_db(task_id: str) -> Dict[str, Any]:
    """Get task from database."""
    if not await ensure_database_connection():
        return None
    
    try:
        collection = mongodb.db.crawler_tasks
        task = await collection.find_one({"task_id": task_id})
        return task
    except Exception as e:
        logger.error(f"Failed to get task from database: {e}")
        return None

async def get_all_tasks_from_db() -> List[Dict[str, Any]]:
    """Get all tasks from database."""
    if not await ensure_database_connection():
        return []
    
    try:
        collection = mongodb.db.crawler_tasks
        cursor = collection.find({}).sort("created_at", -1)
        tasks = await cursor.to_list(length=None)
        return tasks
    except Exception as e:
        logger.error(f"Failed to get tasks from database: {e}")
        return []

async def delete_task_from_db(task_id: str) -> bool:
    """Delete task from database."""
    if not await ensure_database_connection():
        return False
    
    try:
        collection = mongodb.db.crawler_tasks
        result = await collection.delete_one({"task_id": task_id})
        logger.info(f"Task {task_id} deleted from database: {result.deleted_count} deleted")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Failed to delete task from database: {e}")
        return False

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
        
        # Initialize enhanced crawler service
        enhanced_crawler = EnhancedCrawlerService(api_key=api_key)
        
        # Use enhanced crawler with max document count
        result = enhanced_crawler.crawl_with_max_docs(url, max_doc_count=max_documents)
        
        logger.info(f"Crawl completed for URL: {url}")
        return {
            "success": result.get('success', False),
            "url": url,
            "result": result,
            "config": {
                "render_js": render_js,
                "max_documents": max_documents,
                "max_pages": max_pages
            }
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
        
        # Store task in database and memory
        await save_task_to_db(task)
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
    logger.error(f"CRAWLER STARTED: /tasks/{task_id}/start called for task_id={task_id}")
    try:
        if task_id not in TASK_STORAGE:
            logger.error(f"CRAWLER ERROR: Task {task_id} not found in TASK_STORAGE at start")
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = TASK_STORAGE[task_id]
        if task["status"] in ["running", "completed", "failed"]:
            logger.error(f"CRAWLER STATUS: Task {task_id} is already {task['status']}")
            return {
                "task_id": task_id,
                "status": task["status"],
                "message": f"Task is already {task['status']}"
            }
        
        # Update task status
        task["status"] = "running"
        task["updated_at"] = datetime.utcnow().isoformat()
        
        # Save updated task to database
        await save_task_to_db(task)
        
        logger.error(f"CRAWLER: Starting crawler task: {task_id}")
        
        # Run the crawl task directly in this Lambda function
        logger.error(f"CRAWLER: Starting local crawl execution for task {task_id}")
        
        # Run the crawl task directly (not asynchronously)
        await run_crawl_task(task_id)
        
        logger.error(f"CRAWLER: Task {task_id} completed successfully!")
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task completed successfully"
        }
    except Exception as e:
        logger.error(f"CRAWLER EXCEPTION in /tasks/{{task_id}}/start: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")

async def run_crawl_task(task_id: str):
    logger.error(f"CRAWLER: run_crawl_task called for task_id={task_id}")
    try:
        task = TASK_STORAGE[task_id]
        url = task["url"]
        config = task["config"]
        
        logger.error(f"CRAWLER: === STARTING CRAWL TASK {task_id} ===")
        logger.error(f"CRAWLER: URL: {url}")
        logger.error(f"CRAWLER: Config: {config}")
        
        # Get API key
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not api_key:
            error_msg = "SCRAPINGBEE_API_KEY not configured"
            logger.error(f"Crawl task {task_id} failed: {error_msg}")
            task["status"] = "failed"
            task["error"] = error_msg
            task["updated_at"] = datetime.utcnow().isoformat()
            return
        
        logger.info(f"ScrapingBee API key configured: {api_key[:10]}...")
        
        # Initialize enhanced crawler service
        logger.info(f"Initializing EnhancedCrawlerService for task {task_id}")
        try:
            enhanced_crawler = EnhancedCrawlerService(api_key=api_key)
            logger.info(f"EnhancedCrawlerService initialized successfully")
        except Exception as init_error:
            logger.error(f"Failed to initialize EnhancedCrawlerService: {init_error}")
            task["status"] = "failed"
            task["error"] = f"Failed to initialize crawler: {str(init_error)}"
            task["updated_at"] = datetime.utcnow().isoformat()
            await save_task_to_db(task)
            return
        
        try:
            # Get max document count from config
            max_documents = config.get('max_documents', 1)
            logger.info(f"Starting crawl with max_documents: {max_documents}")
            
            # Use enhanced crawler with max document count support
            logger.info(f"Calling enhanced_crawler.crawl_with_max_docs for task {task_id}")
            logger.info(f"Parameters: url={url}, max_doc_count={max_documents}")
            
            try:
                result = enhanced_crawler.crawl_with_max_docs(url, max_doc_count=max_documents)
                logger.info(f"Crawl completed for task {task_id}. Result: {result}")
            except Exception as crawl_error:
                logger.error(f"Exception during crawl_with_max_docs for task {task_id}: {crawl_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                task["status"] = "failed"
                task["error"] = f"Crawl execution failed: {str(crawl_error)}"
                task["updated_at"] = datetime.utcnow().isoformat()
                await save_task_to_db(task)
                return
            
            # Update task with enhanced results
            success = result.get("success", False)
            task["status"] = "completed" if success else "failed"
            task["result"] = result
            task["error"] = result.get("error") if not success else None
            
            # Set progress from enhanced crawler results
            documents_found = result.get("documents_found", 0)
            total_pages = result.get("total_pages", 0)
            documents_processed = len(result.get("documents", []))
            
            task["progress"]["documents_found"] = documents_found
            task["progress"]["pages_crawled"] = total_pages
            task["progress"]["documents_processed"] = documents_processed
                
            task["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated task to database
            await save_task_to_db(task)
            
            logger.info(f"=== CRAWL TASK {task_id} COMPLETED ===")
            logger.info(f"Status: {task['status']}")
            logger.info(f"Documents found: {documents_found}")
            logger.info(f"Pages crawled: {total_pages}")
            logger.info(f"Documents processed: {documents_processed}")
            
            if not success:
                logger.error(f"Crawl failed for task {task_id}: {result.get('error', 'Unknown error')}")
            
        except Exception as crawl_error:
            logger.error(f"Exception during crawl execution for task {task_id}: {crawl_error}")
            task["status"] = "failed"
            task["error"] = str(crawl_error)
            task["updated_at"] = datetime.utcnow().isoformat()
            
            # Save failed task to database
            await save_task_to_db(task)
            
    except Exception as e:
        logger.error(f"=== CRAWL TASK {task_id} FAILED ===")
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if task_id in TASK_STORAGE:
            task = TASK_STORAGE[task_id]
            task["status"] = "failed"
            task["error"] = str(e)
            task["updated_at"] = datetime.utcnow().isoformat()
            
            # Save failed task to database
            await save_task_to_db(task)
        else:
            logger.error(f"Task {task_id} not found in TASK_STORAGE")

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status."""
    try:
        # First check in-memory storage
        if task_id in TASK_STORAGE:
            task = TASK_STORAGE[task_id]
        else:
            # Try to load from database
            task = await get_task_from_db(task_id)
            if task:
                # Load into memory for faster access
                TASK_STORAGE[task_id] = task
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        
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
        
        # Load tasks from database
        db_tasks = await get_all_tasks_from_db()
        
        # Update in-memory storage with database tasks
        for task in db_tasks:
            TASK_STORAGE[task["task_id"]] = task
        
        # Create response list
        tasks = []
        for task in db_tasks:
            tasks.append({
                "task_id": task["task_id"],
                "status": task["status"],
                "url": task["url"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "progress": task["progress"]
            })
        
        # Sort by creation date (newest first)
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.info(f"Found {len(tasks)} tasks in database")
        
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a crawler task."""
    try:
        logger.info(f"Deleting task: {task_id}")
        
        # Delete from database
        db_deleted = await delete_task_from_db(task_id)
        
        # Delete from memory
        memory_deleted = task_id in TASK_STORAGE
        if memory_deleted:
            del TASK_STORAGE[task_id]
        
        if db_deleted or memory_deleted:
            logger.info(f"Task {task_id} deleted successfully")
            return {
                "task_id": task_id,
                "message": "Task deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

logger.info("Crawler router created with real functionality:")
for route in router.routes:
    if hasattr(route, 'path'):
        logger.info(f"  {route.path} - Methods: {getattr(route, 'methods', 'N/A')}") 