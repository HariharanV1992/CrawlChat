"""
Unified Preprocessing API endpoints
Provides endpoints for document preprocessing with unified service.
"""

import logging
import os
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

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
        
        # Upload to S3 using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        result = s3_upload_service.upload_user_document(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            content_type=file.content_type
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

        
        # Get file content from S3
        from common.src.services.s3_upload_service import s3_upload_service, S3UploadService
        
        # Create a temporary S3 upload service instance for the specified bucket
        temp_s3_service = S3UploadService(bucket_name=s3_bucket, region=os.getenv('AWS_REGION', 'ap-south-1'))
        
        # Get file content
        file_content = temp_s3_service.get_file_content(s3_key)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found in S3")
        
        # Upload to our main bucket for processing
        filename = os.path.basename(s3_key)
        result = s3_upload_service.upload_temp_file(
            file_content=file_content,
            filename=filename,
            purpose="s3_import",
            user_id=user.id
        )
        
        if result.get('status') != 'success':
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to import file from S3: {result.get('error', 'Unknown error')}"
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
        
        # Upload documents in batch using the single S3 upload service
        from common.src.services.s3_upload_service import s3_upload_service
        results = []
        
        for doc in documents:
            result = s3_upload_service.upload_user_document(
                file_content=doc["content"],
                filename=doc["filename"],
                user_id=user.id
            )
            results.append(result)
        
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.get("/stats")
async def get_preprocessing_stats():
    """
    Get S3 upload service statistics and capabilities.
    
    Returns:
        Service statistics and supported features
    """
    try:
        from common.src.services.s3_upload_service import s3_upload_service
        stats = {
            "service": "s3_upload_service",
            "bucket": s3_upload_service.bucket_name,
            "region": s3_upload_service.region,
            "capabilities": {
                "file_upload": True,
                "temp_file_upload": True,
                "file_verification": True,
                "file_deletion": True,
                "lambda_compatible": True
            }
        }
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting S3 upload stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/supported-types")
async def get_supported_document_types():
    """
    Get list of supported document types.
    
    Returns:
        List of supported document types
    """
    try:
        supported_types = [
            '.pdf', '.doc', '.docx', '.txt', '.html', '.xlsx', '.xls', 
            '.csv', '.ppt', '.pptx', '.json', '.png', '.jpg', '.jpeg', 
            '.gif', '.bmp', '.tiff'
        ]
        return JSONResponse(content={
            "supported_document_types": supported_types,
            "upload_method": "temp_file_upload_file"
        })
        
    except Exception as e:
        logger.error(f"Error getting supported types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported types: {str(e)}") 