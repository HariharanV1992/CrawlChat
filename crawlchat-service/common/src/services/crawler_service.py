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
from common.src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

# Import crawler modules from lambda-service (these are service-specific)
try:
    # Try to import from lambda-service crawler directory
    import sys
    import os
    
    # Try multiple possible paths for the crawler modules
    possible_paths = [
        # Path for Lambda deployment
        "/var/task/src",
        # Path for local development
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda-service', 'src'),
        # Path for common module structure
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'),
        # Current directory
        os.getcwd(),
        # Lambda task root
        "/var/task",
        # Additional Lambda paths
        "/var/task/lambda-service/src",
        "/var/task/crawlchat-service/lambda-service/src"
    ]
    
    crawler_imported = False
    for path in possible_paths:
        logger.info(f"Trying path: {path}")
        if os.path.exists(path):
            logger.info(f"Path exists: {path}")
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.info(f"Added {path} to sys.path")
            
            try:
                from crawler.advanced_crawler import AdvancedCrawler
                from crawler.settings_manager import SettingsManager
                logger.info(f"Successfully imported AdvancedCrawler and related modules from {path}")
                crawler_imported = True
                break
            except ImportError as e:
                logger.warning(f"Import failed from {path}: {e}")
                # Remove the path if import failed
                if path in sys.path:
                    sys.path.remove(path)
                continue
        else:
            logger.info(f"Path does not exist: {path}")
    
    if not crawler_imported:
        raise ImportError("Could not find crawler modules in any of the expected paths")
        
except ImportError as e:
    # Fallback for when crawler modules are not available
    logger.error(f"Failed to import crawler modules: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Python path: {sys.path}")
    AdvancedCrawler = None
    SettingsManager = None

