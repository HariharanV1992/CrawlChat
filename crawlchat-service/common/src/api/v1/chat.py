"""
Chat API endpoints for Stock Market Crawler.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from common.src.models.chat import (
    ChatSession, ChatMessage, SessionCreate, SessionCreateResponse, 
    SessionList, MessageCreate, MessageResponse, ChatRequest, ChatResponse, ChatHistory
)
from common.src.services.chat_service import chat_service
from common.src.api.dependencies import get_current_user
from common.src.models.auth import UserResponse
from common.src.services.aws_background_service import aws_background_service
from common.src.services.document_service import document_service
from common.src.services.storage_service import get_storage_service
from common.src.core.exceptions import ChatError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

class CrawlDocumentsRequest(BaseModel):
    crawl_task_id: str

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    file_size: int

@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(current_user: UserResponse = Depends(get_current_user)):
    """Create a new chat session."""
    logger.info(f"[API] Creating chat session for user: {current_user.user_id}")
    try:
        response = await chat_service.create_session(current_user.user_id)
        logger.info(f"[API] Created chat session: {response.session_id} for user: {current_user.user_id}")
        return response
    except Exception as e:
        logger.error(f"[API] Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions(current_user: UserResponse = Depends(get_current_user)):
    """List all chat sessions for the current user."""
    try:
        return await chat_service.list_user_sessions(current_user.user_id)
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list chat sessions")

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific chat session."""
    try:
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat session")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a chat session."""
    try:
        success = await chat_service.delete_session(session_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    message: MessageCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a message in a chat session."""
    try:
        # Add user message
        await chat_service.add_message(
            session_id, 
            current_user.user_id, 
            message.role, 
            message.content
        )
        
        # Process AI response if it's a user message
        ai_response = None
        if message.role.value == "user":
            ai_response = await chat_service.process_ai_response(
                session_id, 
                current_user.user_id, 
                message.content
            )
        
        return MessageResponse(
            session_id=session_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_messages(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all messages in a chat session."""
    try:
        # Get messages first
        messages = await chat_service.get_session_messages(session_id, current_user.user_id)
        
        # Check for missing completion message and add it if needed
        # This helps ensure completion messages appear even if they were missed due to Lambda timing
        await chat_service.check_and_add_missing_completion_message(session_id, current_user.user_id)
        
        # Get updated messages after potential completion message addition
        updated_messages = await chat_service.get_session_messages(session_id, current_user.user_id)
        
        return updated_messages
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

@router.post("/sessions/{session_id}/crawl-documents")
async def link_crawl_documents(
    session_id: str,
    request: CrawlDocumentsRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Link crawled documents to a chat session."""
    logger.info(f"[API] Linking crawl documents for session: {session_id}, user: {current_user.user_id}, crawl_task_id: {request.crawl_task_id}")
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get documents for this crawl task from MongoDB
        documents = await document_service.get_task_documents(request.crawl_task_id)
        
        if not documents:
            raise HTTPException(
                status_code=404, 
                detail=f"No documents found for crawl task {request.crawl_task_id}"
            )
        
        # Link documents to the chat session
        linked_documents = await chat_service.link_crawl_documents(
            session_id, 
            current_user.user_id, 
            request.crawl_task_id, 
            documents
        )
        
        logger.info(f"[API] Linked crawl documents for session: {session_id}, result: {len(linked_documents)}")
        return {
            "message": f"Successfully linked {len(linked_documents)} documents from crawl task",
            "session_id": session_id,
            "crawl_task_id": request.crawl_task_id,
            "crawl_documents": [doc.file_path for doc in linked_documents],
            "total_documents": len(linked_documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error linking crawl documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions")
async def clear_all_sessions(current_user: UserResponse = Depends(get_current_user)):
    """Clear all chat sessions for the current user."""
    try:
        deleted_count = await chat_service.clear_user_sessions(current_user.user_id)
        return {"message": f"Deleted {deleted_count} sessions"}
    except Exception as e:
        logger.error(f"Error clearing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear sessions")

@router.post("/sessions/{session_id}/chat")
async def chat_with_session(
    session_id: str,
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a message and get AI response in a chat session."""
    logger.info(f"[API] Chat request for session: {session_id}, user: {current_user.user_id}, message: {request.message}")
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Process AI response (this will add both user message and AI response)
        ai_response = await chat_service.process_ai_response(
            session_id, 
            current_user.user_id, 
            request.message
        )
        
        logger.info(f"[API] Chat completed for session: {session_id}")
        return {
            "session_id": session_id,
            "user_message": request.message,
            "response": ai_response,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document to a chat session."""
    logger.info(f"[API] Uploading document to session: {session_id}, user: {current_user.user_id}, filename: {file.filename}")
    
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.html']
        file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")
        
        # Upload to S3 (using IAM role)
        storage_service = get_storage_service()
        
        # Generate unique filename
        import uuid
        import os
        from datetime import datetime
        
        timestamp = int(datetime.now().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        file_extension = os.path.splitext(file.filename)[1]
        s3_filename = f"uploaded_documents/{current_user.user_id}/{timestamp}_{unique_id}{file_extension}"
        
        # Upload to S3 using IAM role
        s3_key = await storage_service.upload_file_from_bytes(
            file_content, 
            s3_filename, 
            content_type=file.content_type
        )
        
        # Debug logging to see what's being returned
        logger.info(f"[DEBUG] API received s3_key: {s3_key}")
        logger.info(f"[DEBUG] s3_key type: {type(s3_key)}")
        
        # Save document record to database
        from common.src.models.documents import Document, DocumentType, DocumentStatus
        
        document = Document(
            document_id=str(uuid.uuid4()),
            filename=file.filename,
            file_path=s3_key,
            file_size=file_size,
            document_type=DocumentType.PDF,
            status=DocumentStatus.UPLOADED,
            user_id=current_user.user_id
        )
        
        created_document = await document_service.create_document(document)
        
        # Link the uploaded document to the chat session
        await chat_service.link_uploaded_document(
            session_id,
            current_user.user_id,
            created_document
        )
        
        # Note: System message will be added by link_uploaded_document method
        
        logger.info(f"[API] Document uploaded successfully: {created_document.document_id}")
        
        return DocumentUploadResponse(
            message="Document uploaded successfully",
            document_id=created_document.document_id,
            filename=file.filename,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get cache statistics for monitoring performance."""
    try:
        # Cache service removed for AWS deployment
        return {
            "cache_stats": {
                "status": "disabled",
                "message": "Cache service removed for AWS deployment"
            },
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@router.post("/cache/clear")
async def clear_cache(current_user: UserResponse = Depends(get_current_user)):
    """Clear all cache entries."""
    try:
        # Cache service removed for AWS deployment
        return {
            "message": "Cache cleared successfully",
            "note": "Cache service removed for AWS deployment"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/background/tasks/{task_id}")
async def get_background_task_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get status of a background task."""
    try:
        # Background service removed for AWS deployment
        return {
            "task_id": task_id,
            "status": "unknown",
            "message": "Background service removed for AWS deployment"
        }
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

@router.get("/sessions/{session_id}/processing-status")
async def get_processing_status(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check the processing status of documents in a session."""
    try:
        status_info = await chat_service.check_processing_status(session_id, current_user.user_id)
        return status_info
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")

@router.post("/sessions/{session_id}/check-completion")
async def check_completion_message(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check for missing completion message and add it if needed."""
    try:
        success = await chat_service.check_and_add_missing_completion_message(session_id, current_user.user_id)
        if success:
            return {"message": "Completion message checked and added if needed"}
        else:
            return {"message": "No completion message needed or could not be added"}
    except Exception as e:
        logger.error(f"Error checking completion message: {e}")
        raise HTTPException(status_code=500, detail="Failed to check completion message")

@router.post("/sessions/{session_id}/force-completion")
async def force_completion_message(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Force add a completion message if processing is done but message is missing."""
    try:
        success = await chat_service.force_completion_message(session_id, current_user.user_id)
        if success:
            return {"message": "Completion message added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add completion message")
    except Exception as e:
        logger.error(f"Error forcing completion message: {e}")
        raise HTTPException(status_code=500, detail="Failed to force completion message") 