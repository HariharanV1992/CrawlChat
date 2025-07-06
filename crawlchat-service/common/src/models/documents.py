"""
Document models for Stock Market Crawler.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    PDF = "pdf"
    HTML = "html"
    TXT = "txt"
    DOC = "doc"
    DOCX = "docx"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    PPT = "ppt"
    PPTX = "pptx"
    JSON = "json"


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(BaseModel):
    """Document model."""
    document_id: str = Field(..., description="Unique document ID")
    user_id: str = Field(..., description="User ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File path on disk")
    file_size: int = Field(..., description="File size in bytes")
    document_type: DocumentType = Field(..., description="Document type")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Document status")
    
    # Metadata
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    
    # Processing results
    content: Optional[str] = Field(None, description="Extracted content")
    summary: Optional[str] = Field(None, description="Document summary")
    key_points: List[str] = Field(default=[], description="Key points extracted")
    metadata: Dict[str, Any] = Field(default={}, description="Document metadata")
    
    # Task association
    task_id: Optional[str] = Field(None, description="Associated crawl task ID")
    crawl_task_id: Optional[str] = Field(None, description="Crawl task ID for crawl documents")


class DocumentUpload(BaseModel):
    """Document upload request model."""
    filename: str = Field(..., description="Original filename")
    content: bytes = Field(..., description="File content")
    user_id: str = Field(..., description="User ID")
    task_id: Optional[str] = Field(None, description="Associated task ID")


class DocumentProcess(BaseModel):
    """Document processing request model."""
    document_path: str = Field(..., description="Document file path")
    user_query: Optional[str] = Field(None, description="User query for processing")


class DocumentProcessResponse(BaseModel):
    """Document processing response model."""
    document_id: str = Field(..., description="Document ID")
    status: DocumentStatus = Field(..., description="Processing status")
    content: Optional[str] = Field(None, description="Extracted content")
    summary: Optional[str] = Field(None, description="Document summary")
    key_points: List[str] = Field(default=[], description="Key points")
    processing_time: float = Field(..., description="Processing time in seconds")


class DocumentList(BaseModel):
    """Document list response model."""
    documents: List[Document] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents")


class DocumentQuery(BaseModel):
    """Document query model."""
    query: str = Field(..., description="Search query")
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")


class DocumentSearchResult(BaseModel):
    """Document search result model."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    relevance_score: float = Field(..., description="Relevance score")
    matched_content: str = Field(..., description="Matched content snippet")
    document_type: DocumentType = Field(..., description="Document type")


class DocumentCreate(BaseModel):
    """Document creation model."""
    filename: str = Field(..., description="Original filename")
    content: bytes = Field(..., description="File content")
    user_id: str = Field(..., description="User ID")
    task_id: Optional[str] = Field(None, description="Associated task ID")


class DocumentUpdate(BaseModel):
    """Document update model."""
    document_id: str = Field(..., description="Document ID")
    user_query: Optional[str] = Field(None, description="User query for processing")


class DocumentResponse(BaseModel):
    """Document response model."""
    document_id: str = Field(..., description="Document ID")
    status: DocumentStatus = Field(..., description="Processing status")
    content: Optional[str] = Field(None, description="Extracted content")
    summary: Optional[str] = Field(None, description="Document summary")
    key_points: List[str] = Field(default=[], description="Key points")
    processing_time: float = Field(..., description="Processing time in seconds")


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[Document] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents") 