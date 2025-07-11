"""
S3 Document Storage for crawled documents
Stores documents in S3 with structure: crawlchat-data/crawled_documents/user_id/task_id/
"""

import json
import logging
import os
import boto3
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class S3DocumentStorage:
    """S3-based document storage for crawled content."""
    
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize S3 document storage.
        
        Args:
            bucket_name: S3 bucket name (defaults to S3_BUCKET env var)
            region: AWS region (defaults to AWS_REGION env var)
        """
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET', 'crawlchat-data')
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client."""
        try:
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                logger.info("Initializing S3 client using IAM role")
                self.s3_client = boto3.client('s3', region_name=self.region)
            else:
                # Running locally - use default credential chain
                logger.info("Initializing S3 client using default credentials")
                self.s3_client = boto3.client('s3', region_name=self.region)
            
            logger.info(f"S3 document storage initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _generate_document_key(self, user_id: str, task_id: str, document_id: str, content_type: str = "html") -> str:
        """
        Generate S3 key for document storage.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            document_id: Document identifier
            content_type: Type of content (html, pdf, etc.)
            
        Returns:
            S3 object key
        """
        # Sanitize user_id and task_id for S3 key
        safe_user_id = self._sanitize_key(user_id)
        safe_task_id = self._sanitize_key(task_id)
        safe_document_id = self._sanitize_key(document_id)
        
        # Generate file extension based on content type
        extension = self._get_extension_for_content_type(content_type)
        
        return f"crawled_documents/{safe_user_id}/{safe_task_id}/{safe_document_id}{extension}"
    
    def _sanitize_key(self, key: str) -> str:
        """Sanitize string for use as S3 key."""
        # Replace problematic characters
        sanitized = key.replace('/', '_').replace('\\', '_').replace(' ', '_')
        sanitized = sanitized.replace(':', '_').replace('*', '_').replace('?', '_')
        sanitized = sanitized.replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        return sanitized
    
    def _get_extension_for_content_type(self, content_type: str) -> str:
        """Get file extension based on content type."""
        content_type = content_type.lower()
        
        if content_type == "html" or content_type == "text/html":
            return ".html"
        elif content_type == "application/pdf":
            return ".pdf"
        elif content_type == "application/msword" or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return ".docx"
        elif content_type == "application/vnd.ms-excel" or content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return ".xlsx"
        elif content_type == "application/vnd.ms-powerpoint" or content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return ".pptx"
        elif content_type == "text/csv":
            return ".csv"
        elif content_type == "application/json":
            return ".json"
        elif content_type == "text/plain":
            return ".txt"
        elif content_type.startswith("image/"):
            return ".jpg"  # Default image extension
        else:
            return ".bin"  # Binary file
    
    def _get_s3_content_type(self, content_type: str) -> str:
        """Get S3 content type based on content type."""
        content_type = content_type.lower()
        
        if content_type == "html" or content_type == "text/html":
            return "text/html"
        elif content_type == "application/pdf":
            return "application/pdf"
        elif content_type == "application/msword" or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif content_type == "application/vnd.ms-excel" or content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif content_type == "application/vnd.ms-powerpoint" or content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif content_type == "text/csv":
            return "text/csv"
        elif content_type == "application/json":
            return "application/json"
        elif content_type == "text/plain":
            return "text/plain"
        elif content_type.startswith("image/"):
            return content_type  # Keep original image content type
        else:
            return "application/octet-stream"  # Binary file
    
    def store_document(self, user_id: str, task_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a document in S3.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            document: Document object with content and metadata
            
        Returns:
            Dictionary with storage results
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping document storage")
            return {
                "success": False,
                "error": "S3 client not available",
                "s3_url": None
            }
        
        try:
            document_id = document.get("id", f"doc_{hashlib.md5(document.get('url', '').encode()).hexdigest()[:8]}")
            content_type = document.get("content_type", "html")
            
            # Generate S3 key for the actual content file
            s3_key = self._generate_document_key(user_id, task_id, document_id, content_type)
            
            # Generate S3 key for metadata file
            metadata_key = self._generate_document_key(user_id, task_id, document_id, "json").replace(".json", "_metadata.json")
            
            # Prepare content for storage
            content = document.get("content", "")
            raw_html = document.get("raw_html", "")
            
            # Create metadata object
            metadata_object = {
                "document_id": document_id,
                "url": document.get("url", ""),
                "title": document.get("title", ""),
                "content_type": content_type,
                "content_length": document.get("content_length", 0),
                "raw_content_length": document.get("raw_content_length", 0),
                "crawl_time": document.get("crawl_time", 0),
                "status_code": document.get("status_code", 0),
                "headers": document.get("headers", {}),
                "extracted_at": document.get("extracted_at", datetime.utcnow().isoformat()),
                "domain": document.get("domain", ""),
                "filename": document.get("filename", ""),
                "stored_at": datetime.utcnow().isoformat(),
                "s3_key": s3_key,
                "metadata_key": metadata_key,
                "user_id": user_id,
                "task_id": task_id
            }
            
            # Store the actual content file
            content_to_store = content
            s3_content_type = self._get_s3_content_type(content_type)
            
            # For HTML content, use the raw HTML if available
            if content_type == "html" and raw_html:
                content_to_store = raw_html
                s3_content_type = "text/html"
            
            # Handle binary content (PDFs, images, etc.)
            if document.get("is_binary", False) and document.get("content_base64"):
                # Convert base64 back to binary for storage
                try:
                    binary_content = base64.b64decode(document["content_base64"])
                    content_to_store = binary_content
                    logger.info(f"Storing binary content: {len(binary_content)} bytes")
                except Exception as e:
                    logger.error(f"Failed to decode base64 content: {e}")
                    # Fallback to text content
                    content_to_store = content
            
            # Prepare body for S3 upload
            if isinstance(content_to_store, str):
                body = content_to_store.encode('utf-8')
            elif isinstance(content_to_store, bytes):
                body = content_to_store
            else:
                body = str(content_to_store).encode('utf-8')
            
            # Upload content file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=body,
                ContentType=s3_content_type,
                Metadata={
                    'document_id': document_id,
                    'user_id': user_id,
                    'task_id': task_id,
                    'content_type': content_type,
                    'stored_at': metadata_object['stored_at']
                }
            )
            
            # Store metadata file
            json_metadata = json.dumps(metadata_object, indent=2, ensure_ascii=False)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json_metadata.encode('utf-8'),
                ContentType="application/json",
                Metadata={
                    'document_id': document_id,
                    'user_id': user_id,
                    'task_id': task_id,
                    'content_type': 'metadata',
                    'stored_at': metadata_object['stored_at']
                }
            )
            
            # Generate S3 URL
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            
            logger.info(f"Document stored in S3: {s3_url}")
            
            return {
                "success": True,
                "s3_url": s3_url,
                "s3_key": s3_key,
                "metadata_key": metadata_key,
                "document_id": document_id,
                "content_type": content_type,
                "size": len(body),
                "metadata_size": len(json_metadata)
            }
            
        except Exception as e:
            logger.error(f"Failed to store document in S3: {e}")
            return {
                "success": False,
                "error": str(e),
                "s3_url": None
            }
    
    def store_documents_batch(self, user_id: str, task_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store multiple documents in S3.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            documents: List of document objects
            
        Returns:
            Dictionary with batch storage results
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping batch document storage")
            return {
                "success": False,
                "error": "S3 client not available",
                "stored_count": 0,
                "failed_count": len(documents),
                "results": []
            }
        
        results = []
        stored_count = 0
        failed_count = 0
        
        for document in documents:
            result = self.store_document(user_id, task_id, document)
            results.append(result)
            
            if result["success"]:
                stored_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch storage completed: {stored_count} stored, {failed_count} failed")
        
        return {
            "success": stored_count > 0,
            "stored_count": stored_count,
            "failed_count": failed_count,
            "total_count": len(documents),
            "results": results
        }
    
    def get_document(self, user_id: str, task_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from S3.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            document_id: Document identifier
            
        Returns:
            Document object or None if not found
        """
        if not self.s3_client:
            logger.warning("S3 client not available, cannot retrieve document")
            return None
        
        try:
            # First, try to get the metadata file
            metadata_key = self._generate_document_key(user_id, task_id, document_id, "json").replace(".json", "_metadata.json")
            
            try:
                metadata_response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=metadata_key
                )
                
                # Parse metadata
                metadata_content = metadata_response['Body'].read().decode('utf-8')
                metadata = json.loads(metadata_content)
                
                # Get the content file
                content_type = metadata.get("content_type", "html")
                s3_key = self._generate_document_key(user_id, task_id, document_id, content_type)
                
                content_response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                # Read content
                content = content_response['Body'].read()
                
                # For text content, decode as UTF-8
                if content_type in ["html", "text/html", "text/plain", "text/csv", "application/json"]:
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # If UTF-8 fails, try other encodings
                        try:
                            content = content.decode('latin-1')
                        except:
                            # Keep as bytes if all decoding fails
                            pass
                
                # Combine metadata and content
                document = metadata.copy()
                document["content"] = content
                
                # Add raw_html if it's HTML content
                if content_type == "html" and isinstance(content, str):
                    document["raw_html"] = content
                
                logger.info(f"Document retrieved from S3: s3://{self.bucket_name}/{s3_key}")
                return document
                
            except self.s3_client.exceptions.NoSuchKey:
                logger.info(f"Metadata file not found: {metadata_key}")
                # Fallback: try to find the document directly
                return self._get_document_fallback(user_id, task_id, document_id)
            
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
            return None
    
    def _get_document_fallback(self, user_id: str, task_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Fallback method to retrieve document without metadata."""
        try:
            # Try different content types to find the document
            content_types = ["html", "pdf", "docx", "xlsx", "pptx", "csv", "json", "txt"]
            
            for content_type in content_types:
                s3_key = self._generate_document_key(user_id, task_id, document_id, content_type)
                
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    # Read content
                    content = response['Body'].read()
                    
                    # For text content, decode as UTF-8
                    if content_type in ["html", "text/html", "text/plain", "text/csv", "application/json"]:
                        try:
                            content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            # If UTF-8 fails, try other encodings
                            try:
                                content = content.decode('latin-1')
                            except:
                                # Keep as bytes if all decoding fails
                                pass
                    
                    # Create basic document object
                    document = {
                        "document_id": document_id,
                        "content": content,
                        "content_type": content_type,
                        "s3_key": s3_key,
                        "user_id": user_id,
                        "task_id": task_id
                    }
                    
                    logger.info(f"Document retrieved from S3 (fallback): s3://{self.bucket_name}/{s3_key}")
                    return document
                    
                except self.s3_client.exceptions.NoSuchKey:
                    continue
                except Exception as e:
                    logger.warning(f"Error retrieving document with content type {content_type}: {e}")
                    continue
            
            logger.info(f"Document not found: {document_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve document (fallback): {e}")
            return None
    
    def list_documents(self, user_id: str, task_id: str) -> List[Dict[str, Any]]:
        """
        List all documents for a specific task.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            
        Returns:
            List of document metadata
        """
        if not self.s3_client:
            logger.warning("S3 client not available, cannot list documents")
            return []
        
        try:
            safe_user_id = self._sanitize_key(user_id)
            safe_task_id = self._sanitize_key(task_id)
            prefix = f"crawled_documents/{safe_user_id}/{safe_task_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            documents = []
            metadata_files = {}
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Skip metadata files for now, collect them separately
                if key.endswith('_metadata.json'):
                    try:
                        # Get metadata file content
                        metadata_response = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=key
                        )
                        metadata_content = metadata_response['Body'].read().decode('utf-8')
                        metadata = json.loads(metadata_content)
                        
                        document_id = metadata.get('document_id', '')
                        metadata_files[document_id] = metadata
                        
                    except Exception as e:
                        logger.warning(f"Error reading metadata file {key}: {e}")
                        continue
                
                # Process content files
                elif not key.endswith('_metadata.json'):
                    try:
                        # Get object metadata
                        obj_response = self.s3_client.head_object(
                            Bucket=self.bucket_name,
                            Key=key
                        )
                        
                        s3_metadata = obj_response.get('Metadata', {})
                        document_id = s3_metadata.get('document_id', '')
                        
                        # Get corresponding metadata if available
                        metadata = metadata_files.get(document_id, {})
                        
                        documents.append({
                            "s3_key": key,
                            "s3_url": f"s3://{self.bucket_name}/{key}",
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "document_id": document_id,
                            "content_type": s3_metadata.get('content_type', ''),
                            "stored_at": s3_metadata.get('stored_at', ''),
                            "title": metadata.get('title', ''),
                            "url": metadata.get('url', ''),
                            "domain": metadata.get('domain', '')
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error getting metadata for {key}: {e}")
                        continue
            
            logger.info(f"Found {len(documents)} documents for task {task_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    def delete_documents(self, user_id: str, task_id: str) -> bool:
        """
        Delete all documents for a specific task.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            logger.warning("S3 client not available, cannot delete documents")
            return False
        
        try:
            safe_user_id = self._sanitize_key(user_id)
            safe_task_id = self._sanitize_key(task_id)
            prefix = f"crawled_documents/{safe_user_id}/{safe_task_id}/"
            
            # List all objects with the prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.info(f"No documents found to delete for task {task_id}")
                return True
            
            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f"Deleted {len(objects_to_delete)} documents for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False 