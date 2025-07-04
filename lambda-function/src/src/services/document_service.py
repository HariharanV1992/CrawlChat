"""
Document service for handling document processing and management.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from src.models.documents import (
    Document, DocumentType, DocumentStatus, DocumentUpload, 
    DocumentProcess, DocumentProcessResponse, DocumentList
)
from src.core.config import config
from src.core.exceptions import DocumentProcessingError, StorageError
from src.services.storage_service import get_storage_service
from src.core.database import mongodb

logger = logging.getLogger(__name__)

class DocumentService:
    """Document service for managing document processing and storage using MongoDB."""
    
    def __init__(self):
        pass
    
    async def upload_document(self, upload_data: DocumentUpload) -> Document:
        """Upload and store a document."""
        try:
            document_id = str(uuid.uuid4())
            
            # Determine document type
            extension = Path(upload_data.filename).suffix.lower()
            document_type = self._get_document_type(extension)
            
            # Save file to MongoDB GridFS
            storage_service = get_storage_service()
            
            # Create file-like object from bytes
            import io
            file_content = io.BytesIO(upload_data.content)
            
            # Save to MongoDB GridFS
            file_path = storage_service.save_file(file_content, upload_data.filename, "uploads")
            
            # Get file info
            file_info = storage_service.get_file_info(file_path)
            
            # Create document record
            document = Document(
                document_id=document_id,
                user_id=upload_data.user_id,
                filename=upload_data.filename,
                file_path=str(file_path),
                file_size=file_info['size'] if file_info else len(upload_data.content),
                document_type=document_type,
                status=DocumentStatus.UPLOADED,
                uploaded_at=datetime.utcnow(),
                task_id=upload_data.task_id
            )
            
            await mongodb.get_collection("documents").insert_one(document.dict())
            
            logger.info(f"Uploaded document {document_id}: {upload_data.filename}")
            return document
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise DocumentProcessingError(f"Failed to upload document: {e}")
    
    async def process_document(self, document_path: str, user_query: Optional[str] = None) -> DocumentProcessResponse:
        """Process a document and extract content."""
        try:
            start_time = datetime.utcnow()
            
            # Find document by path or document_id
            # For uploaded documents, document_path is actually the S3 key
            # For crawl documents, document_path is the file_path
            doc = None
            if document_path.startswith('uploaded_documents/'):
                # This is an uploaded document, find by file_path (S3 key)
                doc = await mongodb.get_collection("documents").find_one({"file_path": document_path})
            else:
                # This is a crawl document, find by file_path
                doc = await mongodb.get_collection("documents").find_one({"file_path": document_path})
            
            if not doc:
                raise DocumentProcessingError("Document not found")
            document = Document(**doc)
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await mongodb.get_collection("documents").update_one({"document_id": document.document_id}, {"$set": {"status": DocumentStatus.PROCESSING}})
            
            # Extract content based on document type
            content = await self._extract_content(document)
            
            # Generate summary and key points
            summary = await self._generate_summary(content, user_query)
            key_points = await self._extract_key_points(content)
            
            # Update document
            document.content = content
            document.summary = summary
            document.key_points = key_points
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.utcnow()
            await mongodb.get_collection("documents").update_one(
                {"document_id": document.document_id},
                {"$set": {
                    "content": content,
                    "summary": summary,
                    "key_points": key_points,
                    "status": DocumentStatus.PROCESSED,
                    "processed_at": document.processed_at
                }}
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Processed document {document.document_id} in {processing_time:.2f}s")
            
            return DocumentProcessResponse(
                document_id=document.document_id,
                status=DocumentStatus.PROCESSED,
                content=content,
                summary=summary,
                key_points=key_points,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
    
    async def _extract_content(self, document: Document) -> str:
        """Extract content from document based on type."""
        try:
            storage_service = get_storage_service()
            
            if document.document_type == DocumentType.TXT:
                content = await storage_service.get_file_content(document.file_path)
                return content.decode('utf-8') if content else ""
            
            elif document.document_type == DocumentType.HTML:
                content = await storage_service.get_file_content(document.file_path)
                return content.decode('utf-8') if content else ""
            
            elif document.document_type == DocumentType.PDF:
                # Extract text from PDF
                content = await storage_service.get_file_content(document.file_path)
                if not content:
                    return f"Could not read PDF file: {document.filename}"
                
                try:
                    import io
                    import PyPDF2
                    
                    # Create a file-like object from bytes
                    pdf_file = io.BytesIO(content)
                    
                    # Extract text from PDF
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = ""
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text_content += page.extract_text() + "\n"
                    
                    if not text_content.strip():
                        return f"PDF appears to be empty or contains only images: {document.filename}"
                    
                    logger.info(f"Successfully extracted {len(text_content)} characters from PDF: {document.filename}")
                    logger.info(f"PDF content preview: {text_content[:500].replace(chr(10), ' ').replace(chr(13), ' ')}")
                    return text_content
                    
                except ImportError:
                    logger.error("PyPDF2 not installed. Please install it with: pip install PyPDF2")
                    return f"PDF processing requires PyPDF2 library. Please install it and try again."
                except Exception as e:
                    logger.error(f"Error extracting PDF text from {document.filename}: {e}")
                    return f"Error extracting PDF content: {e}"
            
            else:
                return f"Content extraction not implemented for {document.document_type}"
                
        except Exception as e:
            logger.error(f"Error extracting content from {document.filename}: {e}")
            return f"Error extracting content: {e}"
    
    async def _generate_summary(self, content: str, user_query: Optional[str] = None) -> str:
        """Generate summary of document content."""
        if user_query:
            return f"Summary based on query '{user_query}': {content[:200]}..."
        else:
            return f"Document summary: {content[:200]}..."
    
    async def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from document content."""
        return [
            "Key point 1 (placeholder)",
            "Key point 2 (placeholder)",
            "Key point 3 (placeholder)"
        ]
    
    def _get_document_type(self, extension: str) -> DocumentType:
        """Get document type from file extension. Unsupported types are mapped to TXT."""
        extension_map = {
            '.pdf': DocumentType.PDF,
            '.doc': DocumentType.DOC,
            '.docx': DocumentType.DOCX,
            '.txt': DocumentType.TXT,
            '.html': DocumentType.HTML,
            # Map unsupported types to TXT
            '.xlsx': DocumentType.TXT,
            '.xls': DocumentType.TXT,
            '.csv': DocumentType.TXT,
            '.ppt': DocumentType.TXT,
            '.pptx': DocumentType.TXT,
            '.json': DocumentType.TXT,
        }
        return extension_map.get(extension.lower(), DocumentType.TXT)
    
    async def get_document(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get a document by ID."""
        doc = await mongodb.get_collection("documents").find_one({"document_id": document_id, "user_id": user_id})
        if doc:
            return Document(**doc)
        return None
    
    async def list_user_documents(self, user_id: str, limit: int = 50, 
                                skip: int = 0) -> DocumentList:
        """List documents for a user."""
        cursor = mongodb.get_collection("documents").find({"user_id": user_id}).skip(skip).limit(limit)
        docs = [Document(**doc) async for doc in cursor]
        total_count = await mongodb.get_collection("documents").count_documents({"user_id": user_id})
        return DocumentList(documents=docs, total_count=total_count)
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document."""
        try:
            # First get the document to find the file path
            doc = await mongodb.get_collection("documents").find_one({"document_id": document_id, "user_id": user_id})
            if not doc:
                return False
            
            document = Document(**doc)
            
            # Delete the actual file from storage
            try:
                storage_service = get_storage_service()
                storage_service.delete_file(document.file_path)
                logger.info(f"Deleted file from storage: {document.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file from storage {document.file_path}: {e}")
            
            # Delete from database
            result = await mongodb.get_collection("documents").delete_one({"document_id": document_id, "user_id": user_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def delete_document_by_filename(self, filename: str, user_id: str) -> bool:
        """Delete a document by filename."""
        try:
            # Find document by filename and user_id
            doc = await mongodb.get_collection("documents").find_one({"filename": filename, "user_id": user_id})
            if not doc:
                return False
            
            document = Document(**doc)
            
            # Delete the actual file from storage
            try:
                storage_service = get_storage_service()
                storage_service.delete_file(document.file_path)
                logger.info(f"Deleted file from storage: {document.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file from storage {document.file_path}: {e}")
            
            # Delete from database
            result = await mongodb.get_collection("documents").delete_one({"document_id": document.document_id, "user_id": user_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document by filename {filename}: {e}")
            return False
    
    async def get_task_documents(self, task_id: str) -> List[Document]:
        """Get documents for a specific task."""
        try:
            # First try to get documents from the documents collection (for uploaded documents)
            cursor = mongodb.get_collection("documents").find({"task_id": task_id})
            documents = [Document(**doc) async for doc in cursor]
            
            if documents:
                return documents
            
            # If no documents found in documents collection, try crawl_tasks collection
            crawl_task = await mongodb.get_collection("crawl_tasks").find_one({"task_id": task_id})
            if crawl_task and crawl_task.get("documents"):
                # Convert crawl task documents to Document objects
                documents = []
                for doc_data in crawl_task["documents"]:
                    # Create a Document object from crawl task document data
                    document = Document(
                        document_id=doc_data.get("document_id", str(uuid.uuid4())),
                        user_id=crawl_task.get("user_id", ""),
                        filename=doc_data.get("filename", ""),
                        file_path=doc_data.get("file_path", ""),
                        file_size=doc_data.get("file_size", 0),
                        document_type=self._get_document_type(Path(doc_data.get("filename", "")).suffix),
                        status=DocumentStatus.PROCESSED,  # Crawl documents are already processed
                        uploaded_at=doc_data.get("uploaded_at", datetime.utcnow()),
                        task_id=task_id,
                        crawl_task_id=task_id  # Add crawl task ID for reference
                    )
                    documents.append(document)
                
                return documents
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting task documents for {task_id}: {e}")
            return []
    
    async def create_document(self, document: Document) -> Document:
        """Create a new document record in the database."""
        try:
            await mongodb.get_collection("documents").insert_one(document.dict())
            logger.info(f"Created document record: {document.document_id}")
            return document
        except Exception as e:
            logger.error(f"Error creating document record: {e}")
            raise DocumentProcessingError(f"Failed to create document record: {e}")

# Global document service instance
document_service = DocumentService() 