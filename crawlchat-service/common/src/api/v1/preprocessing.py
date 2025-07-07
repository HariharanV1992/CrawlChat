"""
Unified Preprocessing API endpoints
Provides endpoints for document preprocessing with unified service.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from common.src.services.unified_preprocessing_service import unified_preprocessing_service, DocumentType
from common.src.services.document_processing_service import document_processing_service
from common.src.api.dependencies import get_current_user, get_optional_user
from common.src.models.auth import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])

@router.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    user: Optional[UserResponse] = Depends(get_optional_user),
    force_processing: bool = Form(False),
    document_type: Optional[str] = Form(None)
):
    """
    Process a document with unified preprocessing.
    
    Args:
        file: Document file to process
        user: Current user (optional)
        force_processing: Force specific processing even if not needed
        document_type: Optional document type override
        
    Returns:
        Processing result with metadata
    """
    try:
        # Read file content
        file_content = await file.read()
        filename = file.filename or "unknown"
        user_id = user.id if user else "anonymous"
        
        # Convert document_type string to enum if provided
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid document type: {document_type}. Valid types: {[dt.value for dt in DocumentType]}"
                )
        
        # Process document
        result = await unified_preprocessing_service.process_document(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            document_type=doc_type,
            force_processing=force_processing
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/process-document-with-vector-store")
async def process_document_with_vector_store(
    file: UploadFile = File(...),
    user: UserResponse = Depends(get_current_user),
    session_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Process a document with preprocessing and vector store integration.
    
    Args:
        file: Document file to process
        user: Current user
        session_id: Optional session ID for vector store organization
        metadata: Optional JSON metadata string
        
    Returns:
        Processing result with preprocessing and vector store information
    """
    try:
        # Read file content
        file_content = await file.read()
        filename = file.filename or "unknown"
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON metadata")
        
        # Process document with preprocessing and vector store
        result = await document_processing_service.process_document_with_preprocessing(
            file_content=file_content,
            filename=filename,
            user_id=user.id,
            metadata=parsed_metadata,
            session_id=session_id
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing document with vector store: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/process-from-s3")
async def process_document_from_s3(
    s3_bucket: str = Form(...),
    s3_key: str = Form(...),
    user: UserResponse = Depends(get_current_user),
    document_type: Optional[str] = Form(None)
):
    """
    Process a document from S3 with unified preprocessing.
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        user: Current user
        document_type: Optional document type override
        
    Returns:
        Processing result with metadata
    """
    try:
        # Convert document_type string to enum if provided
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid document type: {document_type}. Valid types: {[dt.value for dt in DocumentType]}"
                )
        
        # Process document from S3
        result = await unified_preprocessing_service.process_from_s3(
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            user_id=user.id,
            document_type=doc_type
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing document from S3: {e}")
        raise HTTPException(status_code=500, detail=f"S3 document processing failed: {str(e)}")

@router.post("/batch-process")
async def batch_process_documents(
    files: List[UploadFile] = File(...),
    user: UserResponse = Depends(get_current_user)
):
    """
    Process multiple documents in batch.
    
    Args:
        files: List of document files to process
        user: Current user
        
    Returns:
        List of processing results
    """
    try:
        documents = []
        for file in files:
            file_content = await file.read()
            documents.append({
                "content": file_content,
                "filename": file.filename or "unknown"
            })
        
        # Process documents in batch
        results = await unified_preprocessing_service.batch_process_documents(
            documents=documents,
            user_id=user.id
        )
        
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.get("/stats")
async def get_preprocessing_stats():
    """
    Get preprocessing service statistics and capabilities.
    
    Returns:
        Service statistics and supported features
    """
    try:
        stats = unified_preprocessing_service.get_processing_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting preprocessing stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/supported-types")
async def get_supported_document_types():
    """
    Get list of supported document types.
    
    Returns:
        List of supported document types
    """
    try:
        supported_types = [dt.value for dt in DocumentType]
        return JSONResponse(content={
            "supported_document_types": supported_types,
            "processing_types": [pt.value for pt in unified_preprocessing_service.ProcessingType]
        })
        
    except Exception as e:
        logger.error(f"Error getting supported types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported types: {str(e)}") 