class CrawlerService:
    """Crawler service for managing crawl tasks using MongoDB."""
    def __init__(self):
        self.running_tasks = {}  # Track running tasks for cancellation
        self.cancellation_events = {}  # Track cancellation events
        self.db = mongodb
        self.tasks: Dict[str, CrawlTask] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Check if crawler is available
        if not AdvancedCrawler:
            logger.warning("AdvancedCrawler not available - crawling functionality disabled")

    async def create_crawl_task(self, request: CrawlRequest, user_id: str) -> CrawlResponse:
        """Create a new crawl task."""
        if not AdvancedCrawler:
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
        self.tasks[task_id] = task
        
        # Save to database
        await self.db.get_collection("tasks").insert_one(task.dict())
        
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
        doc = await self.db.get_collection("tasks").find_one({"task_id": task_id})
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
                result = await self.db.get_collection("tasks").update_one(
                    {"task_id": task_id}, 
                    {"$set": update_data}
                )
                return result.modified_count > 0
            else:
                # Fallback if task not found
                result = await self.db.get_collection("tasks").update_one(
                    {"task_id": task_id}, 
                    {"$set": {"status": status, "updated_at": datetime.utcnow()}}
                )
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False

    async def list_user_tasks(self, user_id: str, limit: int = 50, skip: int = 0) -> List[CrawlTask]:
        cursor = self.db.get_collection("tasks").find({"user_id": user_id}).skip(skip).limit(limit)
        return [CrawlTask(**doc) async for doc in cursor]

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        result = await self.db.get_collection("tasks").delete_one({"task_id": task_id, "user_id": user_id})
        return result.deleted_count > 0

    async def set_task_completed(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.COMPLETED)

    async def set_task_running(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.RUNNING)

    async def set_task_cancelled(self, task_id: str) -> bool:
        return await self.update_task_status(task_id, TaskStatus.CANCELLED)

    async def start_crawl_task(self, task_id: str) -> CrawlStatus:
        """Start a crawl task."""
        if not AdvancedCrawler:
            raise Exception("Crawler functionality not available")
        
        task = self.tasks.get(task_id)
        if not task:
            raise Exception(f"Task {task_id} not found")
        
        if task.status != TaskStatus.PENDING:
            raise Exception(f"Task {task_id} is not in pending status")
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # Save to database
        await self.db.get_collection("tasks").update_one(
            {"task_id": task_id},
            {"$set": {"status": task.status.value, "started_at": task.started_at}}
        )
        
        # Start crawling in background
        crawl_task = asyncio.create_task(self._run_crawl_task(task))
        self.active_tasks[task_id] = crawl_task
        
        logger.info(f"Started crawl task {task_id}")
        
        return CrawlStatus(
            task_id=task_id,
            status=task.status.value,
            progress={"pages_crawled": 0, "documents_downloaded": 0},
            documents_downloaded=0,
            pages_crawled=0
        )
    
    async def _run_crawl_task(self, task: CrawlTask):
        """Run the actual crawl task."""
        try:
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
            
            # Initialize crawler
            crawler = AdvancedCrawler(
                api_key=task.proxy_api_key or "",
                output_dir=task.output_dir,
                max_depth=2,
                max_pages=task.max_pages,
                delay=task.delay,
                site_type='generic'
            )
            
            # Start crawling
            results = await crawler.crawl(task.url)
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.pages_crawled = results['crawling_stats']['total_urls_visited']
            task.documents_downloaded = results['crawling_stats']['successful_downloads']
            task.downloaded_files = results['downloaded_files']
            task.metadata = results
            
            # Save to database
            await self.db.get_collection("tasks").update_one(
                {"task_id": task.task_id},
                {"$set": {
                    "status": task.status.value,
                    "completed_at": task.completed_at,
                    "pages_crawled": task.pages_crawled,
                    "documents_downloaded": task.documents_downloaded,
                    "downloaded_files": task.downloaded_files,
                    "metadata": task.metadata
                }}
            )
            
            logger.info(f"Completed crawl task {task.task_id}: {task.documents_downloaded} documents")
            
        except Exception as e:
            logger.error(f"Crawl task {task.task_id} failed: {e}")
            
            # Update task with error
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.errors.append(str(e))
            
            # Save to database
            await self.db.get_collection("tasks").update_one(
                {"task_id": task.task_id},
                {"$set": {
                    "status": task.status.value,
                    "completed_at": task.completed_at,
                    "errors": task.errors
                }}
            )
        
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def get_crawl_status(self, task_id: str) -> CrawlStatus:
        """Get the status of a crawl task."""
        task = self.tasks.get(task_id)
        if not task:
            # Try to get from database
            task_data = await self.db.get_collection("tasks").find_one({"task_id": task_id})
            if not task_data:
                raise Exception(f"Task {task_id} not found")
            
            task = CrawlTask(**task_data)
            self.tasks[task_id] = task
        
        return CrawlStatus(
            task_id=task_id,
            status=task.status.value,
            progress={
                "pages_crawled": task.pages_crawled,
                "documents_downloaded": task.documents_downloaded,
                "total_pages": task.max_pages,
                "total_documents": task.max_documents
            },
            documents_downloaded=task.documents_downloaded,
            pages_crawled=task.pages_crawled,
            error_message=task.errors[-1] if task.errors else None,
            completed_at=task.completed_at
        )
    
    async def cancel_crawl_task(self, task_id: str) -> bool:
        """Cancel a crawl task."""
        task = self.tasks.get(task_id)
        if not task:
            raise Exception(f"Task {task_id} not found")
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise Exception(f"Task {task_id} cannot be cancelled")
        
        # Cancel active task
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        
        # Save to database
        await self.db.get_collection("tasks").update_one(
            {"task_id": task_id},
            {"$set": {"status": task.status.value, "completed_at": task.completed_at}}
        )
        
        logger.info(f"Cancelled crawl task {task_id}")
        return True
    
    async def get_crawl_results(self, task_id: str) -> CrawlResult:
        """Get the results of a completed crawl task."""
        task = self.tasks.get(task_id)
        if not task:
            # Try to get from database
            task_data = await self.db.get_collection("tasks").find_one({"task_id": task_id})
            if not task_data:
                raise Exception(f"Task {task_id} not found")
            
            task = CrawlTask(**task_data)
            self.tasks[task_id] = task
        
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise Exception(f"Task {task_id} is not completed")
        
        return CrawlResult(
            task_id=task_id,
            status=task.status,
            total_pages=task.pages_crawled,
            total_documents=task.documents_downloaded,
            errors=task.errors,
            files=task.downloaded_files,
            completed_at=task.completed_at
        )
    
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