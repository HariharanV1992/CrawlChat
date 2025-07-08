"""
Unified Storage Service
Centralized service for all file storage operations including S3 uploads, downloads, and management.
Handles both uploaded documents and crawled content with consistent naming and organization.
"""

import logging
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import io

from common.src.core.config import config
from common.src.core.aws_config import aws_config
from common.src.core.exceptions import StorageError

logger = logging.getLogger(__name__)

class UnifiedStorageService:
    """
    Unified service for all file storage operations.
    Provides consistent S3 upload, download, and management for all document types.
    """
    
    def __init__(self):
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client with proper configuration."""
        try:
            import boto3
            
            # Check if we're running in Lambda (use IAM role) or local (use credentials)
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                logger.info("Running in Lambda environment, using IAM role for S3")
                self.s3_client = boto3.client('s3', region_name=config.s3_region)
            else:
                # Running locally - use credentials if available
                if config.s3_access_key and config.s3_secret_key:
                    logger.info("Running locally, using provided S3 credentials")
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=config.s3_access_key,
                        aws_secret_access_key=config.s3_secret_key,
                        region_name=config.s3_region
                    )
                else:
                    logger.warning("S3 client not available - missing credentials for local environment")
                    self.s3_client = None
            
            if self.s3_client:
                logger.info("S3 client initialized successfully")
                
        except ImportError:
            logger.warning("boto3 not installed, S3 storage disabled")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    async def upload_user_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a user document to S3 with consistent naming and organization.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User ID for organization
            content_type: Optional content type
            
        Returns:
            Upload result with S3 key and metadata
        """
        try:
            if not self.s3_client:
                raise StorageError("S3 client not available")
            
            # Generate unique S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = str(uuid.uuid4())[:8]
            file_extension = Path(filename).suffix
            s3_key = f"uploaded_documents/{user_id}/{timestamp}_{unique_id}{file_extension}"
            
            # Determine content type if not provided
            if not content_type:
                content_type = self._get_content_type(file_extension)
            
            # Calculate file hash for integrity
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Upload to S3
            upload_params = {
                'Bucket': config.s3_bucket,
                'Key': s3_key,
                'Body': file_content,
                'ContentType': content_type,
                'Metadata': {
                    'original_filename': filename,
                    'user_id': user_id,
                    'upload_timestamp': str(timestamp),
                    'file_hash': file_hash,
                    'file_size': str(len(file_content))
                }
            }
            
            self.s3_client.put_object(**upload_params)
            
            logger.info(f"[UNIFIED_STORAGE] Uploaded user document: {filename} -> {s3_key}")
            
            return {
                "s3_key": s3_key,
                "filename": filename,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "content_type": content_type,
                "upload_timestamp": timestamp,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error uploading user document {filename}: {e}")
            raise StorageError(f"Failed to upload user document: {e}")
    
    async def upload_crawled_content(
        self,
        content: str,
        filename: str,
        task_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload crawled content to S3 with consistent organization.
        
        Args:
            content: Text content
            filename: Generated filename
            task_id: Crawl task ID
            user_id: User ID
            metadata: Additional metadata
            
        Returns:
            Upload result with S3 key and metadata
        """
        try:
            if not self.s3_client:
                raise StorageError("S3 client not available")
            
            # Convert content to bytes
            content_bytes = content.encode('utf-8')
            
            # Generate S3 key for crawled content
            s3_key = f"crawled_documents/{task_id}/{filename}"
            
            # Prepare metadata
            upload_metadata = {
                'original_filename': filename,
                'user_id': user_id,
                'task_id': task_id,
                'content_type': 'text/plain',
                'upload_timestamp': str(int(datetime.utcnow().timestamp())),
                'file_hash': hashlib.md5(content_bytes).hexdigest(),
                'file_size': str(len(content_bytes)),
                'source': 'crawler'
            }
            
            # Add custom metadata if provided
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=config.s3_bucket,
                Key=s3_key,
                Body=content_bytes,
                ContentType='text/plain',
                Metadata=upload_metadata
            )
            
            logger.info(f"[UNIFIED_STORAGE] Uploaded crawled content: {filename} -> {s3_key}")
            
            return {
                "s3_key": s3_key,
                "filename": filename,
                "file_size": len(content_bytes),
                "file_hash": upload_metadata['file_hash'],
                "content_type": 'text/plain',
                "task_id": task_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error uploading crawled content {filename}: {e}")
            raise StorageError(f"Failed to upload crawled content: {e}")
    
    async def upload_temp_file(
        self,
        file_content: bytes,
        filename: str,
        purpose: str = "temp",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a temporary file for processing (e.g., for Textract).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            purpose: Purpose of the temporary file
            user_id: Optional user ID
            
        Returns:
            Upload result with S3 key
        """
        try:
            if not self.s3_client:
                raise StorageError("S3 client not available")
            
            # Generate temporary S3 key
            unique_id = str(uuid.uuid4())
            s3_key = f"temp_files/{purpose}/{unique_id}/{filename}"
            
            # Determine content type
            file_extension = Path(filename).suffix
            content_type = self._get_content_type(file_extension)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=config.s3_bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'purpose': purpose,
                    'user_id': user_id or 'anonymous',
                    'upload_timestamp': str(int(datetime.utcnow().timestamp())),
                    'temp_file': 'true'
                }
            )
            
            logger.info(f"[UNIFIED_STORAGE] Uploaded temp file: {filename} -> {s3_key}")
            
            return {
                "s3_key": s3_key,
                "filename": filename,
                "content_type": content_type,
                "purpose": purpose
            }
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error uploading temp file {filename}: {e}")
            raise StorageError(f"Failed to upload temp file: {e}")
    
    async def get_file_content(self, s3_key: str) -> Optional[bytes]:
        """
        Get file content from S3.
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            File content as bytes or None if not found
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return None
            
            response = self.s3_client.get_object(Bucket=config.s3_bucket, Key=s3_key)
            content = response['Body'].read()
            
            logger.info(f"[UNIFIED_STORAGE] Retrieved file content: {s3_key} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error getting file content {s3_key}: {e}")
            return None
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 key of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return False
            
            self.s3_client.delete_object(Bucket=config.s3_bucket, Key=s3_key)
            logger.info(f"[UNIFIED_STORAGE] Deleted file: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error deleting file {s3_key}: {e}")
            return False
    
    async def list_user_files(self, user_id: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files for a specific user.
        
        Args:
            user_id: User ID
            prefix: Optional prefix filter
            
        Returns:
            List of file information
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return []
            
            # Build prefix for user files
            user_prefix = f"uploaded_documents/{user_id}/"
            if prefix:
                user_prefix += prefix
            
            response = self.s3_client.list_objects_v2(
                Bucket=config.s3_bucket,
                Prefix=user_prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    's3_key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'filename': Path(obj['Key']).name
                })
            
            logger.info(f"[UNIFIED_STORAGE] Listed {len(files)} files for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error listing files for user {user_id}: {e}")
            return []
    
    async def list_task_files(self, task_id: str) -> List[Dict[str, Any]]:
        """
        List files for a specific crawl task.
        
        Args:
            task_id: Crawl task ID
            
        Returns:
            List of file information
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return []
            
            task_prefix = f"crawled_documents/{task_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=config.s3_bucket,
                Prefix=task_prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    's3_key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'filename': Path(obj['Key']).name
                })
            
            logger.info(f"[UNIFIED_STORAGE] Listed {len(files)} files for task {task_id}")
            return files
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error listing files for task {task_id}: {e}")
            return []
    
    async def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.
        
        Args:
            older_than_hours: Age threshold in hours
            
        Returns:
            Number of files deleted
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return 0
            
            cutoff_time = datetime.utcnow().timestamp() - (older_than_hours * 3600)
            
            response = self.s3_client.list_objects_v2(
                Bucket=config.s3_bucket,
                Prefix="temp_files/"
            )
            
            deleted_count = 0
            for obj in response.get('Contents', []):
                # Check if file is older than cutoff
                if obj['LastModified'].timestamp() < cutoff_time:
                    try:
                        self.s3_client.delete_object(Bucket=config.s3_bucket, Key=obj['Key'])
                        deleted_count += 1
                        logger.info(f"[UNIFIED_STORAGE] Cleaned up temp file: {obj['Key']}")
                    except Exception as e:
                        logger.error(f"[UNIFIED_STORAGE] Error deleting temp file {obj['Key']}: {e}")
            
            logger.info(f"[UNIFIED_STORAGE] Cleaned up {deleted_count} temp files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"[UNIFIED_STORAGE] Error cleaning up temp files: {e}")
            return 0
    
    def _get_content_type(self, extension: str) -> str:
        """Get content type from file extension."""
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff'
        }
        return content_types.get(extension.lower(), 'application/octet-stream')
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage configuration information."""
        return {
            's3_configured': self.s3_client is not None,
            's3_bucket': config.s3_bucket if self.s3_client else None,
            's3_region': config.s3_region,
            'storage_type': 's3'
        }

# Global instance
unified_storage_service = UnifiedStorageService() 