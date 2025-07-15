"""
Enhanced Document Processing Service with Vector Store Integration.
Provides advanced document processing, chunking, and vector store management.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid
import asyncio
from pathlib import Path
import re
import hashlib

from common.src.services.vector_store_service import vector_store_service
from common.src.services.s3_upload_service import s3_upload_service
from common.src.models.documents import DocumentType
from common.src.core.database import mongodb

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Enhanced service for processing documents with vector store integration."""
    
    def __init__(self):
        self.storage_service = s3_upload_service
        self.vector_store_id = None
        
    async def process_document_with_vector_store(
        self, 
        document_id: str, 
        content: str, 
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a document and store it in the vector store with enhanced metadata and deduplication."""
        try:
            logger.info(f"[DOC_PROCESSING] Processing document: {filename}")
            
            # Generate content hash for deduplication
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Check if document with same content already exists in this session
            if session_id:
                existing_doc = await self._check_existing_document(content_hash, session_id)
                if existing_doc:
                    logger.info(f"[DOC_PROCESSING] Document with same content already exists: {existing_doc['filename']} (skipping embedding)")
                    
                    # Store document metadata in MongoDB with reference to existing file
                    document_metadata = {
                        "id": document_id,
                        "filename": filename,
                        "vector_store_file_id": existing_doc['vector_store_file_id'],
                        "vector_store_id": existing_doc['vector_store_id'],
                        "content_hash": content_hash,
                        "is_duplicate": True,
                        "original_document_id": existing_doc['id'],
                        "attributes": {
                            "document_id": document_id,
                            "filename": filename,
                            "processed_at": int(datetime.utcnow().timestamp()),
                            "content_type": "crawled_data",
                            "source": "crawlchat",
                            "is_duplicate": True
                        },
                        "content_length": len(content),
                        "processed_at": datetime.utcnow(),
                        "status": "duplicate_skipped"
                    }
                    
                    # Add custom metadata if provided
                    if metadata:
                        document_metadata["attributes"].update(metadata)
                    
                    collection = mongodb.get_collection('processed_documents')
                    await collection.update_one(
                        {"id": document_id},
                        {"$set": document_metadata},
                        upsert=True
                    )
                    
                    return {
                        "document_id": document_id,
                        "vector_store_file_id": existing_doc['vector_store_file_id'],
                        "vector_store_id": existing_doc['vector_store_id'],
                        "status": "duplicate_skipped",
                        "content_hash": content_hash
                    }
            
            # Prepare attributes for vector store
            attributes = {
                "document_id": document_id,
                "filename": filename,
                "processed_at": int(datetime.utcnow().timestamp()),
                "content_type": metadata.get("content_type", "document") if metadata else "document",
                "source": metadata.get("source", "uploaded") if metadata else "uploaded",
                "content_hash": content_hash
            }
            
            # Add custom metadata if provided
            if metadata:
                attributes.update(metadata)
            
            # Get session-specific vector store if session_id is provided
            vector_store_id = None
            if session_id:
                vector_store_id = await vector_store_service.get_or_create_session_vector_store(session_id)
                logger.info(f"[DOC_PROCESSING] Using session-specific vector store: {vector_store_id}")
            
            # Log a preview of the extracted content
            logger.info(f"[DOC_PROCESSING] Content preview for {filename}: {content[:500].replace(chr(10), ' ').replace(chr(13), ' ')}")
            
            # Upload to vector store
            file_id = await vector_store_service.upload_text_to_vector_store(
                text=content,
                filename=filename,
                vector_store_id=vector_store_id
            )
            
            # Store document metadata in MongoDB
            document_metadata = {
                "id": document_id,
                "filename": filename,
                "vector_store_file_id": file_id,
                "vector_store_id": vector_store_service.vector_store_id,
                "content_hash": content_hash,
                "is_duplicate": False,
                "attributes": attributes,
                "content_length": len(content),
                "processed_at": datetime.utcnow(),
                "status": "processed"
            }
            
            collection = mongodb.get_collection('processed_documents')
            await collection.update_one(
                {"id": document_id},
                {"$set": document_metadata},
                upsert=True
            )
            
            logger.info(f"[DOC_PROCESSING] Successfully processed document: {filename}")
            
            return {
                "document_id": document_id,
                "vector_store_file_id": file_id,
                "vector_store_id": vector_store_service.vector_store_id,
                "status": "success",
                "content_hash": content_hash
            }
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error processing document {filename}: {e}")
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_existing_document(self, content_hash: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Check if a document with the same content hash already exists in the session."""
        try:
            collection = mongodb.get_collection('processed_documents')
            
            # Look for existing document with same content hash in this session
            existing_doc = await collection.find_one({
                "content_hash": content_hash,
                "attributes.session_id": session_id,
                "is_duplicate": {"$ne": True}  # Don't consider already marked duplicates
            })
            
            if existing_doc:
                logger.info(f"[DOC_PROCESSING] Found existing document with same content: {existing_doc['filename']}")
                return existing_doc
            
            return None
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error checking for existing document: {e}")
            return None
    
    async def process_crawled_data(
        self, 
        crawled_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple crawled data entries and store them in vector store."""
        try:
            logger.info(f"[DOC_PROCESSING] Processing {len(crawled_data)} crawled data entries")
            
            results = []
            
            for data in crawled_data:
                try:
                    # Extract content and metadata
                    content = data.get('content', '')
                    url = data.get('url', '')
                    title = data.get('title', '')
                    domain = data.get('domain', '')
                    
                    # Generate document ID
                    document_id = str(uuid.uuid4())
                    
                    # Create filename from URL or title
                    filename = self._create_filename_from_url(url, title)
                    
                    # Prepare metadata
                    metadata = {
                        "url": url,
                        "title": title,
                        "domain": domain,
                        "crawled_at": data.get('crawled_at', int(datetime.utcnow().timestamp())),
                        "content_type": "web_page",
                        "source": "crawler"
                    }
                    
                    # Process the document
                    result = await self.process_document_with_vector_store(
                        document_id=document_id,
                        content=content,
                        filename=filename,
                        metadata=metadata
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"[DOC_PROCESSING] Error processing crawled data: {e}")
                    results.append({
                        "status": "error",
                        "error": str(e),
                        "data": data
                    })
            
            logger.info(f"[DOC_PROCESSING] Completed processing {len(results)} entries")
            return results
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error in batch processing: {e}")
            raise
    
    def _create_filename_from_url(self, url: str, title: str) -> str:
        """Create a filename from URL or title."""
        if title:
            # Clean title for filename
            clean_title = re.sub(r'[^\w\s-]', '', title)
            clean_title = re.sub(r'[-\s]+', '-', clean_title)
            return f"{clean_title[:50]}.txt"
        elif url:
            # Extract domain and path from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('.', '_')
            path = parsed.path.replace('/', '_')[:30]
            return f"{domain}_{path}.txt"
        else:
            return f"document_{uuid.uuid4().hex[:8]}.txt"
    
    async def search_documents(
        self, 
        query: str,
        max_results: int = 10,
        score_threshold: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search documents using vector store with optional filtering."""
        try:
            logger.info(f"[DOC_PROCESSING] Searching documents for: {query[:50]}...")
            
            # Get session-specific vector store if session_id is provided
            vector_store_id = None
            if session_id:
                vector_store_id = await vector_store_service.get_or_create_session_vector_store(session_id)
                logger.info(f"[DOC_PROCESSING] Searching in session-specific vector store: {vector_store_id}")
            
            # Perform search
            search_results = await vector_store_service.search_vector_store(
                query=query,
                max_results=max_results,
                score_threshold=score_threshold,
                vector_store_id=vector_store_id
            )
            
            # Enhance results with additional metadata
            enhanced_results = await self._enhance_search_results(search_results["results"])
            
            return {
                "results": enhanced_results,
                "search_query": search_results["search_query"],
                "has_more": search_results["has_more"],
                "total_results": len(enhanced_results)
            }
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error searching documents: {e}")
            raise
    

    
    async def _enhance_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance search results with additional metadata from MongoDB."""
        try:
            enhanced_results = []
            
            for result in results:
                # Get additional metadata from MongoDB if available
                file_id = result.get('file_id')
                if file_id:
                    collection = mongodb.get_collection('processed_documents')
                    doc_metadata = await collection.find_one({"vector_store_file_id": file_id})
                    
                    if doc_metadata:
                        result['document_metadata'] = doc_metadata
                
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error enhancing search results: {e}")
            return results
    
    async def get_document_summary(
        self, 
        query: str,
        max_results: int = 5
    ) -> str:
        """Get a synthesized summary based on search results."""
        try:
            # Search for relevant documents
            search_results = await self.search_documents(
                query=query,
                max_results=max_results
            )
            
            if not search_results["results"]:
                return "No relevant documents found to generate a summary."
            
            # Synthesize response
            summary = await vector_store_service.synthesize_response(
                query=query,
                search_results=search_results["results"]
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error generating document summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    async def list_processed_documents(
        self, 
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List processed documents with pagination."""
        try:
            collection = mongodb.get_collection('processed_documents')
            cursor = collection.find().sort("processed_at", -1).skip(skip).limit(limit)
            documents = await cursor.to_list(length=None)
            
            return documents
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error listing processed documents: {e}")
            return []
    
    async def delete_document(
        self, 
        document_id: str
    ) -> bool:
        """Delete a document from both vector store and MongoDB."""
        try:
            # Get document metadata
            collection = mongodb.get_collection('processed_documents')
            doc_metadata = await collection.find_one({"id": document_id})
            
            if not doc_metadata:
                logger.warning(f"[DOC_PROCESSING] Document {document_id} not found")
                return False
            
            # Delete from vector store
            vector_store_file_id = doc_metadata.get('vector_store_file_id')
            if vector_store_file_id:
                await vector_store_service.delete_vector_store_file(vector_store_file_id)
            
            # Delete from MongoDB
            await collection.delete_one({"id": document_id})
            
            logger.info(f"[DOC_PROCESSING] Successfully deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error deleting document {document_id}: {e}")
            return False
    
    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            # Get vector store info
            store_info = await vector_store_service.get_vector_store_info()
            
            # Get file count
            files = await vector_store_service.list_vector_store_files()
            
            # Get document count from MongoDB
            collection = mongodb.get_collection('processed_documents')
            doc_count = await collection.count_documents({})
            
            return {
                "vector_store_info": store_info,
                "file_count": len(files),
                "document_count": doc_count,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error getting vector store stats: {e}")
            return {"error": str(e)}
    


    async def process_document_with_preprocessing(
        self,
        file_content: bytes,
        filename: str,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document with unified preprocessing before vector store integration.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            user_id: User ID for organization
            metadata: Additional metadata
            session_id: Optional session ID for vector store organization
            
        Returns:
            Processing result with preprocessing and vector store information
        """
        try:
            logger.info(f"[DOC_PROCESSING] Processing document with preprocessing: {filename}")
            
            # Step 1: Extract text content using appropriate method
            text_content = await self._extract_text_with_aws_textract(file_content, filename)
            
            if not text_content:
                # Fallback to local text extraction
                text_content = self._extract_text_from_file(file_content, filename)
            
            if not text_content:
                return {
                    "status": "error",
                    "error": "No text content could be extracted from file",
                    "filename": filename
                }
            
            if text_content:
                document_id = str(uuid.uuid4())
                
                # Prepare metadata
                processing_metadata = {
                    "processing_type": "aws_textract_with_fallback",
                    "document_type": self._get_document_type(filename),
                    "user_id": user_id
                }
                
                if metadata:
                    processing_metadata.update(metadata)
                
                # Process with vector store
                vector_result = await self.process_document_with_vector_store(
                    document_id=document_id,
                    content=text_content,
                    filename=filename,
                    metadata=processing_metadata,
                    session_id=session_id
                )
                
                # Combine results
                return {
                    "status": "success",
                    "preprocessing": {
                        "status": "success",
                        "text_content": text_content,
                        "processing_type": "aws_textract_with_fallback"
                    },
                    "vector_store": vector_result,
                    "document_id": document_id,
                    "filename": filename
                }
            else:
                # Document was processed but no text extracted (e.g., images)
                return {
                    "status": "success",
                    "preprocessing": {
                        "status": "no_text_extracted",
                        "processing_type": "aws_textract_with_fallback"
                    },
                    "vector_store": None,
                    "message": "Document preprocessed but no text content for vector store",
                    "filename": filename
                }
                
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error processing document with preprocessing {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "filename": filename
            }

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        session_id: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Process a document with preprocessing and vector store integration."""
        try:
            logger.info(f"[DOC_PROCESSING] Processing document: {filename} for user: {user_id}")
            
            # Use the existing process_document_with_preprocessing method
            result = await self.process_document_with_preprocessing(
                file_content=file_content,
                filename=filename,
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "document_id": document_id,
                    "source": "chat_upload"
                },
                session_id=session_id
            )
            
            logger.info(f"[DOC_PROCESSING] Document processing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error processing document {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "content_length": 0,
                "extraction_method": "none"
            }

    def _extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text from file content using appropriate method based on file type."""
        try:
            import os
            _, ext = os.path.splitext(filename.lower())
            
            # For PDF files, use proper PDF text extraction
            if ext == '.pdf':
                logger.info(f"[DOC_PROCESSING] Extracting text from PDF: {filename}")
                return self._extract_text_from_pdf(file_content, filename)
            
            # For text files, try to decode as text
            elif ext in ['.txt', '.md', '.html', '.htm']:
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return file_content.decode('latin-1')
                    except UnicodeDecodeError:
                        logger.warning(f"[DOC_PROCESSING] Could not decode text file: {filename}")
                        return ""
            
            # For other file types, return empty string
            else:
                logger.warning(f"[DOC_PROCESSING] Unsupported file type for text extraction: {filename}")
                return ""
                
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error extracting text from {filename}: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_content: bytes, filename: str) -> str:
        """Extract text from PDF using PyPDF2 or other PDF libraries."""
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                from io import BytesIO
                
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_content = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"[DOC_PROCESSING] Error extracting text from PDF page {page_num + 1}: {e}")
                
                if text_content.strip():
                    logger.info(f"[DOC_PROCESSING] Successfully extracted {len(text_content)} characters from PDF using PyPDF2: {filename}")
                    return text_content.strip()
                else:
                    logger.warning(f"[DOC_PROCESSING] PyPDF2 extracted no text from PDF: {filename}")
                    
            except ImportError:
                logger.warning("[DOC_PROCESSING] PyPDF2 not available, trying alternative methods")
            except Exception as e:
                logger.warning(f"[DOC_PROCESSING] PyPDF2 extraction failed: {e}")
            
            # Try pdfminer.six as fallback
            try:
                from pdfminer.high_level import extract_text_to_fp
                from pdfminer.layout import LAParams
                from io import StringIO
                
                output = StringIO()
                extract_text_to_fp(BytesIO(file_content), output, laparams=LAParams())
                text_content = output.getvalue()
                output.close()
                
                if text_content.strip():
                    logger.info(f"[DOC_PROCESSING] Successfully extracted {len(text_content)} characters from PDF using pdfminer: {filename}")
                    return text_content.strip()
                else:
                    logger.warning(f"[DOC_PROCESSING] pdfminer extracted no text from PDF: {filename}")
                    
            except ImportError:
                logger.warning("[DOC_PROCESSING] pdfminer.six not available")
            except Exception as e:
                logger.warning(f"[DOC_PROCESSING] pdfminer extraction failed: {e}")
            
            # If all local methods fail, log that AWS Textract should be used
            logger.error(f"[DOC_PROCESSING] All local PDF text extraction methods failed for: {filename}")
            logger.info(f"[DOC_PROCESSING] Consider using AWS Textract service for better PDF text extraction")
            return ""
            
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error in PDF text extraction for {filename}: {e}")
            return ""
    
    def _get_document_type(self, filename: str) -> str:
        """Get document type from filename extension."""
        try:
            import os
            _, ext = os.path.splitext(filename.lower())
            if ext in ['.pdf']:
                return 'pdf'
            elif ext in ['.txt', '.md']:
                return 'text'
            elif ext in ['.html', '.htm']:
                return 'html'
            elif ext in ['.doc', '.docx']:
                return 'document'
            else:
                return 'unknown'
        except Exception:
            return 'unknown'

    async def _extract_text_with_aws_textract(self, file_content: bytes, filename: str) -> str:
        """Extract text using AWS Textract if available and appropriate."""
        try:
            import os
            _, ext = os.path.splitext(filename.lower())
            
            # Only use AWS Textract for PDFs and images
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                logger.info(f"[DOC_PROCESSING] File type {ext} not suitable for AWS Textract, using local extraction")
                return ""
            
            # Check if we're in a Lambda environment or have AWS credentials
            is_lambda = (
                os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
                os.getenv('AWS_EXECUTION_ENV') or 
                os.getenv('LAMBDA_TASK_ROOT')
            )
            
            has_aws_creds = (
                os.getenv('AWS_ACCESS_KEY_ID') and 
                os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            if not is_lambda and not has_aws_creds:
                logger.info(f"[DOC_PROCESSING] Not in Lambda and no AWS credentials, using local extraction for: {filename}")
                return ""
            
            # Try to use AWS Textract
            try:
                from common.src.services.aws_textract_service import textract_service
                
                logger.info(f"[DOC_PROCESSING] Attempting AWS Textract extraction for: {filename}")
                
                # Upload to S3 temporarily for Textract processing
                from common.src.core.config import config
                import tempfile
                import uuid
                
                # Create temporary S3 key
                temp_key = f"temp_textract/{uuid.uuid4().hex}/{filename}"
                
                # Upload to S3
                import boto3
                s3_client = boto3.client('s3')
                s3_client.put_object(
                    Bucket=config.s3_bucket,
                    Key=temp_key,
                    Body=file_content
                )
                
                logger.info(f"[DOC_PROCESSING] Uploaded file to S3 for Textract processing: {temp_key}")
                
                # Process with Textract
                text_content, page_count = await textract_service.extract_text_from_s3_pdf(
                    s3_bucket=config.s3_bucket,
                    s3_key=temp_key,
                    document_type="general"
                )
                
                # Clean up temporary file
                try:
                    s3_client.delete_object(Bucket=config.s3_bucket, Key=temp_key)
                    logger.info(f"[DOC_PROCESSING] Cleaned up temporary S3 file: {temp_key}")
                except Exception as cleanup_error:
                    logger.warning(f"[DOC_PROCESSING] Failed to clean up temporary file: {cleanup_error}")
                
                if text_content and text_content.strip():
                    logger.info(f"[DOC_PROCESSING] Successfully extracted {len(text_content)} characters using AWS Textract: {filename}")
                    return text_content.strip()
                else:
                    logger.warning(f"[DOC_PROCESSING] AWS Textract returned no text for: {filename}")
                    return ""
                    
            except ImportError:
                logger.warning("[DOC_PROCESSING] AWS Textract service not available")
                return ""
            except Exception as e:
                logger.warning(f"[DOC_PROCESSING] AWS Textract extraction failed: {e}")
                return ""
                
        except Exception as e:
            logger.error(f"[DOC_PROCESSING] Error in AWS Textract extraction for {filename}: {e}")
            return ""

# Global instance
document_processing_service = DocumentProcessingService() 