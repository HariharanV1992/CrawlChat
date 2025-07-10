"""
Crawler API endpoints for Stock Market Crawler.
"""

import logging
import traceback
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import io

from common.src.models.crawler import (
    CrawlRequest, CrawlResponse, CrawlStatus, TaskList, 
    TaskStatus, CrawlTask, CrawlTaskCreate, CrawlTaskUpdate, CrawlTaskResponse, CrawlTaskListResponse
)
from common.src.services.crawler_service import crawler_service
from common.src.api.dependencies import get_current_user
from common.src.models.auth import UserResponse
from common.src.core.exceptions import CrawlerError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["crawler"])

@router.post("/tasks", response_model=CrawlResponse)
async def create_crawl_task(
    request: CrawlRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new crawl task."""
    print(f"=== CREATING CRAWL TASK VIA API ===")
    print(f"User ID: {current_user.user_id}")
    print(f"Request URL: {request.url}")
    print(f"Max documents: {request.max_documents}")
    print(f"Max pages: {request.max_pages}")
    
    logger.info(f"API: Creating crawl task for user {current_user.user_id} with URL: {request.url}")
    
    try:
        print("Calling crawler_service.create_crawl_task...")
        response = await crawler_service.create_crawl_task(
            request=request,
            user_id=current_user.user_id
        )
        print(f"Crawl task created successfully: {response.task_id}")
        logger.info(f"API: Crawl task created successfully: {response.task_id}")
        return response
    except CrawlerError as e:
        error_msg = f"API: CrawlerError creating crawl task: {e}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = f"API: Error creating crawl task: {e} (type={type(e)}, repr={repr(e)})"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create crawl task")

@router.post("/tasks/{task_id}/start")
async def start_crawl_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Start a crawl task."""
    print(f"=== STARTING CRAWL TASK VIA API ===")
    print(f"Task ID: {task_id}")
    print(f"User ID: {current_user.user_id}")
    
    logger.info(f"API: Starting crawl task {task_id} for user {current_user.user_id}")
    
    try:
        print("Calling crawler_service.start_crawl_task...")
        success = await crawler_service.start_crawl_task(task_id)
        if not success:
            error_msg = f"API: Task {task_id} not found or cannot be started"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise HTTPException(status_code=404, detail="Task not found or cannot be started")
        
        print(f"Task {task_id} started successfully")
        logger.info(f"API: Task {task_id} started successfully")
        return {"message": f"Task {task_id} started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"API: Error starting crawl task: {e}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to start crawl task")

@router.get("/tasks/{task_id}", response_model=CrawlStatus)
async def get_task_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get the status of a crawl task."""
    try:
        task = await crawler_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return CrawlStatus(
            task_id=task.task_id,
            status=task.status.value,
            progress={
                "pages_crawled": task.pages_crawled,
                "documents_downloaded": task.documents_downloaded,
                "max_pages": task.max_pages,
                "max_documents": task.max_documents
            },
            documents_downloaded=task.documents_downloaded,
            pages_crawled=task.pages_crawled,
            error_message=task.errors[-1] if task.errors else None,
            completed_at=task.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

@router.get("/tasks", response_model=TaskList)
async def list_tasks(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0)
):
    """List all crawl tasks for the current user."""
    try:
        tasks = await crawler_service.list_user_tasks(
            current_user.user_id, 
            limit=limit, 
            skip=skip
        )
        
        return TaskList(
            tasks=tasks,
            total_count=len(tasks)  # This should be improved with proper pagination
        )
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel a running crawl task."""
    try:
        success = await crawler_service.cancel_crawl_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
        
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")

@router.post("/tasks/{task_id}/cancel")
async def cancel_task_post(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel a running crawl task (POST method for compatibility)."""
    try:
        success = await crawler_service.cancel_crawl_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
        
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")

@router.delete("/tasks/{task_id}/delete")
async def delete_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a crawl task from the database."""
    try:
        success = await crawler_service.delete_crawl_task(task_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be deleted")
        
        return {"message": f"Task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.get("/tasks/{task_id}/documents")
async def get_task_documents(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get documents for a specific crawl task."""
    try:
        documents = await crawler_service.get_task_documents(task_id)
        if documents is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "documents": documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task documents")

@router.get("/stats")
async def get_crawler_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get crawler statistics."""
    try:
        active_tasks = len(crawler_service.active_tasks)
        
        return {
            "active_tasks": active_tasks,
            "total_tasks": len(crawler_service.active_tasks) + len(crawler_service.task_cancellation_events),
            "user_id": current_user.user_id
        }
        
    except Exception as e:
        logger.error(f"Error getting crawler stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get crawler stats") 

@router.post("/download")
async def download_file(
    url: str = Query(..., description="URL of the file to download"),
    render_js: bool = Query(False, description="Whether to render JavaScript"),
    wait: int = Query(0, description="Time to wait after page load (ms)"),
    block_ads: bool = Query(False, description="Block ad-related content"),
    block_resources: bool = Query(False, description="Block resource loading"),
    window_width: int = Query(1920, description="Browser viewport width"),
    window_height: int = Query(1080, description="Browser viewport height"),
    premium_proxy: bool = Query(False, description="Use premium proxies"),
    country_code: str = Query("in", description="Country code for geolocation"),
    stealth_proxy: bool = Query(False, description="Use stealth proxies"),
    own_proxy: str = Query(None, description="Use custom proxy"),
    forward_headers: bool = Query(False, description="Forward custom headers"),
    forward_headers_pure: bool = Query(False, description="Forward headers without ScrapingBee headers"),
    scraping_config: str = Query(None, description="Use pre-saved scraping configuration"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Download a file directly from URL using ScrapingBee."""
    try:
        logger.info(f"API: Downloading file from {url} for user {current_user.user_id}")
        
        # Create a temporary crawl task for file download
        from common.src.models.crawler import CrawlRequest
        request = CrawlRequest(
            url=url,
            max_pages=1,
            max_documents=1,
            render_js=render_js,
            wait=wait,
            block_ads=block_ads,
            block_resources=block_resources,
            window_width=window_width,
            window_height=window_height,
            premium_proxy=premium_proxy,
            country_code=country_code,
            stealth_proxy=stealth_proxy,
            own_proxy=own_proxy,
            forward_headers=forward_headers,
            forward_headers_pure=forward_headers_pure,
            download_file=True,  # Enable file download
            scraping_config=scraping_config
        )
        
        # Create and start the task
        response = await crawler_service.create_crawl_task(request, current_user.user_id)
        task_id = response.task_id
        
        # Start the task
        success = await crawler_service.start_crawl_task(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start download task")
        
        # Get the task result
        task = await crawler_service.get_task_status(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=500, detail="Download failed")
        
        # Get the downloaded content
        metadata = task.metadata
        if not metadata.get('success') or not metadata.get('content'):
            raise HTTPException(status_code=500, detail="No content downloaded")
        
        content = metadata['content']
        content_type = metadata.get('content_type', 'application/octet-stream')
        file_type = metadata.get('file_type', 'unknown')
        
        # Generate filename
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1] or f"download.{file_type}"
        
        # Return the file as a streaming response
        return StreamingResponse(
            io.BytesIO(content) if isinstance(content, bytes) else io.BytesIO(content.encode('utf-8')),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}") 