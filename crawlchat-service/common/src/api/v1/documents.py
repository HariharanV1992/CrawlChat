"""
Documents API endpoints for Stock Market Crawler.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
import io
import os
from pathlib import Path
import hashlib
import traceback

from common.src.models.documents import (
    Document, DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse, DocumentType, DocumentStatus, DocumentUpload
)
from common.src.services.document_service import document_service

from common.src.api.dependencies import get_current_user
from common.src.models.auth import UserResponse
from common.src.core.exceptions import DocumentProcessingError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

class DocumentUploadRequest(BaseModel):
    session_id: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload and process a document using the unified document processor."""
    try:
        logger.info(f"[API] Uploading document: {file.filename} for user: {current_user.user_id}")
        
        # 🔍 ENHANCED DEBUGGING - Track file upload process
        logger.info(f"[API_DEBUG] === UPLOAD START ===")
        logger.info(f"[API_DEBUG] File info: {file.filename}")
        logger.info(f"[API_DEBUG] Content type: {file.content_type}")
        logger.info(f"[API_DEBUG] File size: {file.size if hasattr(file, 'size') else 'Unknown'}")
        
        # Read file content with enhanced error handling
        try:
            logger.info(f"[API_DEBUG] Reading file content...")
            file_content = await file.read()
            logger.info(f"[API_DEBUG] File content read successfully")
            logger.info(f"[API_DEBUG] Content type: {type(file_content)}")
            logger.info(f"[API_DEBUG] Content length: {len(file_content) if file_content else 'None'}")
            
            if file_content:
                logger.info(f"[API_DEBUG] Content MD5: {hashlib.md5(file_content).hexdigest()}")
                logger.info(f"[API_DEBUG] First 20 bytes: {file_content[:20].hex()}")
                logger.info(f"[API_DEBUG] Last 20 bytes: {file_content[-20:].hex()}")
                
                # Validate PDF if it's a PDF
                if file.filename and file.filename.lower().endswith('.pdf'):
                    if file_content.startswith(b'%PDF'):
                        logger.info(f"[API_DEBUG] ✅ Valid PDF header detected")
                    else:
                        logger.warning(f"[API_DEBUG] ⚠️ Invalid PDF header: {file_content[:10]}")
                    
                    if b'%%EOF' in file_content:
                        logger.info(f"[API_DEBUG] ✅ PDF EOF marker found")
                    else:
                        logger.warning(f"[API_DEBUG] ⚠️ PDF EOF marker not found")
            else:
                logger.error(f"[API_DEBUG] ❌ File content is empty or None")
                raise HTTPException(status_code=400, detail="File content is empty")
                
        except Exception as read_error:
            logger.error(f"[API_DEBUG] ❌ Error reading file: {read_error}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(read_error)}")
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON metadata")
        
        # 🔍 FINAL CHECK before S3 upload
        logger.info(f"[API_DEBUG] === FINAL CHECK BEFORE S3 UPLOAD ===")
        logger.info(f"[API_DEBUG] File content length: {len(file_content)}")
        logger.info(f"[API_DEBUG] File content MD5: {hashlib.md5(file_content).hexdigest()}")
        logger.info(f"[API_DEBUG] File content type: {type(file_content)}")
        
        # Upload to S3 using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        upload_result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=file.filename or "unknown",
            user_id=current_user.user_id,
            content_type=file.content_type
        )
        
        if upload_result.get('status') != 'success':
            logger.error(f"[API_DEBUG] ❌ S3 upload failed: {upload_result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Upload failed: {upload_result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"[API_DEBUG] ✅ S3 upload successful")
        logger.info(f"[API_DEBUG] === UPLOAD COMPLETE ===")
        
        # Return upload result
        return {
            "message": "Document uploaded successfully",
            "document_id": upload_result.get('s3_key'),  # Use S3 key as document ID
            "filename": upload_result.get('filename'),
            "s3_key": upload_result.get('s3_key'),
            "file_size": upload_result.get('file_size'),
            "upload_method": upload_result.get('upload_method')
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error uploading document: {e}")
        logger.error(f"[API_DEBUG] Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[API_DEBUG] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/process-crawled")
async def process_crawled_content(
    content: str,
    filename: str,
    session_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Process crawled content using the unified document processor."""
    try:
        logger.info(f"[API] Processing crawled content: {filename} for user: {current_user.user_id}")
        
        # Simple content processing without unified processor
        document_id = str(uuid.uuid4())
        result = {
            "status": "success",
            "document_id": document_id,
            "filename": filename,
            "content_length": len(content),
            "vector_store_result": None
        }
        
        if result.get("status") == "success":
            return {
                "message": "Crawled content processed successfully",
                "document_id": result.get("document_id"),
                "filename": result.get("filename"),
                "content_length": result.get("content_length", 0),
                "vector_store_result": result.get("vector_store_result")
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Content processing failed: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error processing crawled content: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/process", response_model=DocumentResponse)
async def process_document(
    request: DocumentUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Process a document with AI analysis."""
    try:
        # Verify document belongs to user
        document = await document_service.get_document(
            request.document_id, 
            current_user.user_id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process document
        response = await document_service.process_document(
            document.file_path,
            request.user_query
        )
        
        return response
        
    except HTTPException:
        raise
    except DocumentProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document")

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    document_type: Optional[DocumentType] = Query(None)
):
    """List documents for the current user."""
    try:
        document_list = await document_service.list_user_documents(
            current_user.user_id,
            limit=limit,
            skip=skip
        )
        
        # Filter by document type if specified
        if document_type:
            document_list.documents = [
                doc for doc in document_list.documents
                if doc.document_type == document_type
            ]
        
        return document_list
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@router.get("/page-usage")
async def get_user_page_usage(current_user: UserResponse = Depends(get_current_user)):
    """Get the user's current total processed pages and the page limit."""
    try:
        total_pages = await document_service.get_total_pages_for_user(current_user.user_id)
        return {
            "user_id": current_user.user_id,
            "total_pages": total_pages,
            "page_limit": 100
        }
    except Exception as e:
        logger.error(f"Error getting user page usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user page usage")

@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific document."""
    try:
        document = await document_service.get_document(document_id, current_user.user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a document."""
    try:
        success = await document_service.delete_document(document_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.delete("/filename/{filename}")
async def delete_document_by_filename(
    filename: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a document by filename."""
    try:
        success = await document_service.delete_document_by_filename(filename, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document by filename: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.get("/task/{task_id}", response_model=List[Document])
async def get_task_documents(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get documents for a specific task."""
    try:
        documents = await document_service.get_task_documents(task_id)
        
        # Filter documents that belong to the current user
        user_documents = [
            doc for doc in documents
            if doc.user_id == current_user.user_id
        ]
        
        return user_documents
        
    except Exception as e:
        logger.error(f"Error getting task documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task documents")

@router.post("/batch-process")
async def batch_process_documents(
    task_id: str,
    user_query: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Process all documents for a specific task."""
    try:
        documents = await document_service.get_task_documents(task_id)
        
        # Filter documents that belong to the current user
        user_documents = [
            doc for doc in documents
            if doc.user_id == current_user.user_id
        ]
        
        results = []
        for document in user_documents:
            try:
                response = await document_service.process_document(
                    document.file_path,
                    user_query
                )
                results.append({
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "status": "success",
                    "processing_time": response.processing_time
                })
            except Exception as e:
                results.append({
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "task_id": task_id,
            "total_documents": len(user_documents),
            "processed": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error batch processing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch process documents")

@router.get("/download/{filename}")
async def download_document(
    filename: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Download a document by filename."""
    try:
        # Get document info
        document = await document_service.get_document_by_filename(filename, current_user.user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if file exists
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail="Error reading document file")
        
        # Determine content type
        content_type = "application/octet-stream"
        if filename.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.txt'):
            content_type = "text/plain"
        elif filename.lower().endswith('.html'):
            content_type = "text/html"
        elif filename.lower().endswith('.csv'):
            content_type = "text/csv"
        elif filename.lower().endswith('.json'):
            content_type = "application/json"
        elif filename.lower().endswith('.xml'):
            content_type = "application/xml"
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download document") 