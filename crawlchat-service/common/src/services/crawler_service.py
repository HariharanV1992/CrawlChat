"""
Production crawler service with database integration and monitoring
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
import traceback

from common.src.core.database import mongodb
from common.src.models.crawler import CrawlTask, TaskStatus, CrawlConfig, CrawlRequest, CrawlResponse, CrawlStatus, CrawlResult
from common.src.models.documents import Document, DocumentType
from common.src.services.unified_storage_service import unified_storage_service
from common.src.services.storage_service import get_storage_service
from common.src.core.config import config
from common.src.core.exceptions import CrawlerError, DatabaseError
from common.src.models.auth import User, UserCreate, Token, TokenData
from common.src.services.document_service import DocumentService
# SQS helper removed - no longer needed for direct Lambda invocation
# from common.src.services.sqs_helper import sqs_helper

logger = logging.getLogger(__name__)

# Global variables for lazy loading
_AdvancedCrawler = None
_SettingsManager = None

def get_advanced_crawler():
    """Lazy load AdvancedCrawler to avoid cold start issues."""
    global _AdvancedCrawler
    
    if _AdvancedCrawler is None:
        try:
            logger.info("Loading AdvancedCrawler...")
            
            # Try to import from lambda-service crawler directory
            import sys
            import os
            
            # Try multiple possible paths for the crawler modules
            # Prioritize lambda-service version which has the correct __init__ signature
            possible_paths = [
                # Path for Lambda deployment (primary) - lambda-service version
                "/var/task/src",
                # Path for local development - lambda-service version
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda-service', 'src'),
                # Additional Lambda paths - lambda-service version
                "/var/task/lambda-service/src",
                "/var/task/crawlchat-service/lambda-service/src",
                # Fallback paths (avoid crawler-service version)
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'),
                # Current directory
                os.getcwd(),
                # Lambda task root
                "/var/task",
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
                        
                        # Verify this is the lambda-service version by checking __init__ signature
                        import inspect
                        init_signature = inspect.signature(AdvancedCrawler.__init__)
                        init_params = list(init_signature.parameters.keys())
                        
                        logger.info(f"AdvancedCrawler __init__ parameters: {init_params}")
                        
                        # Lambda-service version should have api_key and settings parameters
                        # Crawler-service version has base_url parameter which we don't want
                        if 'base_url' in init_params:
                            logger.warning(f"Found crawler-service version at {path} (has base_url parameter), skipping...")
                            # Remove the path if it's the wrong version
                            if path in sys.path:
                                sys.path.remove(path)
                            continue
                        
                        if 'api_key' in init_params:
                            logger.info(f"Successfully imported lambda-service AdvancedCrawler from {path}")
                            _AdvancedCrawler = AdvancedCrawler
                            _SettingsManager = SettingsManager
                            crawler_imported = True
                            break
                        else:
                            logger.warning(f"AdvancedCrawler at {path} has unexpected signature: {init_params}")
                            # Remove the path if import failed
                            if path in sys.path:
                                sys.path.remove(path)
                            continue
                            
                    except ImportError as e:
                        logger.warning(f"Import failed from {path}: {e}")
                        # Remove the path if import failed
                        if path in sys.path:
                            sys.path.remove(path)
                        continue
                else:
                    logger.info(f"Path does not exist: {path}")
            
            if not crawler_imported:
                raise ImportError("Could not find lambda-service crawler modules in any of the expected paths")
                
        except ImportError as e:
            # Fallback for when crawler modules are not available
            logger.error(f"Failed to import crawler modules: {e}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Python path: {sys.path}")
            _AdvancedCrawler = None
            _SettingsManager = None
    
    return _AdvancedCrawler

def get_settings_manager():
    """Lazy load SettingsManager to avoid cold start issues."""
    global _SettingsManager
    
    if _SettingsManager is None:
        # This will trigger the import of both AdvancedCrawler and SettingsManager
        get_advanced_crawler()
    
    return _SettingsManager

class CrawlerService:
    """Crawler service for managing crawl tasks using MongoDB."""
    def __init__(self):
        self.running_tasks = {}  # Track running tasks for cancellation
        self.cancellation_events = {}  # Track cancellation events
        self.db = mongodb
        self.tasks: Dict[str, CrawlTask] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Don't check crawler availability during initialization
        # This will be done when actually needed

    async def create_crawl_task(self, request: CrawlRequest, user_id: str) -> CrawlResponse:
        """Create a new crawl task."""
        logger.info(f"Creating crawl task for user {user_id} with URL: {request.url}")
        
        try:
            # Check if crawler is available only when needed
            AdvancedCrawler = get_advanced_crawler()
            if not AdvancedCrawler:
                error_msg = "AdvancedCrawler not available - cannot create crawl task"
                logger.error(error_msg)
                raise Exception("Crawler functionality not available")
            
            task_id = str(uuid.uuid4())
            logger.info(f"Generated task ID: {task_id}")
            
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
                request_timeout=request.request_timeout,
                # ScrapingBee parameters - use getattr with defaults
                render_js=getattr(request, 'render_js', True),
                block_ads=getattr(request, 'block_ads', False),
                block_resources=getattr(request, 'block_resources', True),
                wait=getattr(request, 'wait', None),
                wait_for=getattr(request, 'wait_for', None),
                wait_browser=getattr(request, 'wait_browser', None),
                window_width=getattr(request, 'window_width', 1920),
                window_height=getattr(request, 'window_height', 1080),
                premium_proxy=getattr(request, 'premium_proxy', False),
                country_code=getattr(request, 'country_code', 'in'),
                stealth_proxy=getattr(request, 'stealth_proxy', False),
                own_proxy=getattr(request, 'own_proxy', None),
                forward_headers=getattr(request, 'forward_headers', False),
                forward_headers_pure=getattr(request, 'forward_headers_pure', False),
                download_file=getattr(request, 'download_file', False),
                scraping_config=getattr(request, 'scraping_config', None)
            )
            print("CrawlTask object created successfully")
            
            # Store task in memory
            print("Storing task in memory...")
            self.tasks[task_id] = task
            
            # Save to database
            print("Saving task to database...")
            try:
                await self.db.get_collection("tasks").insert_one(task.model_dump())
                logger.info(f"Task {task_id} saved to database")
                print(f"Task {task_id} saved to database successfully")
            except Exception as e:
                error_msg = f"Failed to save task {task_id} to database: {e}"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                raise
            
            logger.info(f"Created crawl task {task_id} for user {user_id}")
            print(f"Created crawl task {task_id} for user {user_id}")
            
            return CrawlResponse(
                task_id=task_id,
                status=task.status.value,
                message="Crawl task created successfully",
                url=str(request.url),
                max_documents=request.max_documents,
                created_at=task.created_at
            )
            
        except Exception as e:
            error_msg = f"Error creating crawl task: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

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

    async def start_crawl_task(self, task_id: str, user_id: str = None) -> CrawlStatus:
        """Start a crawl task by sending it to SQS."""
        print(f"=== STARTING CRAWL TASK ===")
        print(f"Task ID: {task_id}")
        print(f"User ID: {user_id}")
        
        logger.info(f"[SQS] Enqueuing crawl task {task_id}")
        
        try:
            # Set status to running in DB
            print("Getting task from memory or database...")
            task = self.tasks.get(task_id)
            if not task:
                print("Task not found in memory, checking database...")
                task_data = await self.db.get_collection("tasks").find_one({"task_id": task_id})
                if task_data:
                    task = CrawlTask(**task_data)
                    self.tasks[task_id] = task
                    print(f"Task {task_id} found in database")
                else:
                    error_msg = f"Task {task_id} not found in database"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    raise Exception(f"Task {task_id} not found")
            
            print(f"Current task status: {task.status}")
            if task.status != TaskStatus.PENDING:
                error_msg = f"Task {task_id} is not in pending status (current: {task.status})"
                logger.warning(error_msg)
                print(f"WARNING: {error_msg}")
                raise Exception(f"Task {task_id} is not in pending status")
            
            # Set to running
            print("Updating task status to RUNNING...")
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            try:
                await self.db.get_collection("tasks").update_one(
                    {"task_id": task_id},
                    {"$set": {"status": task.status.value, "started_at": task.started_at}}
                )
                print(f"Task {task_id} status updated to RUNNING in database")
            except Exception as e:
                error_msg = f"Failed to update task {task_id} status in database: {e}"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                raise
            
            # SQS removed - using direct Lambda invocation instead
            # Task will be processed directly by the crawler Lambda
            logger.info(f"Task {task_id} ready for direct processing")
            print(f"Task {task_id} ready for direct processing")
            
            return CrawlStatus(
                task_id=task_id,
                status=task.status.value,
                progress={"pages_crawled": 0, "documents_downloaded": 0},
                documents_downloaded=0,
                pages_crawled=0
            )
            
        except Exception as e:
            error_msg = f"Error starting crawl task {task_id}: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _run_crawl_task(self, task: CrawlTask):
        """Run the actual crawl task."""
        logger.info(f"Starting _run_crawl_task for task {task.task_id}")
        logger.info(f"Task URL: {task.url}")
        logger.info(f"Task config: max_pages={task.max_pages}, max_documents={task.max_documents}")
        
        try:
            # Create crawler configuration
            logger.info("Creating crawler configuration")
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
            logger.info(f"Crawler config created: {crawler_config}")
            
            # Get ScrapingBee API key from environment or task
            api_key = task.proxy_api_key or os.getenv("SCRAPINGBEE_API_KEY") or ""
            if not api_key:
                logger.warning("No ScrapingBee API key found. Crawling may fail without proxy support.")
            else:
                logger.info("ScrapingBee API key found")
            
            # Initialize crawler
            logger.info("Initializing AdvancedCrawler")
            AdvancedCrawler = get_advanced_crawler()
            crawler = AdvancedCrawler(
                api_key=api_key
            )
            logger.info("AdvancedCrawler initialized successfully")
            
            # Start crawling
            logger.info(f"Starting crawl for URL: {task.url}")
            results = crawler.crawl_url(
                url=task.url,
                render_js=getattr(task, 'render_js', True),
                block_ads=getattr(task, 'block_ads', False),
                block_resources=getattr(task, 'block_resources', True),
                wait=getattr(task, 'wait', None),
                wait_for=getattr(task, 'wait_for', None),
                wait_browser=getattr(task, 'wait_browser', None),
                window_width=getattr(task, 'window_width', 1920),
                window_height=getattr(task, 'window_height', 1080),
                premium_proxy=getattr(task, 'premium_proxy', False),
                country_code=getattr(task, 'country_code', 'in'),
                stealth_proxy=getattr(task, 'stealth_proxy', False),
                own_proxy=getattr(task, 'own_proxy', None),
                forward_headers=getattr(task, 'forward_headers', False),
                forward_headers_pure=getattr(task, 'forward_headers_pure', False),
                download_file=getattr(task, 'download_file', False),
                scraping_config=getattr(task, 'scraping_config', None)
            )
            logger.info(f"Crawl completed with results: {results}")
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Handle different result formats
            if results.get('success', False):
                # Lambda service format
                task.pages_crawled = 1  # Single URL crawl
                task.documents_downloaded = 1 if results.get('content') else 0
                task.downloaded_files = [task.url] if results.get('content') else []
                task.metadata = results
                
                # Save content to temporary file for S3 upload
                if results.get('content'):
                    import tempfile
                    from pathlib import Path
                    
                    # Create temporary file
                    temp_dir = "/tmp/crawled"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Create filename from URL
                    from urllib.parse import urlparse
                    parsed_url = urlparse(task.url)
                    domain = parsed_url.netloc
                    path = parsed_url.path.strip('/') or 'index'
                    filename = f"{domain}_{path.replace('/', '_')}.html"
                    
                    temp_file_path = os.path.join(temp_dir, filename)
                    
                    # Save content to file
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        f.write(results['content'])
                    
                    # Update task with local file path
                    task.downloaded_files = [temp_file_path]
                    task.output_dir = temp_dir
                    
                    logger.info(f"Saved crawled content to {temp_file_path}")
            else:
                # Handle failure
                task.status = TaskStatus.FAILED
                task.errors.append(results.get('error', 'Unknown error'))
                task.metadata = results
            
            logger.info(f"Task {task.task_id} completed: {task.documents_downloaded} documents, {task.pages_crawled} pages")
            
            # Only upload to S3 if crawl was successful (document processing happens during chat)
            if task.status == TaskStatus.COMPLETED and task.documents_downloaded > 0:
                # Upload crawled files to S3 for later processing
                await self._upload_crawled_files_to_s3(task)
                logger.info(f"Uploaded {task.documents_downloaded} documents to S3 for task {task.task_id}")
            else:
                logger.info(f"Skipping S3 upload for failed task {task.task_id}")
            
            # Save to database
            update_data = {
                "status": task.status.value,
                "completed_at": task.completed_at,
                "pages_crawled": task.pages_crawled,
                "documents_downloaded": task.documents_downloaded,
                "downloaded_files": task.downloaded_files,
                "s3_files": task.s3_files,
                "metadata": task.metadata
            }
            
            # Add errors if any
            if task.errors:
                update_data["errors"] = task.errors
            
            await self.db.get_collection("tasks").update_one(
                {"task_id": task.task_id},
                {"$set": update_data}
            )
            logger.info(f"Task {task.task_id} results saved to database")
            
            logger.info(f"Completed crawl task {task.task_id}: {task.documents_downloaded} documents")
            
        except Exception as e:
            logger.error(f"Crawl task {task.task_id} failed: {e}", exc_info=True)
            
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
            logger.info(f"Task {task.task_id} marked as FAILED in database")
        
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
                logger.info(f"Task {task.task_id} removed from active tasks")
    
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
        try:
            # Get task from database
            task = await self.get_task_status(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for cancellation")
                return False
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                logger.warning(f"Task {task_id} cannot be cancelled - status is {task.status}")
                return False
            
            # Cancel active task if it exists
            if task_id in self.active_tasks:
                self.active_tasks[task_id].cancel()
                del self.active_tasks[task_id]
                logger.info(f"Cancelled active task {task_id}")
            
            # Update task status to cancelled
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            # Save to database
            await self.db.get_collection("tasks").update_one(
                {"task_id": task_id},
                {"$set": {"status": task.status.value, "completed_at": task.completed_at}}
            )
            
            # Also update in-memory task if it exists
            if task_id in self.tasks:
                self.tasks[task_id] = task
            
            logger.info(f"Cancelled crawl task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling crawl task {task_id}: {e}")
            return False
    
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

    async def _upload_crawled_files_to_s3(self, task: CrawlTask):
        """Upload crawled files to S3."""
        try:
            import os
            from pathlib import Path
            
            output_dir = task.output_dir
            logger.info(f"Uploading crawled files from {output_dir} to S3")
            
            if not os.path.exists(output_dir):
                logger.warning(f"Output directory {output_dir} does not exist")
                return
            
            # Find all files in the output directory
            uploaded_files = []
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create filename based on file path
                        relative_path = os.path.relpath(file_path, output_dir)
                        # Don't add .html if the file already has an extension
                        if '.' in relative_path.split('/')[-1]:
                            filename = relative_path.replace('/', '_')
                        else:
                            filename = f"{relative_path.replace('/', '_')}.html"
                        
                        logger.info(f"Uploading {file_path} to S3 as: {filename}")
                        
                        # Upload using unified storage service
                        result = await unified_storage_service.upload_crawled_content(
                            content=content,
                            filename=filename,
                            task_id=task.task_id,
                            user_id=task.user_id,
                            metadata={
                                "original_path": relative_path,
                                "source_url": task.url
                            }
                        )
                        
                        uploaded_files.append(result["s3_key"])
                        logger.info(f"Successfully uploaded: {result['s3_key']}")
                            
                    except Exception as e:
                        logger.error(f"Error uploading {file_path}: {e}")
            
            # Update task with S3 file paths
            if uploaded_files:
                task.s3_files = uploaded_files
                logger.info(f"Uploaded {len(uploaded_files)} files to S3 for task {task.task_id}")
            else:
                logger.warning(f"No files were uploaded to S3 for task {task.task_id}")
                
        except Exception as e:
            logger.error(f"Error uploading crawled files to S3: {e}")

    async def _process_crawled_documents(self, task: CrawlTask):
        """Process crawled documents for chat (Textract, chunking, vector embedding)."""
        try:
            logger.info(f"Processing {len(task.s3_files) if task.s3_files else 0} crawled documents for task {task.task_id}")
            
            if not task.s3_files:
                logger.warning(f"No S3 files to process for task {task.task_id}")
                return
            
            # Import unified document processor
            try:
                from common.src.services.unified_document_processor import unified_document_processor
                
                processed_count = 0
                
                for s3_file_path in task.s3_files:
                    try:
                        logger.info(f"Processing document: {s3_file_path}")
                        
                        # Get document content from S3
                        storage_service = get_storage_service()
                        content = await storage_service.get_file_content(s3_file_path)
                        
                        if content:
                            # Decode content
                            if isinstance(content, bytes):
                                content = content.decode('utf-8', errors='ignore')
                            
                            # Clean HTML content if needed
                            filename = Path(s3_file_path).name
                            if filename.endswith('.html'):
                                import re
                                content = re.sub(r'<[^>]+>', '', content)
                                content = re.sub(r'\s+', ' ', content).strip()
                            
                            # Process crawled content using unified processor
                            result = await unified_document_processor.process_crawled_content(
                                content=content,
                                filename=filename,
                                user_id=task.user_id,
                                metadata={
                                    "source_url": task.url,
                                    "crawl_task_id": task.task_id,
                                    "crawled_at": task.completed_at.isoformat() if task.completed_at else None,
                                    "s3_key": s3_file_path
                                }
                            )
                            
                            if result.get("status") == "success":
                                processed_count += 1
                                logger.info(f"Successfully processed document: {result.get('document_id')}")
                            else:
                                logger.error(f"Failed to process document: {filename}")
                        else:
                            logger.warning(f"Could not read content for {s3_file_path}")
                            
                    except Exception as e:
                        logger.error(f"Error processing document {s3_file_path}: {e}")
                        continue
                
                logger.info(f"Processed {processed_count}/{len(task.s3_files)} documents for task {task.task_id}")
                
            except ImportError as e:
                logger.warning(f"Unified document processor not available: {e}")
                logger.warning("Documents will not be processed for chat functionality")
                
        except Exception as e:
            logger.error(f"Error processing crawled documents for task {task.task_id}: {e}")
            task.errors.append(f"Document processing failed: {str(e)}")

# Global crawler service instance
crawler_service = CrawlerService() 