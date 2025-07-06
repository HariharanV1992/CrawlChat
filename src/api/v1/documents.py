"""
Documents API endpoints for Stock Market Crawler.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional

from src.models.documents import (
    Document, DocumentUpload, DocumentProcess, DocumentProcessResponse, 
    DocumentList, DocumentType
)
from src.services.document_service import document_service
from src.api.dependencies import get_current_user
from src.models.auth import UserResponse
from src.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    task_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document."""
    try:
        # Read file content
        content = await file.read()
        
        # Create upload data
        upload_data = DocumentUpload(
            filename=file.filename,
            content=content,
            user_id=current_user.user_id,
            task_id=task_id
        )
        
        # Upload document
        document = await document_service.upload_document(upload_data)
        return document
        
    except DocumentProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
    request: DocumentProcess,
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

@router.get("/", response_model=DocumentList)
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