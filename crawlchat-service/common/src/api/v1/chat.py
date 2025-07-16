"""
Chat API endpoints for Stock Market Crawler.
"""

import logging
import uuid
import hashlib
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from common.src.models.chat import (
    ChatSession, ChatMessage, SessionCreate, SessionCreateResponse, 
    SessionList, MessageCreate, MessageResponse, ChatRequest, ChatResponse, ChatHistory
)
from common.src.models.documents import DocumentUpload
from common.src.services.chat_service import chat_service
from common.src.api.dependencies import get_current_user
from common.src.models.auth import UserResponse
from common.src.services.aws_background_service import aws_background_service
from common.src.services.document_service import document_service

from common.src.services.document_processing_service import document_processing_service
from common.src.core.exceptions import ChatError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

class CrawlDocumentsRequest(BaseModel):
    crawl_task_id: str

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    content_length: int
    extraction_method: str
    s3_key: str
    processing_status: str

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

@router.post("/start", response_model=SessionCreateResponse)
async def start_chat_session(
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Start a new chat session (compatibility endpoint)."""
    logger.info(f"[API] Starting chat session for user: {current_user.user_id}")
    try:
        response = await chat_service.create_session(current_user.user_id)
        logger.info(f"[API] Started chat session: {response.session_id} for user: {current_user.user_id}")
        return response
    except Exception as e:
        logger.error(f"[API] Error starting chat session: {e}")
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

@router.post("/message", response_model=MessageResponse)
async def send_message_compatibility(
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a message (compatibility endpoint)."""
    try:
        session_id = request.get("session_id")
        message_content = request.get("message", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Create message object
        from common.src.models.chat import MessageRole
        message = MessageCreate(
            role=MessageRole.USER,
            content=message_content
        )
        
        # Add user message
        await chat_service.add_message(
            session_id, 
            current_user.user_id, 
            message.role, 
            message.content
        )
        
        # Process AI response
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
    """Upload a document to a chat session with AWS Textract processing."""
    logger.info(f"[API] Uploading document to session: {session_id}, user: {current_user.user_id}, filename: {file.filename}")
    
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.html', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content with enhanced validation - READ ONLY ONCE
        file_content = await file.read()
        file_size = len(file_content)
        
        # 🔍 CRITICAL: Enhanced file content validation
        logger.info(f"[API] === FILE CONTENT VALIDATION ===")
        logger.info(f"[API] File size: {file_size:,} bytes")
        logger.info(f"[API] File content type: {type(file_content)}")
        logger.info(f"[API] File content is None: {file_content is None}")
        logger.info(f"[API] File content is empty: {not file_content}")
        
        if file_content:
            logger.info(f"[API] File MD5: {hashlib.md5(file_content).hexdigest()}")
            logger.info(f"[API] First 50 bytes: {file_content[:50].hex()}")
            logger.info(f"[API] Last 50 bytes: {file_content[-50:].hex()}")
            
            # Enhanced PDF validation
            if file.filename.lower().endswith('.pdf'):
                logger.info(f"[API] PDF file detected - performing enhanced validation")
                logger.info(f"[API] PDF header check: {file_content.startswith(b'%PDF')}")
                logger.info(f"[API] PDF EOF check: {b'%%EOF' in file_content}")
                logger.info(f"[API] PDF size: {len(file_content):,} bytes")
                
                if not file_content.startswith(b'%PDF'):
                    logger.error(f"[API] ❌ Invalid PDF header: {file_content[:20]}")
                    raise HTTPException(status_code=400, detail="Invalid PDF file - missing PDF header")
                
                if b'%%EOF' not in file_content[-1000:]:
                    logger.warning(f"[API] ⚠️ PDF EOF marker not found in last 1000 bytes")
                    # Don't fail for missing EOF, but log it
                
                logger.info(f"[API] ✅ PDF validation passed")
        else:
            logger.error(f"[API] ❌ File content is empty or None")
            raise HTTPException(status_code=400, detail="File content is empty")
        
        # Check if file is empty
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Check file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")
        
        logger.info(f"[API] === FILE CONTENT VALIDATION COMPLETE ===")
        
        # Generate task ID for organization
        task_id = str(uuid.uuid4())
        
        # Test S3 connectivity before upload
        try:
            logger.info(f"[API] Testing S3 connectivity...")
            from common.src.core.aws_config import aws_config
            logger.info(f"[API] S3 Bucket: {aws_config.s3_bucket}")
            logger.info(f"[API] AWS Region: {aws_config.region}")
            
            # Test S3 access
            import boto3
            s3_test_client = boto3.client('s3', region_name=aws_config.region)
            s3_test_client.head_bucket(Bucket=aws_config.s3_bucket)
            logger.info(f"[API] S3 connectivity test passed")
        except Exception as s3_error:
            logger.error(f"[API] S3 connectivity test failed: {s3_error}")
            raise HTTPException(status_code=500, detail=f"S3 connectivity failed: {str(s3_error)}")
        
        # Upload to S3 using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.user_id,
            content_type=file.content_type,
            task_id=task_id
        )
        
        if result.get('status') != 'success':
            logger.error(f"[API] Upload failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.get('error')}")
        
        s3_key = result["s3_key"]
        upload_method = result.get("upload_method", "unknown")
        
        logger.info(f"[API] Document uploaded to S3: {s3_key}")
        logger.info(f"[API] Upload method used: {upload_method}")
        logger.info(f"[API] Upload verification included in service")
        
        # Create document record
        document_data = DocumentUpload(
            filename=file.filename,
            file_content=file_content,
            user_id=current_user.user_id,
            task_id=task_id
        )
        
        document = await document_service.upload_document(document_data)
        
        # Link the uploaded document to the chat session
        await chat_service.link_uploaded_document(
            session_id,
            current_user.user_id,
            document
        )
        
        # Process document with AWS Textract
        try:
            processing_result = await document_processing_service.process_document(
                file_content=file_content,
                filename=file.filename,
                user_id=current_user.user_id,
                session_id=session_id,
                document_id=document.document_id
            )
            
            logger.info(f"[API] Document processing completed: {processing_result}")
            
            return DocumentUploadResponse(
                message="Document uploaded and processed successfully",
                document_id=document.document_id,
                filename=file.filename,
                content_length=processing_result.get("content_length", 0),
                extraction_method=processing_result.get("extraction_method", "AWS Textract"),
                s3_key=s3_key,
                processing_status="completed"
            )
            
        except Exception as processing_error:
            logger.error(f"[API] Document processing failed: {processing_error}")
            # Still return success for upload, but note processing failed
            return DocumentUploadResponse(
                message="Document uploaded successfully but processing failed",
                document_id=document.document_id,
                filename=file.filename,
                content_length=0,
                extraction_method="none",
                s3_key=s3_key,
                processing_status="failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/sessions/{session_id}/documents/base64")
async def upload_document_base64(
    session_id: str,
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document via Base64-encoded content to a chat session with AWS Textract processing."""
    logger.info(f"[API] Uploading Base64 document to session: {session_id}, user: {current_user.user_id}")
    
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Extract data from request
        file_content_base64 = request.get("file_content")
        filename = request.get("filename")
        content_type = request.get("content_type")
        
        if not file_content_base64 or not filename:
            raise HTTPException(status_code=400, detail="Missing file_content or filename")
        
        # Decode Base64 content
        import base64
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid Base64 content: {str(e)}")
        
        file_size = len(file_content)
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.html', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        file_extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")
        
        # Generate task ID for organization
        task_id = str(uuid.uuid4())
        
        # Upload to S3 using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=filename,
            user_id=current_user.user_id,
            content_type=content_type,
            task_id=task_id
        )
        s3_key = result["s3_key"]
        
        logger.info(f"[API] Base64 document uploaded to S3: {s3_key}")
        
        # Process document with AWS Textract using unified document processor
        
        
        # Simple document processing without unified processor
        processing_result = {
            "status": "success",
            "document_id": document_id,
            "content_length": len(file_content),
            "extraction_method": "simple_text_extraction"
        }
        
        if processing_result.get("status") != "success":
            logger.error(f"[API] Base64 document processing failed: {processing_result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Document processing failed: {processing_result.get('error', 'Unknown error')}"
            )
        
        document_id = processing_result.get("document_id")
        content_length = processing_result.get("content_length", 0)
        extraction_method = processing_result.get("extraction_method", "unknown")
        
        logger.info(f"[API] Base64 document processed successfully: {document_id}, content length: {content_length}, method: {extraction_method}")
        
        # Get the document record that was already created by unified document processor
        from common.src.models.documents import Document, DocumentType, DocumentStatus
        
        # Fetch the existing document record from database
        from common.src.core.database import mongodb
        from datetime import datetime
        
        await mongodb.connect()
        doc_data = await mongodb.get_collection("documents").find_one({"document_id": document_id})
        
        if not doc_data:
            logger.error(f"[API] Base64 document record not found after processing: {document_id}")
            raise HTTPException(status_code=500, detail="Document record not found after processing")
        
        # Update the document record with additional metadata
        update_data = {
            "file_path": s3_key,
            "metadata.task_id": task_id,
            "metadata.extraction_method": extraction_method,
            "metadata.content_length": content_length,
            "metadata.vector_store_result": processing_result.get("vector_store_result"),
            "updated_at": datetime.utcnow()
        }
        
        await mongodb.get_collection("documents").update_one(
            {"document_id": document_id},
            {"$set": update_data}
        )
        
        # Create Document object for chat service
        document_data = {
            "document_id": doc_data.get("document_id"),
            "user_id": doc_data.get("user_id"),
            "filename": doc_data.get("filename"),
            "file_path": s3_key,  # Use the S3 key as file_path
            "file_size": doc_data.get("file_size", file_size),
            "document_type": doc_data.get("document_type", "pdf"),
            "status": doc_data.get("status", "processed"),  # Use processed status
            "uploaded_at": doc_data.get("uploaded_at", datetime.utcnow()),
            "processed_at": doc_data.get("processed_at", datetime.utcnow()),
            "content": doc_data.get("content"),
            "summary": doc_data.get("summary"),
            "key_points": doc_data.get("key_points", []),
            "metadata": doc_data.get("metadata", {}),
            "task_id": doc_data.get("task_id"),
            "crawl_task_id": doc_data.get("crawl_task_id")
        }
        
        # Update metadata with additional information
        document_data["metadata"].update({
            "task_id": task_id,
            "extraction_method": extraction_method,
            "content_length": content_length,
            "vector_store_result": processing_result.get("vector_store_result")
        })
        
        document = Document(**document_data)
        
        # Link the uploaded document to the chat session
        await chat_service.link_uploaded_document(
            session_id,
            current_user.user_id,
            document
        )
        
        logger.info(f"[API] Base64 document uploaded and processed successfully: {document.document_id}")
        
        return {
            "message": f"Document uploaded and processed successfully using {extraction_method}",
            "document_id": document.document_id,
            "filename": filename,
            "file_size": file_size,
            "extraction_method": extraction_method,
            "content_length": content_length
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error uploading Base64 document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.post("/sessions/{session_id}/documents/background")
async def upload_document_background(
    session_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document for background processing to avoid timeouts."""
    logger.info(f"[API] Background upload for document: {file.filename} to session: {session_id}")
    
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.html', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
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
        
        # Generate task ID for organization
        task_id = str(uuid.uuid4())
        
        # Upload to S3 using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.user_id,
            content_type=file.content_type,
            task_id=task_id
        )
        s3_key = result["s3_key"]
        
        logger.info(f"[API] Document uploaded to S3: {s3_key}")
        
        # Create a background task for processing
        from common.src.services.aws_background_service import aws_background_service
        
        background_task = await aws_background_service.create_document_processing_task(
            task_id=task_id,
            session_id=session_id,
            user_id=current_user.user_id,
            filename=file.filename,
            s3_key=s3_key,
            file_size=file_size,
            content_type=file.content_type
        )
        
        return {
            "message": f"Document uploaded successfully. Processing started in background.",
            "task_id": task_id,
            "background_task_id": background_task.get("task_id"),
            "status": "processing",  # This is a response status, not a document status
            "filename": file.filename,
            "file_size": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error in background document upload: {e}")
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
    """Force add a completion message to a session."""
    try:
        await chat_service.force_add_completion_message(session_id, current_user.user_id)
        return {"message": "Completion message added successfully"}
    except Exception as e:
        logger.error(f"Error forcing completion message: {e}")
        raise HTTPException(status_code=500, detail="Failed to add completion message")

@router.get("/sessions/{session_id}/documents/{document_id}/vector-status")
async def check_document_vector_status(
    session_id: str,
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check the vector store processing status for a specific document."""
    try:
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get document from database
        from common.src.core.database import mongodb
        await mongodb.connect()
        
        doc_data = await mongodb.get_collection("documents").find_one({
            "document_id": document_id,
            "user_id": current_user.user_id
        })
        
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check vector store status
        vector_result = doc_data.get("metadata", {}).get("vector_store_result", {})
        file_id = vector_result.get("vector_store_file_id")
        
        if not file_id:
            return {
                "document_id": document_id,
                "vector_status": "not_uploaded",
                "message": "Document not uploaded to vector store"
            }
        
        # Check current status from vector store
        from common.src.services.vector_store_service import vector_store_service
        status_check = await vector_store_service.check_file_upload_status(
            file_id, 
            vector_result.get("vector_store_id")
        )
        
        return {
            "document_id": document_id,
            "vector_status": status_check.get("status", "unknown"),
            "file_id": file_id,
            "error": status_check.get("error"),
            "usage": status_check.get("usage"),
            "message": f"Vector store status: {status_check.get('status', 'unknown')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking vector status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check vector status") 

@router.get("/test-s3")
async def test_s3_connectivity(current_user: UserResponse = Depends(get_current_user)):
    """Test S3 connectivity and permissions."""
    try:
        logger.info(f"[API] Testing S3 connectivity for user: {current_user.user_id}")
        
        import boto3
        from datetime import datetime
        from common.src.core.aws_config import aws_config
        
        # Test basic connectivity
        s3_client = boto3.client('s3', region_name=aws_config.region)
        
        # Test bucket access
        bucket_info = s3_client.head_bucket(Bucket=aws_config.s3_bucket)
        logger.info(f"[API] S3 bucket access test passed: {aws_config.s3_bucket}")
        
        # Test write permissions with a small test file
        test_key = f"test_uploads/{current_user.user_id}/test_{int(datetime.utcnow().timestamp())}.txt"
        test_content = b"Test file content for S3 connectivity verification"
        
        upload_response = s3_client.put_object(
            Bucket=aws_config.s3_bucket,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        logger.info(f"[API] S3 write test passed: {test_key}")
        
        # Test read permissions
        download_response = s3_client.get_object(Bucket=aws_config.s3_bucket, Key=test_key)
        downloaded_content = download_response['Body'].read()
        logger.info(f"[API] S3 read test passed: {len(downloaded_content)} bytes")
        
        # Clean up test file
        s3_client.delete_object(Bucket=aws_config.s3_bucket, Key=test_key)
        logger.info(f"[API] S3 cleanup test passed")
        
        return {
            "status": "success",
            "message": "S3 connectivity and permissions test passed",
            "bucket": aws_config.s3_bucket,
            "region": aws_config.region,
            "user_id": current_user.user_id,
            "tests": {
                "bucket_access": "passed",
                "write_permissions": "passed",
                "read_permissions": "passed",
                "cleanup_permissions": "passed"
            }
        }
        
    except Exception as e:
        logger.error(f"[API] S3 connectivity test failed: {e}")
        return {
            "status": "error",
            "message": f"S3 connectivity test failed: {str(e)}",
            "bucket": aws_config.s3_bucket,
            "region": aws_config.region,
            "user_id": current_user.user_id,
            "error": str(e)
        } 

@router.post("/test-simple-upload")
async def test_simple_upload(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Test simple upload without processing - for debugging PDF upload issues."""
    logger.info(f"[API_DEBUG] === SIMPLE UPLOAD TEST START ===")
    logger.info(f"[API_DEBUG] File: {file.filename}")
    logger.info(f"[API_DEBUG] Content type: {file.content_type}")
    logger.info(f"[API_DEBUG] User: {current_user.user_id}")
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"[API_DEBUG] File content read successfully")
        logger.info(f"[API_DEBUG] File size: {file_size:,} bytes")
        logger.info(f"[API_DEBUG] File content type: {type(file_content)}")
        
        if file_content:
            logger.info(f"[API_DEBUG] File MD5: {hashlib.md5(file_content).hexdigest()}")
            logger.info(f"[API_DEBUG] First 50 bytes: {file_content[:50].hex()}")
            logger.info(f"[API_DEBUG] Last 50 bytes: {file_content[-50:].hex()}")
            
            # Check if it's a PDF
            if file.filename and file.filename.lower().endswith('.pdf'):
                logger.info(f"[API_DEBUG] PDF file detected")
                logger.info(f"[API_DEBUG] PDF header check: {file_content.startswith(b'%PDF')}")
                logger.info(f"[API_DEBUG] PDF EOF check: {b'%%EOF' in file_content}")
                
                if file_content.startswith(b'%PDF'):
                    logger.info(f"[API_DEBUG] ✅ Valid PDF header")
                else:
                    logger.error(f"[API_DEBUG] ❌ Invalid PDF header: {file_content[:20]}")
                
                if b'%%EOF' in file_content[-1000:]:
                    logger.info(f"[API_DEBUG] ✅ PDF EOF marker found")
                else:
                    logger.warning(f"[API_DEBUG] ⚠️ PDF EOF marker not found")
        else:
            logger.error(f"[API_DEBUG] ❌ File content is empty")
            raise HTTPException(status_code=400, detail="File content is empty")
        
        # Check environment
        import os
        is_lambda = (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
            os.getenv('AWS_EXECUTION_ENV') or 
            os.getenv('LAMBDA_TASK_ROOT') or
            os.getenv('AWS_LAMBDA_RUNTIME_API')
        )
        
        logger.info(f"[API_DEBUG] Environment check:")
        logger.info(f"[API_DEBUG]   AWS_LAMBDA_FUNCTION_NAME: {os.getenv('AWS_LAMBDA_FUNCTION_NAME')}")
        logger.info(f"[API_DEBUG]   AWS_EXECUTION_ENV: {os.getenv('AWS_EXECUTION_ENV')}")
        logger.info(f"[API_DEBUG]   LAMBDA_TASK_ROOT: {os.getenv('LAMBDA_TASK_ROOT')}")
        logger.info(f"[API_DEBUG]   AWS_LAMBDA_RUNTIME_API: {os.getenv('AWS_LAMBDA_RUNTIME_API')}")
        logger.info(f"[API_DEBUG]   Current working directory: {os.getcwd()}")
        logger.info(f"[API_DEBUG]   Is Lambda environment: {is_lambda}")
        
        # Test S3 upload
        from common.src.services.s3_upload_service import s3_upload_service
        
        logger.info(f"[API_DEBUG] Starting S3 upload test...")
        result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.user_id,
            content_type=file.content_type
        )
        
        logger.info(f"[API_DEBUG] S3 upload result: {result}")
        
        if result.get('status') == 'success':
            logger.info(f"[API_DEBUG] ✅ S3 upload successful")
            
            # Test download to verify
            try:
                s3_key = result['s3_key']
                logger.info(f"[API_DEBUG] Testing download verification...")
                
                downloaded_content = s3_upload_service.get_file_content(s3_key)
                if downloaded_content:
                    logger.info(f"[API_DEBUG] Download successful")
                    logger.info(f"[API_DEBUG] Downloaded size: {len(downloaded_content):,} bytes")
                    logger.info(f"[API_DEBUG] Downloaded MD5: {hashlib.md5(downloaded_content).hexdigest()}")
                    
                    if len(downloaded_content) == len(file_content):
                        logger.info(f"[API_DEBUG] ✅ Size match verified")
                    else:
                        logger.error(f"[API_DEBUG] ❌ Size mismatch: original={len(file_content)}, downloaded={len(downloaded_content)}")
                    
                    if hashlib.md5(downloaded_content).hexdigest() == hashlib.md5(file_content).hexdigest():
                        logger.info(f"[API_DEBUG] ✅ MD5 match verified")
                    else:
                        logger.error(f"[API_DEBUG] ❌ MD5 mismatch")
                        
                        # Check if it's a PDF and compare headers
                        if file.filename.lower().endswith('.pdf'):
                            logger.info(f"[API_DEBUG] PDF comparison:")
                            logger.info(f"[API_DEBUG] Original PDF header: {file_content[:20]}")
                            logger.info(f"[API_DEBUG] Downloaded PDF header: {downloaded_content[:20]}")
                            logger.info(f"[API_DEBUG] Original PDF EOF: {file_content[-50:]}")
                            logger.info(f"[API_DEBUG] Downloaded PDF EOF: {downloaded_content[-50:]}")
                else:
                    logger.error(f"[API_DEBUG] ❌ Download failed - no content returned")
                    
            except Exception as download_error:
                logger.error(f"[API_DEBUG] ❌ Download verification failed: {download_error}")
            
            return {
                "message": "Simple upload test completed successfully",
                "upload_result": result,
                "file_size": file_size,
                "environment": "lambda" if is_lambda else "local",
                "pdf_valid": file.filename.lower().endswith('.pdf') and file_content.startswith(b'%PDF')
            }
        else:
            logger.error(f"[API_DEBUG] ❌ S3 upload failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API_DEBUG] ❌ Error in simple upload test: {e}")
        import traceback
        logger.error(f"[API_DEBUG] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
    finally:
        logger.info(f"[API_DEBUG] === SIMPLE UPLOAD TEST END ===") 