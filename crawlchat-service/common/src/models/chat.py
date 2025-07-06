"""
Chat models for Stock Market Crawler.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    session_id: Optional[str] = Field(None, description="Session ID")


class ChatSession(BaseModel):
    """Chat session model."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Session last update timestamp")
    messages: List[ChatMessage] = Field(default=[], description="Session messages")
    document_count: int = Field(default=0, description="Number of documents in session")
    crawl_tasks: List[str] = Field(default=[], description="List of associated crawl task IDs")
    uploaded_documents: List[str] = Field(default=[], description="List of associated uploaded document IDs")


class ChatHistory(BaseModel):
    """Chat history model - represents user conversation history."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Session last update timestamp")
    messages: List[ChatMessage] = Field(default=[], description="Session messages")
    document_count: int = Field(default=0, description="Number of documents in session")
    crawl_tasks: List[str] = Field(default=[], description="List of associated crawl task IDs")
    uploaded_documents: List[str] = Field(default=[], description="List of associated uploaded document IDs")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SessionList(BaseModel):
    """Session list response model."""
    sessions: List[ChatSession] = Field(..., description="List of chat sessions")


class SessionCreate(BaseModel):
    """Session creation request model."""
    user_id: str = Field(..., description="User ID")


class SessionCreateResponse(BaseModel):
    """Session creation response model."""
    session_id: str = Field(..., description="Created session ID")
    created_at: datetime = Field(..., description="Session creation timestamp")


class MessageCreate(BaseModel):
    """Message creation request model."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Message timestamp")


class MessageResponse(BaseModel):
    """Message response model."""
    session_id: str = Field(..., description="Session ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp") 