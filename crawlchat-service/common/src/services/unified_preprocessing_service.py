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
        """Process PDF documents with text extraction and image conversion if needed."""
        try:
            logger.info(f"[UNIFIED_PREPROCESSING] Processing PDF: {filename}")
            
            # Step 1: Try to extract text directly from PDF
            text_content = await self._extract_text_from_pdf(pdf_content)
            
            if text_content and len(text_content.strip()) > 50 and not force_processing:
                # PDF has extractable text, use as-is
                logger.info(f"[UNIFIED_PREPROCESSING] PDF has extractable text ({len(text_content)} characters), using as-is")
                
                # Upload to normalized documents bucket
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
                    "processing_type": ProcessingType.DIRECT_TEXT.value,
                    "document_type": DocumentType.PDF.value,
                    "text_content": text_content,
                    "text_length": len(text_content),
                    "normalized_key": normalized_key,
                    "message": "PDF processed directly - contains extractable text",
                    "filename": filename,
                    "user_id": user_id
                }
            else:
                # PDF needs conversion to images
                logger.info("[UNIFIED_PREPROCESSING] PDF has no extractable text, converting to images")
                return await self._convert_pdf_to_images(pdf_content, filename, user_id)
                
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error processing PDF {filename}: {e}")
            raise PreprocessingError(f"PDF processing failed: {e}")
    
    async def _extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Try to extract text from PDF using various libraries."""
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    logger.info("[UNIFIED_PREPROCESSING] Successfully extracted text using PyPDF2")
                    return text
            except Exception as e:
                logger.debug(f"[UNIFIED_PREPROCESSING] PyPDF2 extraction failed: {e}")
            
            # Try pdfminer.six
            try:
                from pdfminer.high_level import extract_text_to_fp
                from pdfminer.layout import LAParams
                
                output = io.StringIO()
                extract_text_to_fp(io.BytesIO(pdf_content), output, laparams=LAParams())
                text = output.getvalue()
                if text.strip():
                    logger.info("[UNIFIED_PREPROCESSING] Successfully extracted text using pdfminer.six")
                    return text
            except Exception as e:
                logger.debug(f"[UNIFIED_PREPROCESSING] pdfminer.six extraction failed: {e}")
            
            # Try PyMuPDF
            try:
                import fitz
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                if text.strip():
                    logger.info("[UNIFIED_PREPROCESSING] Successfully extracted text using PyMuPDF")
                    return text
            except Exception as e:
                logger.debug(f"[UNIFIED_PREPROCESSING] PyMuPDF extraction failed: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Text extraction failed: {e}")
            return None
    
    async def _convert_pdf_to_images(
        self, 
        pdf_content: bytes, 
        filename: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Convert PDF to images and upload to S3."""
        try:
            # Convert PDF to images using pdf2image
            image_files = await self._convert_pdf_to_images_local(pdf_content, filename)
            
            if not image_files:
                raise PreprocessingError("Failed to convert PDF to images")
            
            # Upload images to S3
            uploaded_keys = []
            for i, (image_content, image_filename) in enumerate(image_files):
                s3_key = f"normalized-documents/{user_id}/images/{os.path.splitext(filename)[0]}_page_{i+1}.png"
                
                if self.s3_client:
                    self.s3_client.put_object(
                        Bucket=config.s3_bucket,
                        Key=s3_key,
                        Body=image_content,
                        ContentType='image/png'
                    )
                uploaded_keys.append(s3_key)
                logger.info(f"[UNIFIED_PREPROCESSING] Uploaded image {i+1}/{len(image_files)}: {s3_key}")
            
            return {
                "status": "success",
                "processing_type": ProcessingType.PDF_TO_IMAGES.value,
                "document_type": DocumentType.PDF.value,
                "image_count": len(image_files),
                "uploaded_keys": uploaded_keys,
                "message": f"PDF converted to {len(image_files)} images",
                "filename": filename,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error converting PDF to images: {e}")
            raise PreprocessingError(f"PDF to image conversion failed: {e}")
    
    async def _convert_pdf_to_images_local(
        self, 
        pdf_content: bytes, 
        filename: str
    ) -> List[Tuple[bytes, str]]:
        """Convert PDF to images locally using pdf2image."""
        try:
            import pdf2image
            from PIL import Image
            import io
            
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(
                pdf_content,
                dpi=200,  # Good balance between quality and size
                fmt='PNG',
                thread_count=1  # Single thread for Lambda compatibility
            )
            
            image_files = []
            for i, image in enumerate(images):
                # Convert PIL image to bytes
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG', optimize=True)
                img_bytes = img_buffer.getvalue()
                
                image_filename = f"{os.path.splitext(filename)[0]}_page_{i+1}.png"
                image_files.append((img_bytes, image_filename))
                
                logger.info(f"[UNIFIED_PREPROCESSING] Converted page {i+1} to image: {len(img_bytes)} bytes")
            
            return image_files
            
        except Exception as e:
            logger.error(f"[UNIFIED_PREPROCESSING] Error converting PDF to images locally: {e}")
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