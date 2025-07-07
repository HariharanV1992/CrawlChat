"""
Unified Document Preprocessing Service
Consolidates all document preprocessing logic including PDF processing, text extraction, and document normalization.
Handles multiple document types and provides a unified interface for document processing.
"""

import logging
import os
import io
import asyncio
import time
import tempfile
import json
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Tuple, Union
from pathlib import Path
from enum import Enum
import boto3
from botocore.exceptions import ClientError

from common.src.core.config import config
from common.src.core.exceptions import PreprocessingError
from common.src.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Supported document types for preprocessing."""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    DOCUMENT = "document"
    UNKNOWN = "unknown"

class ProcessingType(Enum):
    """Types of processing that can be applied."""
    DIRECT_TEXT = "direct_text"
    PDF_TO_IMAGES = "pdf_to_images"
    TEXT_EXTRACTION = "text_extraction"
    NORMALIZATION = "normalization"

class UnifiedPreprocessingService:
    """Unified service for preprocessing all types of documents."""
    
    def __init__(self):
        """Initialize the unified preprocessing service."""
        self.s3_client = None
        self.storage_service = get_storage_service()
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients."""
        try:
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                self.s3_client = boto3.client('s3')
            else:
                # Running in ECS or locally - use credentials if available
                self.s3_client = boto3.client('s3')
            
            logger.info("AWS clients initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.s3_client = None
    
    async def process_document(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str = "anonymous",
        document_type: Optional[DocumentType] = None,
        force_processing: bool = False
    ) -> Dict[str, Any]:
        """
        Process any type of document with unified preprocessing logic.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            user_id: User ID for organization
            document_type: Optional document type override
            force_processing: Force specific processing even if not needed
            
        Returns:
            Processing result with metadata and normalized content
        """
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing document: {filename}")
            
            # Determine document type if not provided
            if not document_type:
                document_type = self._detect_document_type(filename, file_content)
            
            logger.info(f"[UNIFIED_PREPROCESSING] Detected document type: {document_type.value}")
            
            # Process based on document type
            if document_type == DocumentType.PDF:
                return await self._process_pdf(file_content, filename, user_id, force_processing)
            elif document_type == DocumentType.IMAGE:
                return await self._process_image(file_content, filename, user_id)
            elif document_type == DocumentType.TEXT:
                return await self._process_text(file_content, filename, user_id)
            else:
                return await self._process_generic(file_content, filename, user_id, document_type)
                
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing document {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to process document: {e}",
                "filename": filename,
                "document_type": document_type.value if document_type else "unknown"
            }
    
    def _detect_document_type(self, filename: str, file_content: bytes) -> DocumentType:
        """Detect document type based on filename and content."""
        filename_lower = filename.lower()
        
        # Check file extension
        if filename_lower.endswith('.pdf'):
            return DocumentType.PDF
        elif any(filename_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']):
            return DocumentType.IMAGE
        elif any(filename_lower.endswith(ext) for ext in ['.txt', '.md', '.csv', '.json']):
            return DocumentType.TEXT
        else:
            # Try to detect from content
            if file_content.startswith(b'%PDF'):
                return DocumentType.PDF
            elif file_content.startswith(b'\x89PNG') or file_content.startswith(b'\xff\xd8\xff'):
                return DocumentType.IMAGE
            else:
                return DocumentType.DOCUMENT
    
    async def _process_pdf(
        self, 
        pdf_content: bytes, 
        filename: str, 
        user_id: str,
        force_processing: bool = False
    ) -> Dict[str, Any]:
        """
        Upload PDF to S3 for Textract processing. Textract service will handle PDF-to-image conversion.
        """
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing PDF: {filename}")
            
            # Upload PDF to normalized documents bucket
            normalized_key = f"normalized-documents/{user_id}/{filename}"
            
            if self.s3_client:
                self.s3_client.put_object(
                    Bucket=config.s3_bucket,
                    Key=normalized_key,
                    Body=pdf_content,
                    ContentType='application/pdf'
                )
            
            return {
                "status": "success",
                "processing_type": ProcessingType.NORMALIZATION.value,
                "document_type": DocumentType.PDF.value,
                "normalized_key": normalized_key,
                "message": "PDF uploaded for Textract processing",
                "filename": filename,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing PDF {filename}: {e}")
            raise PreprocessingError(f"PDF processing failed: {e}")
    
    async def _convert_pdf_to_images_local(
        self, 
        pdf_content: bytes, 
        filename: str
    ) -> List[Tuple[bytes, str]]:
        """
        This method is deprecated. PDF-to-image conversion is now handled by the Textract service.
        """
        logger.warning("[UNIFIED_PREPROCESSING] PDF-to-image conversion is now handled by Textract service")
        return []
    
    async def _process_image(
        self, 
        image_content: bytes, 
        filename: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Process image documents."""
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing image: {filename}")
            
            # Upload image to normalized documents bucket
            normalized_key = f"normalized-documents/{user_id}/images/{filename}"
            
            if self.s3_client:
                self.s3_client.put_object(
                    Bucket=config.s3_bucket,
                    Key=normalized_key,
                    Body=image_content,
                    ContentType=self._get_content_type(filename)
                )
            
            return {
                "status": "success",
                "processing_type": ProcessingType.NORMALIZATION.value,
                "document_type": DocumentType.IMAGE.value,
                "normalized_key": normalized_key,
                "message": "Image processed and normalized",
                "filename": filename,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing image {filename}: {e}")
            raise PreprocessingError(f"Image processing failed: {e}")
    
    async def _process_text(
        self, 
        text_content: bytes, 
        filename: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Process text documents."""
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing text document: {filename}")
            
            # Decode text content
            text = text_content.decode('utf-8', errors='ignore')
            
            # Upload text to normalized documents bucket
            normalized_key = f"normalized-documents/{user_id}/text/{filename}"
            
            if self.s3_client:
                self.s3_client.put_object(
                    Bucket=config.s3_bucket,
                    Key=normalized_key,
                    Body=text_content,
                    ContentType='text/plain'
                )
            
            return {
                "status": "success",
                "processing_type": ProcessingType.DIRECT_TEXT.value,
                "document_type": DocumentType.TEXT.value,
                "text_content": text,
                "text_length": len(text),
                "normalized_key": normalized_key,
                "message": "Text document processed",
                "filename": filename,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing text document {filename}: {e}")
            raise PreprocessingError(f"Text processing failed: {e}")
    
    async def _process_generic(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """Process generic documents."""
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing generic document: {filename}")
            
            # Upload file to normalized documents bucket
            normalized_key = f"normalized-documents/{user_id}/documents/{filename}"
            
            if self.s3_client:
                self.s3_client.put_object(
                    Bucket=config.s3_bucket,
                    Key=normalized_key,
                    Body=file_content,
                    ContentType=self._get_content_type(filename)
                )
            
            return {
                "status": "success",
                "processing_type": ProcessingType.NORMALIZATION.value,
                "document_type": document_type.value,
                "normalized_key": normalized_key,
                "message": "Generic document processed and normalized",
                "filename": filename,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing generic document {filename}: {e}")
            raise PreprocessingError(f"Generic document processing failed: {e}")
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from file extension."""
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        ext = Path(filename).suffix.lower()
        return content_types.get(ext, 'application/octet-stream')
    
    async def process_from_s3(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        user_id: str = "anonymous",
        document_type: Optional[DocumentType] = None
    ) -> Dict[str, Any]:
        """Process a document from S3."""
        try:
            if not self.s3_client:
                raise PreprocessingError("AWS S3 client not available")
            
            logger.info(f"[UNIFIED_PREPROCESSING] Processing document from S3: s3://{s3_bucket}/{s3_key}")
            
            # Download file from S3
            response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = response['Body'].read()
            
            # Process the document
            filename = os.path.basename(s3_key)
            return await self.process_document(file_content, filename, user_id, document_type)
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing document from S3 {s3_key}: {e}")
            raise PreprocessingError(f"S3 document processing failed: {e}")
    
    async def batch_process_documents(
        self, 
        documents: List[Dict[str, Any]], 
        user_id: str = "anonymous"
    ) -> List[Dict[str, Any]]:
        """Process multiple documents in batch."""
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing {len(documents)} documents in batch")
            
            results = []
            for doc in documents:
                try:
                    file_content = doc.get('content')
                    filename = doc.get('filename', 'unknown')
                    document_type = doc.get('document_type')
                    
                    if document_type:
                        doc_type = DocumentType(document_type)
                    else:
                        doc_type = None
                    
                    result = await self.process_document(
                        file_content, 
                        filename, 
                        user_id, 
                        doc_type
                    )
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"[UNIFIED_PREPROCESSING] Error processing document in batch: {e}")
                    results.append({
                        "status": "error",
                        "error": str(e),
                        "filename": doc.get('filename', 'unknown')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error in batch processing: {e}")
            raise PreprocessingError(f"Batch processing failed: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics and capabilities."""
        return {
            "service": "unified_preprocessing",
            "supported_document_types": [dt.value for dt in DocumentType],
            "processing_types": [pt.value for pt in ProcessingType],
            "capabilities": {
                "pdf_text_extraction": True,
                "pdf_to_image_conversion": True,
                "image_processing": True,
                "text_processing": True,
                "s3_integration": self.s3_client is not None,
                "batch_processing": True
            },
            "aws_region": config.s3_region,
            "s3_bucket": config.s3_bucket
        }

# Global instance
unified_preprocessing_service = UnifiedPreprocessingService() 