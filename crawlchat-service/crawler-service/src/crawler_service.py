"""
Production crawler service with database integration and monitoring
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from common.src.core.database import mongodb
from common.src.models.crawler import CrawlTask, TaskStatus, CrawlConfig, CrawlRequest, CrawlResponse, CrawlStatus, CrawlResult
from common.src.models.documents import Document, DocumentType
from common.src.services.storage_service import get_storage_service
from common.src.core.config import config
from common.src.core.exceptions import CrawlerError, DatabaseError
from common.src.models.auth import User, UserCreate, Token, TokenData

# Import crawler modules
try:
    from src.crawler.advanced_crawler import AdvancedCrawler
    CRAWLER_AVAILABLE = True
except ImportError:
    try:
        from crawler.advanced_crawler import AdvancedCrawler
        CRAWLER_AVAILABLE = True
    except ImportError:
        CRAWLER_AVAILABLE = False
        AdvancedCrawler = None

logger = logging.getLogger(__name__)

class CrawlerService:
    """Crawler service for managing crawl tasks using MongoDB."""
    def __init__(self):
        self.running_tasks = {}  # Track running tasks for cancellation
        self.cancellation_events = {}  # Track cancellation events
        
        # Check if crawler is available
        if not CRAWLER_AVAILABLE:
            logger.warning("AdvancedCrawler not available - crawling functionality disabled")

    async def create_crawl_task(self, request: CrawlRequest, user_id: str) -> CrawlResponse:
        """Create a new crawl task."""
        if not CRAWLER_AVAILABLE:
            raise Exception("Crawler functionality not available")
        
        task_id = str(uuid.uuid4())
        
        # Create crawl task
        task = CrawlTask(
            task_id=task_id,
            user_id=user_id,
            url=str(request.url),
            max_documents=request.max_documents,
            max_pages=request.max_pages,
            max_workers=request.max_workers,
            delay=request.delay,
            total_timeout=request.total_timeout,
            page_timeout=request.page_timeout,
            request_timeout=request.request_timeout
        )
        
        # Store task
        self.running_tasks[task_id] = task
        
        logger.info(f"Created crawl task {task_id} for user {user_id}")
        
        return CrawlResponse(
            task_id=task_id,
            status=task.status.value,
            message="Crawl task created successfully",
            url=str(request.url),
            max_documents=request.max_documents,
            created_at=task.created_at
        )

    async def get_task_status(self, task_id: str) -> Optional[CrawlTask]:
        doc = await mongodb.get_collection("tasks").find_one({"task_id": task_id})
        if doc:
            return CrawlTask(**doc)
        return None

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status while preserving progress fields."""
        try:
            # Get current task to preserve progress fields
            task = await self.get_task_status(task_id)
            if task:
                # Preserve progress fields when updating status
                update_data = {
                    "status": status, 
                    "updated_at": datetime.utcnow(),
                    "pages_crawled": task.pages_crawled,
                    "documents_downloaded": task.documents_downloaded
                }
                result = await mongodb.get_collection("tasks").update_one(
                    {"task_id": task_id}, 
                    {"$set": update_data}
                )
                return result.modified_count > 0
            else:
                # Fallback if task not found
                result = await mongodb.get_collection("tasks").update_one(
                    {"task_id": task_id}, 
                    {"$set": {"status": status, "updated_at": datetime.utcnow()}}
                )
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False

    async def list_user_tasks(self, user_id: str, limit: int = 50, skip: int = 0) -> List[CrawlTask]:
        cursor = mongodb.get_collection("tasks").find({"user_id": user_id}).skip(skip).limit(limit)
        return [CrawlTask(**doc) async for doc in cursor]

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        result = await mongodb.get_collection("tasks").delete_one({"task_id": task_id, "user_id": user_id})
        return result.deleted_count > 0

    async def set_task_completed(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.COMPLETED)

    async def set_task_running(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.RUNNING)

    async def set_task_cancelled(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.CANCELLED)

    async def start_crawl_task(self, task_id: str) -> CrawlStatus:
        """Start a crawl task."""
        if not CRAWLER_AVAILABLE:
            raise Exception("Crawler functionality not available")
        
        task = await self.get_task_status(task_id)
        if not task:
            raise Exception(f"Task {task_id} not found")
        
        if task.status != TaskStatus.PENDING:
            raise Exception(f"Task {task_id} is not in pending status")
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # Create cancellation event
        cancellation_event = asyncio.Event()
        self.cancellation_events[task_id] = cancellation_event
        
        # Start crawl task
        crawl_task = asyncio.create_task(
            self._run_crawl_task(task_id, task, cancellation_event)
        )
        
        # Store the running task for cancellation
        self.running_tasks[task_id] = crawl_task
        
        logger.info(f"Started crawl task {task_id}")
        
        return CrawlStatus(
            task_id=task_id,
            status=task.status.value,
            progress={"pages_crawled": 0, "documents_downloaded": 0},
            documents_downloaded=0,
            pages_crawled=0
        )
    
    async def _run_crawl_task(self, task_id: str, task: CrawlTask, cancellation_event: asyncio.Event):
        """Run the actual crawl task."""
        start_time = datetime.utcnow()
        final_progress = {"pages_crawled": 0, "documents_downloaded": 0}
        
        try:
            if not AdvancedCrawler:
                raise CrawlerError("AdvancedCrawler not available")
            
            # Create crawler configuration
            crawler_config = CrawlConfig(
                max_documents=task.max_documents,
                max_pages=task.max_pages,
                max_workers=task.max_workers,
                delay=task.delay,
                total_timeout=task.total_timeout,
                page_timeout=task.page_timeout,
                request_timeout=task.request_timeout,
                use_proxy=task.use_proxy,
                proxy_api_key=task.proxy_api_key,
                render=task.render,
                retry=task.retry
            )
            
            # Create progress callback
            async def progress_callback(progress: Dict[str, Any]):
                # Check for cancellation before updating progress
                if cancellation_event.is_set():
                    raise asyncio.CancelledError()
                
                final_progress.update(progress)
                await self._update_task_progress(task_id, progress)
            
            # Run crawler
            async with AdvancedCrawler(task.url, crawler_config, progress_callback, user_id=task.user_id) as crawler:
                # Set task_id for document saving
                crawler.task_id = task_id
                
                # Check for cancellation
                if cancellation_event.is_set():
                    crawler.cancel()
                    return
                
                # Start the crawl
                await crawler.crawl()
            
            # Update task as completed
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self._update_task_completion(task_id, TaskStatus.COMPLETED, processing_time, final_progress=final_progress)
            
        except asyncio.CancelledError:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self._update_task_completion(task_id, TaskStatus.CANCELLED, processing_time, "Task was cancelled by user", final_progress=final_progress)
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Crawl task {task_id} failed after {processing_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            await self._update_task_completion(task_id, TaskStatus.FAILED, processing_time, str(e), final_progress=final_progress)
        
        finally:
            # Clean up task tracking
            self.running_tasks.pop(task_id, None)
            self.cancellation_events.pop(task_id, None)
    
    async def _update_task_progress(self, task_id: str, progress: Dict[str, Any]):
        """Update task progress in storage."""
        try:
            task = await self.get_task_status(task_id)
            if task:
                task.pages_crawled = progress.get('pages_crawled', 0)
                task.documents_downloaded = progress.get('documents_downloaded', 0)
                await self.update_task_status(task_id, TaskStatus.RUNNING)
            else:
                logger.warning(f"Task {task_id} not found when updating progress")
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
    
    async def _update_task_completion(self, task_id: str, status: TaskStatus, 
                                    processing_time: float, error_message: Optional[str] = None, final_progress: Dict[str, Any] = None):
        """Update task completion status."""
        try:
            task = await self.get_task_status(task_id)
            if task:
                task.status = status
                task.completed_at = datetime.utcnow()
                if error_message:
                    task.errors.append(error_message)
                
                # Preserve progress fields when updating status
                update_data = {
                    "status": status, 
                    "updated_at": datetime.utcnow(),
                    "completed_at": task.completed_at,
                    "pages_crawled": task.pages_crawled,
                    "documents_downloaded": task.documents_downloaded
                }
                if error_message:
                    update_data["errors"] = task.errors
                if final_progress:
                    update_data.update(final_progress)
                
                result = await mongodb.get_collection("tasks").update_one(
                    {"task_id": task_id},
                    {"$set": update_data}
                )
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating task completion: {e}")
            return False
    
    def _get_document_type(self, extension: str) -> DocumentType:
        """Get document type from file extension."""
        extension_map = {
            '.pdf': DocumentType.PDF,
            '.doc': DocumentType.DOC,
            '.docx': DocumentType.DOCX,
            '.txt': DocumentType.TXT,
            '.html': DocumentType.HTML,
        }
        return extension_map.get(extension.lower(), DocumentType.TXT)
    
    async def cancel_crawl_task(self, task_id: str) -> bool:
        """Cancel a running crawl task."""
        try:
            # Get the task to check if it exists
            task = await self.get_task_status(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for cancellation")
                return False
            
            # Set cancellation event if it exists
            if task_id in self.cancellation_events:
                self.cancellation_events[task_id].set()
            
            # Cancel the running task if it exists
            if task_id in self.running_tasks:
                running_task = self.running_tasks[task_id]
                if not running_task.done():
                    running_task.cancel()
            
            # Update task status to cancelled
                await self.update_task_status(task_id, TaskStatus.CANCELLED)
            
            # Clean up tracking
            self.running_tasks.pop(task_id, None)
            self.cancellation_events.pop(task_id, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling crawl task {task_id}: {e}")
            return False

    async def delete_crawl_task(self, task_id: str, user_id: str) -> bool:
        """Delete a crawl task and its associated documents from the database."""
        try:
            # First, get the task to check if it exists and belongs to the user
            task = await self.get_task_status(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for deletion")
                return False
            
            if task.user_id != user_id:
                logger.warning(f"User {user_id} attempted to delete task {task_id} owned by {task.user_id}")
                return False
            
            # Delete associated documents first
            try:
                from common.src.services.document_service import DocumentService
                document_service = DocumentService()
                documents = await document_service.get_task_documents(task_id)
                
                for doc in documents:
                    try:
                        await document_service.delete_document_by_filename(doc.filename)
                        logger.info(f"Deleted document {doc.filename} for task {task_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete document {doc.filename}: {e}")
                        
            except ImportError:
                logger.warning("Document service not available, skipping document deletion")
            except Exception as e:
                logger.warning(f"Error deleting documents for task {task_id}: {e}")
            
            # Delete the task from database
            success = await self.delete_task(task_id, user_id)
            if success:
                logger.info(f"Deleted crawl task {task_id} and associated documents")
            else:
                logger.warning(f"Failed to delete task {task_id} from database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting crawl task {task_id}: {e}")
            return False
    
    async def get_task_documents(self, task_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get documents for a specific crawl task."""
        try:
            # Verify task exists
            task = await self.get_task_status(task_id)
            if not task:
                return None
            
            # Use the new document service to get actual documents
            try:
                from common.src.services.document_service import DocumentService
                document_service = DocumentService()
                
                # Get documents for this task
                documents = await document_service.get_task_documents(task_id)
                
                # Convert to API response format
                document_list = []
                for doc in documents:
                    document_list.append({
                        "document_id": doc.document_id,
                        "filename": doc.filename,
                        "file_path": doc.file_path,
                        "file_size": doc.file_size,
                        "document_type": doc.document_type.value,
                        "status": doc.status.value,
                        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                        "metadata": doc.metadata
                    })
                
                return document_list
                
            except ImportError:
                # Fallback to basic file info if document service not available
                documents = []
                for file_path in task.downloaded_files:
                    documents.append({
                        "filename": Path(file_path).name,
                        "file_path": file_path,
                        "created_at": task.created_at.isoformat(),
                        "processed": False
                    })
                return documents
            
        except Exception as e:
            logger.error(f"Error getting task documents: {e}")
            return None

# Global crawler service instance
crawler_service = CrawlerService() 