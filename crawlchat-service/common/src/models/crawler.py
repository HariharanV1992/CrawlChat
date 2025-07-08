"""
Crawler models for Stock Market Crawler.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlRequest(BaseModel):
    """Crawl request model."""
    url: HttpUrl = Field(..., description="Target URL to crawl")
    max_documents: int = Field(default=5, ge=1, le=100, description="Maximum documents to download")
    max_pages: int = Field(default=50, ge=1, le=1000, description="Maximum pages to crawl")
    max_workers: int = Field(default=3, ge=1, le=50, description="Maximum concurrent workers")
    delay: float = Field(default=0.05, ge=0, le=10, description="Delay between requests in seconds")
    total_timeout: int = Field(default=1800, ge=60, le=7200, description="Total timeout in seconds")
    page_timeout: int = Field(default=60, ge=10, le=300, description="Page timeout in seconds")
    request_timeout: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")


class CrawlTask(BaseModel):
    """Crawl task model."""
    task_id: str = Field(..., description="Unique task ID")
    user_id: str = Field(..., description="User ID")
    url: str = Field(..., description="Target URL")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Task update timestamp")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    
    # Configuration
    max_documents: int = Field(..., description="Maximum documents to download")
    max_pages: int = Field(..., description="Maximum pages to crawl")
    max_workers: int = Field(..., description="Maximum concurrent workers")
    
    # Timeout settings
    timeout: int = Field(default=30, description="General timeout in seconds")
    total_timeout: int = Field(default=1800, description="Total timeout in seconds")
    page_timeout: int = Field(default=60, description="Page timeout in seconds")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    connection_limit: int = Field(default=100, description="Connection limit")
    tcp_connector_limit: int = Field(default=100, description="TCP connector limit")
    keepalive_timeout: int = Field(default=30, description="Keepalive timeout in seconds")
    
    # Crawler settings
    delay: float = Field(default=0.05, description="Delay between requests in seconds")
    min_file_size: int = Field(default=1024, description="Minimum file size in bytes")
    output_dir: str = Field(default="/tmp/data/crawled", description="Output directory")
    use_proxy: bool = Field(default=False, description="Use proxy")
    proxy_api_key: Optional[str] = Field(None, description="Proxy API key")
    proxy_method: str = Field(default="http", description="Proxy method")
    country_code: str = Field(default="us", description="Country code")
    premium: bool = Field(default=False, description="Use premium proxy")
    bypass: bool = Field(default=False, description="Bypass proxy")
    render: bool = Field(default=False, description="Render JavaScript")
    retry: int = Field(default=3, description="Number of retries")
    session_number: int = Field(default=0, description="Session number")
    enable_compression: bool = Field(default=True, description="Enable compression")
    max_pages_without_documents: int = Field(default=10, description="Max pages without documents")
    
    # Progress
    pages_crawled: int = Field(default=0, description="Number of pages crawled")
    documents_downloaded: int = Field(default=0, description="Number of documents downloaded")
    errors: List[str] = Field(default=[], description="List of errors encountered")
    
    # Results
    downloaded_files: List[str] = Field(default=[], description="List of downloaded file paths")
    s3_files: List[str] = Field(default=[], description="List of S3 file paths")
    metadata: Dict[str, Any] = Field(default={}, description="Task metadata")


class CrawlResponse(BaseModel):
    """Crawl response model."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Response message")
    url: str = Field(..., description="Target URL")
    max_documents: int = Field(..., description="Maximum documents to download")
    created_at: datetime = Field(..., description="Task creation timestamp")


class CrawlStatus(BaseModel):
    """Crawl status model."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Dict[str, Any] = Field(..., description="Progress information")
    documents_downloaded: int = Field(..., description="Documents downloaded")
    pages_crawled: int = Field(..., description="Pages crawled")
    error_message: Optional[str] = Field(None, description="Error message if any")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class TaskResponse(BaseModel):
    """Task response model."""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    message: str = Field(..., description="Response message")


class TaskList(BaseModel):
    """Task list response model."""
    tasks: List[CrawlTask] = Field(..., description="List of crawl tasks")


class TaskProgress(BaseModel):
    """Task progress model."""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    pages_crawled: int = Field(..., description="Pages crawled")
    documents_downloaded: int = Field(..., description="Documents downloaded")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining in seconds")


class CrawlResult(BaseModel):
    """Crawl result model."""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Final status")
    total_pages: int = Field(..., description="Total pages crawled")
    total_documents: int = Field(..., description="Total documents downloaded")
    errors: List[str] = Field(default=[], description="List of errors")
    files: List[str] = Field(default=[], description="List of downloaded files")
    completed_at: datetime = Field(..., description="Completion timestamp")


class CrawlConfig(BaseModel):
    """Crawl configuration model."""
    max_documents: int = Field(default=5, ge=1, le=100, description="Maximum documents to download")
    max_pages: int = Field(default=50, ge=1, le=1000, description="Maximum pages to crawl")
    max_workers: int = Field(default=3, ge=1, le=50, description="Maximum concurrent workers")
    delay: float = Field(default=0.05, ge=0, le=10, description="Delay between requests in seconds")
    total_timeout: int = Field(default=1800, ge=60, le=7200, description="Total timeout in seconds")
    page_timeout: int = Field(default=60, ge=10, le=300, description="Page timeout in seconds")
    request_timeout: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")
    use_proxy: bool = Field(default=False, description="Use proxy")
    proxy_api_key: Optional[str] = Field(None, description="Proxy API key")
    render: bool = Field(default=False, description="Render JavaScript")
    retry: int = Field(default=3, description="Number of retries")


class CrawlTaskCreate(BaseModel):
    """Crawl task creation model."""
    url: HttpUrl = Field(..., description="Target URL to crawl")
    max_documents: int = Field(default=5, ge=1, le=100, description="Maximum documents to download")
    max_pages: int = Field(default=50, ge=1, le=1000, description="Maximum pages to crawl")
    max_workers: int = Field(default=3, ge=1, le=50, description="Maximum concurrent workers")
    delay: float = Field(default=0.05, ge=0, le=10, description="Delay between requests in seconds")
    total_timeout: int = Field(default=1800, ge=60, le=7200, description="Total timeout in seconds")
    page_timeout: int = Field(default=60, ge=10, le=300, description="Page timeout in seconds")
    request_timeout: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")


class CrawlTaskUpdate(BaseModel):
    """Crawl task update model."""
    status: Optional[TaskStatus] = Field(None, description="Task status")
    max_documents: Optional[int] = Field(None, ge=1, le=100, description="Maximum documents to download")
    max_pages: Optional[int] = Field(None, ge=1, le=1000, description="Maximum pages to crawl")
    max_workers: Optional[int] = Field(None, ge=1, le=50, description="Maximum concurrent workers")
    delay: Optional[float] = Field(None, ge=0, le=10, description="Delay between requests in seconds")


class CrawlTaskResponse(BaseModel):
    """Crawl task response model."""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    message: str = Field(..., description="Response message")
    url: str = Field(..., description="Target URL")
    max_documents: int = Field(..., description="Maximum documents to download")
    created_at: datetime = Field(..., description="Task creation timestamp")


class CrawlTaskListResponse(BaseModel):
    """Crawl task list response model."""
    tasks: List[CrawlTask] = Field(..., description="List of crawl tasks")
    total_count: int = Field(..., description="Total number of tasks") 