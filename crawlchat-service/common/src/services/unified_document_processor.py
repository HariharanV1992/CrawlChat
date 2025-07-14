"""
Unified Document Processing Service
Centralized service for processing all document types (PDF, images, text, crawled content)
with consistent preprocessing, text extraction, chunking, and vector store integration.
"""

import logging
import asyncio
import uuid
import hashlib
import re
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import io

from common.src.models.documents import Document, DocumentType, DocumentStatus
from common.src.services.unified_storage_service import unified_storage_service
from common.src.services.vector_store_service import vector_store_service
from common.src.services.aws_textract_service import textract_service, DocumentType
from common.src.core.database import mongodb
from common.src.core.config import config

logger = logging.getLogger(__name__)

class UnifiedDocumentProcessor:
    """
    Unified service for processing all document types with consistent pipeline:
    1. Document type detection
    2. Content extraction (text, images, etc.)
    3. Content cleaning and normalization
    4. Chunking (if needed)
    5. Vector store integration
    6. Metadata management
    """
    
    def __init__(self):
        # Use unified storage service
        pass
        
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "uploaded"
    ) -> Dict[str, Any]:
        """
        Process any document type with unified pipeline.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            user_id: User ID for organization
            session_id: Optional session ID for vector store organization
            metadata: Additional metadata
            source: Document source ("uploaded", "crawled", etc.)
            
        Returns:
            Processing result with all pipeline information
        """
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Processing document: {filename} (source: {source})")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Step 1: Detect document type
            doc_type = self._detect_document_type(filename, file_content)
            logger.info(f"[UNIFIED_PROCESSOR] Detected type: {doc_type}")
            
            # Step 2: Extract content based on type
            content_result = await self._extract_content(file_content, filename, doc_type)
            
            if content_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": content_result.get("error", "Content extraction failed"),
                    "document_id": document_id,
                    "filename": filename
                }
            
            # Step 3: Clean and normalize content
            text_content = content_result.get("text_content", "")
            if text_content:
                text_content = self._clean_content(text_content, filename)
            
            # Step 4: Create document record in database
            document_record = await self._create_document_record(
                document_id=document_id,
                filename=filename,
                user_id=user_id,
                doc_type=doc_type,
                file_size=len(file_content),
                metadata=metadata,
                source=source
            )
            
            # Step 5: Process with vector store if we have text content
            vector_result = None
            if text_content and text_content.strip():
                vector_result = await self._process_with_vector_store(
                    document_id=document_id,
                    content=text_content,
                    filename=filename,
                    session_id=session_id,
                    metadata=metadata,
                    source=source
                )
            
            # Step 6: Update document record with processing results
            processing_status = DocumentStatus.PROCESSED
            if not text_content or not text_content.strip():
                processing_status = DocumentStatus.PROCESSED_NO_TEXT
            elif vector_result and vector_result.get("status") == "uploaded":
                processing_status = DocumentStatus.PROCESSED_VECTOR_PENDING
            elif vector_result and vector_result.get("status") == "error":
                processing_status = DocumentStatus.PROCESSED_VECTOR_FAILED
            
            await self._update_document_record(
                document_id=document_id,
                content=text_content,
                vector_result=vector_result,
                processing_status=processing_status
            )
            
            return {
                "status": "success",
                "document_id": document_id,
                "filename": filename,
                "document_type": doc_type,
                "content_length": len(text_content) if text_content else 0,
                "vector_store_result": vector_result,
                "processing_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error processing document {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "document_id": document_id if 'document_id' in locals() else None,
                "filename": filename
            }
    
    async def process_crawled_content(
        self,
        content: str,
        filename: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process crawled content (already extracted text).
        
        Args:
            content: Extracted text content
            filename: Generated filename
            user_id: User ID
            session_id: Optional session ID
            metadata: Additional metadata
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Processing crawled content: {filename}")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Clean content
            cleaned_content = self._clean_content(content, filename)
            
            # Create document record
            document_record = await self._create_document_record(
                document_id=document_id,
                filename=filename,
                user_id=user_id,
                doc_type="text",
                file_size=len(content.encode('utf-8')),
                metadata=metadata,
                source="crawled"
            )
            
            # Process with vector store
            vector_result = await self._process_with_vector_store(
                document_id=document_id,
                content=cleaned_content,
                filename=filename,
                session_id=session_id,
                metadata=metadata,
                source="crawled"
            )
            
            # Update document record
            await self._update_document_record(
                document_id=document_id,
                content=cleaned_content,
                vector_result=vector_result,
                processing_status=DocumentStatus.PROCESSED
            )
            
            return {
                "status": "success",
                "document_id": document_id,
                "filename": filename,
                "content_length": len(cleaned_content),
                "vector_store_result": vector_result
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error processing crawled content {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "filename": filename
            }
    
    def _detect_document_type(self, filename: str, file_content: bytes) -> str:
        """Detect document type based on filename and content."""
        filename_lower = filename.lower()
        
        # Check file extension first
        if filename_lower.endswith('.pdf'):
            return "pdf"
        elif any(filename_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']):
            return "image"
        elif any(filename_lower.endswith(ext) for ext in ['.txt', '.md', '.csv', '.json', '.html']):
            return "text"
        elif any(filename_lower.endswith(ext) for ext in ['.doc', '.docx']):
            return "document"
        else:
            # Try to detect from content
            if file_content.startswith(b'%PDF'):
                return "pdf"
            elif file_content.startswith(b'\x89PNG') or file_content.startswith(b'\xff\xd8\xff'):
                return "image"
            else:
                return "text"  # Default to text
    
    async def _extract_content(self, file_content: bytes, filename: str, doc_type: str) -> Dict[str, Any]:
        """Extract text content from document based on type."""
        try:
            if doc_type == "pdf":
                return await self._extract_pdf_content(file_content, filename)
            elif doc_type == "image":
                return await self._extract_image_content(file_content, filename)
            elif doc_type == "text":
                return await self._extract_text_content(file_content, filename)
            elif doc_type == "document":
                return await self._extract_document_content(file_content, filename)
            else:
                return await self._extract_text_content(file_content, filename)
                
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error extracting content from {filename}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _extract_pdf_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from PDF using AWS Textract with fallback methods."""
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Extracting text from PDF: {filename}")
            
            # Upload PDF to S3 for Textract processing using unified storage
            result = await unified_storage_service.upload_temp_file(
                file_content=file_content,
                filename=filename,
                purpose="textract_pdf"
            )
            
            if not result:
                return {
                    "status": "error",
                    "error": "Failed to upload PDF to S3"
                }
            
            s3_key = result["s3_key"]
            
            # Determine document type for AWS pattern processing
            document_type = self._determine_document_type_for_textract(filename, file_content)
            logger.info(f"[UNIFIED_PROCESSOR] Detected document type: {document_type.value}")
            
            # Process with Textract using the full AWS pattern
            bucket_name = config.s3_bucket
            text_content, page_count = await textract_service.extract_text_from_s3_pdf(
                bucket_name, s3_key, document_type
            )
            
            # Clean up temporary file
            try:
                await unified_storage_service.delete_file(s3_key)
            except:
                pass  # Don't fail if cleanup fails
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": page_count,
                    "extraction_method": "aws_textract_pattern",
                    "document_type": document_type.value
                }
            else:
                # Try fallback methods
                logger.info(f"[UNIFIED_PROCESSOR] Textract returned no content, trying fallback methods for {filename}")
                return await self._try_fallback_pdf_extraction(file_content, filename)
                
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error extracting PDF content: {e}")
            # Try fallback methods
            return await self._try_fallback_pdf_extraction(file_content, filename)

    def _determine_document_type_for_textract(self, filename: str, file_content: bytes) -> DocumentType:
        """
        Determine the appropriate document type for AWS Textract pattern processing.
        """
        try:
            from common.src.services.aws_textract_service import DocumentType
            
            filename_lower = filename.lower()
            
            # Check for form/invoice documents
            form_keywords = ['form', 'invoice', 'receipt', 'tax', 'w2', '1099', 'bill', 'statement']
            if any(keyword in filename_lower for keyword in form_keywords):
                return DocumentType.FORM
            
            # Check for table-heavy documents
            table_keywords = ['report', 'table', 'spreadsheet', 'data', 'analysis', 'summary']
            if any(keyword in filename_lower for keyword in table_keywords):
                return DocumentType.TABLE_HEAVY
            
            # Check for invoice-specific documents
            invoice_keywords = ['invoice', 'bill', 'receipt', 'payment']
            if any(keyword in filename_lower for keyword in invoice_keywords):
                return DocumentType.INVOICE
            
            # Default to general
            return DocumentType.GENERAL
            
        except Exception as e:
            logger.warning(f"Error determining document type: {e}")
            return DocumentType.GENERAL

    async def _try_fallback_pdf_extraction(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Try fallback methods for PDF text extraction using AWS pattern."""
        try:
            # Try direct Textract processing with AWS pattern
            logger.info(f"[UNIFIED_PROCESSOR] Trying direct Textract processing with AWS pattern for {filename}")
            document_type = self._determine_document_type_for_textract(filename, file_content)
            text_content, page_count = await textract_service.upload_to_s3_and_extract(
                content=file_content,
                filename=filename,
                document_type=document_type
            )
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": page_count,
                    "extraction_method": "aws_textract_pattern_direct",
                    "document_type": document_type.value
                }
        except Exception as e:
            logger.warning(f"[UNIFIED_PROCESSOR] Direct Textract processing failed: {e}")
        
        try:
            # Try PyPDF2 extraction (lightweight, works everywhere)
            logger.info(f"[UNIFIED_PROCESSOR] Trying PyPDF2 extraction for {filename}")
            text_content, page_count = await textract_service._try_pypdf2_extraction(file_content, filename)
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": page_count,
                    "extraction_method": "pypdf2_extraction"
                }
        except Exception as e:
            logger.warning(f"[UNIFIED_PROCESSOR] PyPDF2 extraction failed: {e}")
        
        try:
            # Try aggressive text extraction (regex-based)
            logger.info(f"[UNIFIED_PROCESSOR] Trying aggressive text extraction for {filename}")
            text_content = await textract_service._try_aggressive_text_extraction(file_content, filename)
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": 1,
                    "extraction_method": "aggressive_text_extraction"
                }
        except Exception as e:
            logger.warning(f"[UNIFIED_PROCESSOR] Aggressive text extraction failed: {e}")
        
        # If all methods fail, return error
        return {
            "status": "error",
            "error": "All PDF extraction methods failed",
            "extraction_method": "all_methods_failed"
        }

    async def _try_fallback_image_extraction(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Try fallback methods for image text extraction using AWS pattern."""
        try:
            # Try direct Textract processing with AWS pattern
            logger.info(f"[UNIFIED_PROCESSOR] Trying direct Textract processing with AWS pattern for {filename}")
            document_type = self._determine_document_type_for_textract(filename, file_content)
            text_content, page_count = await textract_service.upload_to_s3_and_extract(
                content=file_content,
                filename=filename,
                document_type=document_type
            )
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": page_count,
                    "extraction_method": "aws_textract_pattern_direct",
                    "document_type": document_type.value
                }
        except Exception as e:
            logger.warning(f"[UNIFIED_PROCESSOR] Direct Textract processing failed: {e}")
        
        try:
            # Try raw text extraction (encoding-based)
            logger.info(f"[UNIFIED_PROCESSOR] Trying raw text extraction for {filename}")
            text_content = await textract_service._try_raw_text_extraction(file_content, filename)
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": 1,
                    "extraction_method": "raw_text_extraction"
                }
        except Exception as e:
            logger.warning(f"[UNIFIED_PROCESSOR] Raw text extraction failed: {e}")
        
        # If all methods fail, return error
        return {
            "status": "error",
            "error": "All image extraction methods failed",
            "extraction_method": "all_methods_failed"
        }
    
    async def _extract_image_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from image using AWS Textract with fallback methods."""
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Extracting text from image: {filename}")
            
            # Upload image to S3 for Textract processing using unified storage
            result = await unified_storage_service.upload_temp_file(
                file_content=file_content,
                filename=filename,
                purpose="textract_image"
            )
            
            if not result:
                return {
                    "status": "error",
                    "error": "Failed to upload image to S3"
                }
            
            s3_key = result["s3_key"]
            
            # Determine document type for AWS pattern processing
            document_type = self._determine_document_type_for_textract(filename, file_content)
            logger.info(f"[UNIFIED_PROCESSOR] Detected document type: {document_type.value}")
            
            # Process with Textract using the full AWS pattern
            bucket_name = config.s3_bucket
            text_content, page_count = await textract_service.extract_text_from_s3_pdf(
                bucket_name, s3_key, document_type
            )
            
            # Clean up temporary file
            try:
                await unified_storage_service.delete_file(s3_key)
            except:
                pass
            
            if text_content and text_content.strip():
                return {
                    "status": "success",
                    "text_content": text_content,
                    "page_count": page_count,
                    "extraction_method": "aws_textract_pattern",
                    "document_type": document_type.value
                }
            else:
                # Try fallback methods
                logger.info(f"[UNIFIED_PROCESSOR] Textract returned no content, trying fallback methods for {filename}")
                return await self._try_fallback_image_extraction(file_content, filename)
                
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error extracting image content: {e}")
            # Try fallback methods
            return await self._try_fallback_image_extraction(file_content, filename)
    
    async def _extract_text_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from text files."""
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Extracting text from text file: {filename}")
            
            # Decode text content
            text_content = file_content.decode('utf-8', errors='ignore')
            
            return {
                "status": "success",
                "text_content": text_content
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error extracting text content: {e}")
            return {
                "status": "error",
                "error": f"Text extraction failed: {str(e)}"
            }
    
    async def _extract_document_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from document files (DOC, DOCX)."""
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Extracting text from document: {filename}")
            
            # For now, treat as text file
            # In the future, this could use python-docx or other libraries
            text_content = file_content.decode('utf-8', errors='ignore')
            
            return {
                "status": "success",
                "text_content": text_content
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error extracting document content: {e}")
            return {
                "status": "error",
                "error": f"Document extraction failed: {str(e)}"
            }
    
    def _clean_content(self, content: str, filename: str) -> str:
        """Clean and normalize text content."""
        if not content:
            return ""
        
        # Remove HTML tags if it's an HTML file
        if filename.lower().endswith('.html'):
            content = re.sub(r'<[^>]+>', '', content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    async def _create_document_record(
        self,
        document_id: str,
        filename: str,
        user_id: str,
        doc_type: str,
        file_size: int,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "uploaded"
    ) -> Dict[str, Any]:
        """Create document record in database."""
        try:
            document_data = {
                "document_id": document_id,
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "document_type": doc_type,
                "status": DocumentStatus.PROCESSING.value,
                "source": source,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await mongodb.get_collection("documents").insert_one(document_data)
            logger.info(f"[UNIFIED_PROCESSOR] Created document record: {document_id}")
            
            return document_data
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error creating document record: {e}")
            raise
    
    async def _process_with_vector_store(
        self,
        document_id: str,
        content: str,
        filename: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "uploaded"
    ) -> Optional[Dict[str, Any]]:
        """Process document with vector store using non-blocking upload."""
        try:
            logger.info(f"[UNIFIED_PROCESSOR] Processing with vector store: {filename}")
            
            # Generate content hash for deduplication
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Prepare metadata
            vector_metadata = {
                "document_id": document_id,
                "filename": filename,
                "source": source,
                "content_hash": content_hash,
                "processed_at": int(datetime.utcnow().timestamp())
            }
            
            if metadata:
                vector_metadata.update(metadata)
            
            # Get session-specific vector store if session_id is provided
            vector_store_id = None
            if session_id:
                vector_store_id = await vector_store_service.get_or_create_session_vector_store(session_id)
            
            # Upload to vector store (non-blocking)
            file_id = await vector_store_service.upload_text_to_vector_store(
                text=content,
                filename=filename,
                vector_store_id=vector_store_id
            )
            
            # Check initial status
            status_check = await vector_store_service.check_file_upload_status(file_id, vector_store_id)
            initial_status = status_check.get("status", "unknown")
            
            logger.info(f"[UNIFIED_PROCESSOR] Vector store upload initiated: {file_id} (status: {initial_status})")
            
            return {
                "vector_store_file_id": file_id,
                "vector_store_id": vector_store_service.vector_store_id,
                "content_hash": content_hash,
                "status": "uploaded",  # Changed from "success" to "uploaded"
                "processing_status": initial_status,
                "message": "Document uploaded to vector store for processing"
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error processing with vector store: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _update_document_record(
        self,
        document_id: str,
        content: str,
        vector_result: Optional[Dict[str, Any]] = None,
        processing_status: DocumentStatus = DocumentStatus.PROCESSED
    ):
        """Update document record with processing results."""
        try:
            update_data = {
                "content": content,
                "status": processing_status.value,
                "processed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if vector_result:
                update_data["vector_store_result"] = vector_result
            
            await mongodb.get_collection("documents").update_one(
                {"document_id": document_id},
                {"$set": update_data}
            )
            
            logger.info(f"[UNIFIED_PROCESSOR] Updated document record: {document_id}")
            
        except Exception as e:
            logger.error(f"[UNIFIED_PROCESSOR] Error updating document record: {e}")

# Global instance
unified_document_processor = UnifiedDocumentProcessor() 