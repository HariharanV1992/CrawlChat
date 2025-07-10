"""
Crawler data models for CrawlChat API.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a crawl task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlStatus(str, Enum):
    """Status of a crawl operation."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class CrawlConfig(BaseModel):
    """Configuration for a crawl operation."""
    max_doc_count: Optional[int] = Field(default=1, description="Maximum number of documents to extract")
    content_type: str = Field(default="generic", description="Type of content to crawl")
    use_js_scenario: bool = Field(default=False, description="Whether to use JavaScript scenario")
    take_screenshot: bool = Field(default=False, description="Whether to take screenshot")
    download_file: bool = Field(default=False, description="Whether to download file")
    country_code: str = Field(default="in", description="Country code for proxy")
    force_mode: Optional[str] = Field(default=None, description="Force specific proxy mode")


class CrawlRequest(BaseModel):
    """Request for a crawl operation."""
    url: str = Field(..., description="URL to crawl")
    config: Optional[CrawlConfig] = Field(default=None, description="Crawl configuration")
    user_id: Optional[str] = Field(default=None, description="User ID requesting the crawl")


class CrawlResult(BaseModel):
    """Result of a crawl operation."""
    success: bool = Field(..., description="Whether the crawl was successful")
    url: str = Field(..., description="URL that was crawled")
    content: Optional[str] = Field(default=None, description="Crawled content")
    content_length: Optional[int] = Field(default=None, description="Length of content")
    crawl_time: Optional[float] = Field(default=None, description="Time taken to crawl")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    headers: Optional[Dict[str, Any]] = Field(default=None, description="Response headers")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CrawlResponse(BaseModel):
    """Response from a crawl operation."""
    success: bool = Field(..., description="Whether the operation was successful")
    task_id: Optional[str] = Field(default=None, description="Task ID if async")
    result: Optional[CrawlResult] = Field(default=None, description="Crawl result")
    usage_stats: Optional[Dict[str, Any]] = Field(default=None, description="Usage statistics")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CrawlTask(BaseModel):
    """A crawl task."""
    id: str = Field(..., description="Unique task ID")
    url: str = Field(..., description="URL to crawl")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    config: Optional[CrawlConfig] = Field(default=None, description="Crawl configuration")
    user_id: Optional[str] = Field(default=None, description="User ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    result: Optional[CrawlResult] = Field(default=None, description="Crawl result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    documents_found: int = Field(default=0, description="Number of documents found")
    total_pages: int = Field(default=0, description="Total pages crawled")
    total_documents: int = Field(default=0, description="Total documents extracted")


class CrawlTaskCreate(BaseModel):
    """Request to create a crawl task."""
    url: str = Field(..., description="URL to crawl")
    config: Optional[CrawlConfig] = Field(default=None, description="Crawl configuration")
    user_id: Optional[str] = Field(default=None, description="User ID")


class CrawlTaskUpdate(BaseModel):
    """Request to update a crawl task."""
    status: Optional[TaskStatus] = Field(default=None, description="New status")
    result: Optional[CrawlResult] = Field(default=None, description="Crawl result")
    error: Optional[str] = Field(default=None, description="Error message")
    documents_found: Optional[int] = Field(default=None, description="Number of documents found")
    total_pages: Optional[int] = Field(default=None, description="Total pages crawled")
    total_documents: Optional[int] = Field(default=None, description="Total documents extracted")


class CrawlTaskList(BaseModel):
    """List of crawl tasks."""
    tasks: List[CrawlTask] = Field(default_factory=list, description="List of tasks")
    total: int = Field(default=0, description="Total number of tasks")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=10, description="Tasks per page") 