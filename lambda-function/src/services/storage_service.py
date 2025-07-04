"""
Storage service for handling file uploads and downloads using MongoDB.
"""

import os
import logging
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any, List
from datetime import datetime
import uuid
import io

from src.core.config import config
from src.core.exceptions import StorageError
from src.core.database import mongodb

logger = logging.getLogger(__name__)

class StorageService:
    """Storage service for file management using MongoDB GridFS."""
    
    def __init__(self):
        self.storage_type = "mongodb"  # Always use MongoDB for Lambda
        self.s3_client = None
        
        # Debug logging
        logger.info(f"Storage type: {self.storage_type}")
        logger.info(f"S3 access key present: {bool(config.s3_access_key)}")
        logger.info(f"S3 secret key present: {bool(config.s3_secret_key)}")
        logger.info(f"S3 bucket: {config.s3_bucket}")
        logger.info(f"S3 region: {config.s3_region}")
        
        # Initialize S3 client if configured (for optional S3 backup)
        if config.s3_bucket:
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
        else:
            logger.warning("S3 client not available - missing bucket configuration")
        
        # Initialize GridFS (lazy initialization)
        self.gridfs = None
    
    def _init_gridfs(self):
        """Initialize GridFS for file storage."""
        if self.gridfs is not None:
            return
            
        try:
            from gridfs import GridFS
            if mongodb.db is None:
                logger.warning("MongoDB not connected yet, GridFS will be initialized when needed")
                return
            self.gridfs = GridFS(mongodb.db)
            logger.info("GridFS initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GridFS: {e}")
            # Don't raise error, just log it - GridFS will be retried when needed
    
    def save_file(self, file_content: BinaryIO, filename: str, 
                 folder: str = "uploads") -> str:
        """Save a file to MongoDB GridFS."""
        try:
            # Initialize GridFS if needed
            self._init_gridfs()
            if self.gridfs is None:
                raise StorageError("GridFS not available - MongoDB not connected")
                
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            unique_filename = f"{file_id}{file_extension}"
            
            # Read file content
            content = file_content.read()
            
            # Store in GridFS
            gridfs_id = self.gridfs.put(
                content,
                filename=unique_filename,
                folder=folder,
                original_filename=filename,
                upload_date=datetime.utcnow(),
                content_type=self._get_content_type(file_extension)
            )
            
            # Return MongoDB file ID as path
            file_path = f"mongodb://{gridfs_id}"
            
            logger.info(f"File saved to MongoDB: {file_path}")
            return file_path
                
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise StorageError(f"File save failed: {e}")
    
    def get_file(self, file_path: str) -> Optional[BinaryIO]:
        """Get a file from MongoDB GridFS."""
        try:
            if file_path.startswith("mongodb://"):
                return self._get_from_mongodb(file_path)
            elif file_path.startswith("s3://"):
                return self._get_from_s3(file_path)
            else:
                # Fallback to local file (for compatibility)
                return self._get_from_local(file_path)
        except Exception as e:
            logger.error(f"Failed to get file {file_path}: {e}")
            return None
    
    def _get_from_mongodb(self, file_path: str) -> Optional[BinaryIO]:
        """Get file from MongoDB GridFS."""
        try:
            # Initialize GridFS if needed
            self._init_gridfs()
            if self.gridfs is None:
                logger.error("GridFS not available - MongoDB not connected")
                return None
                
            # Extract file ID from mongodb://{id} format
            file_id = file_path.replace("mongodb://", "")
            
            # Get file from GridFS
            gridfs_file = self.gridfs.get(file_id)
            content = gridfs_file.read()
            
            # Return as file-like object
            return io.BytesIO(content)
        except Exception as e:
            logger.error(f"Failed to get file from MongoDB {file_path}: {e}")
            return None
    
    def _get_from_local(self, file_path: str) -> Optional[BinaryIO]:
        """Get file from local storage (fallback)."""
        path = Path(file_path)
        if path.exists():
            return open(path, 'rb')
        return None
    
    def _get_from_s3(self, s3_path: str) -> Optional[BinaryIO]:
        """Get file from S3 storage."""
        if not self.s3_client:
            return None
        
        # Parse s3://bucket/key format
        parts = s3_path.replace("s3://", "").split("/", 1)
        if len(parts) != 2:
            return None
        
        bucket, key = parts
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body']
        except Exception as e:
            logger.error(f"Failed to get file from S3 {s3_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            if file_path.startswith("mongodb://"):
                return self._delete_from_mongodb(file_path)
            elif file_path.startswith("s3://"):
                return self._delete_from_s3(file_path)
            else:
                return self._delete_from_local(file_path)
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def _delete_from_mongodb(self, file_path: str) -> bool:
        """Delete file from MongoDB GridFS."""
        try:
            # Initialize GridFS if needed
            self._init_gridfs()
            if self.gridfs is None:
                logger.error("GridFS not available - MongoDB not connected")
                return False
                
            file_id = file_path.replace("mongodb://", "")
            self.gridfs.delete(file_id)
            logger.info(f"File deleted from MongoDB: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from MongoDB {file_path}: {e}")
            return False
    
    def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage."""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def _delete_from_s3(self, s3_path: str) -> bool:
        """Delete file from S3 storage."""
        if not self.s3_client:
            return False
        
        # Parse s3://bucket/key format
        parts = s3_path.replace("s3://", "").split("/", 1)
        if len(parts) != 2:
            return False
        
        bucket, key = parts
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3 {s3_path}: {e}")
            return False
    
    def list_files(self, folder: str = "uploads", 
                  prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in a folder from MongoDB GridFS."""
        try:
            # Initialize GridFS if needed
            self._init_gridfs()
            if self.gridfs is None:
                logger.error("GridFS not available - MongoDB not connected")
                return []
                
            files = []
            
            # Query GridFS for files in the specified folder
            query = {"folder": folder}
            if prefix:
                query["filename"] = {"$regex": f"^{prefix}"}
            
            for gridfs_file in self.gridfs.find(query):
                files.append({
                    'name': gridfs_file.filename,
                    'path': f"mongodb://{gridfs_file._id}",
                    'size': gridfs_file.length,
                    'modified': gridfs_file.upload_date,
                    'content_type': getattr(gridfs_file, 'content_type', 'application/octet-stream')
                })
            
            return files
        except Exception as e:
            logger.error(f"Failed to list files in {folder}: {e}")
            return []
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information."""
        try:
            if file_path.startswith("mongodb://"):
                # Initialize GridFS if needed
                self._init_gridfs()
                if self.gridfs is None:
                    logger.error("GridFS not available - MongoDB not connected")
                    return None
                    
                file_id = file_path.replace("mongodb://", "")
                gridfs_file = self.gridfs.get(file_id)
                return {
                    'name': gridfs_file.filename,
                    'size': gridfs_file.length,
                    'modified': gridfs_file.upload_date,
                    'content_type': getattr(gridfs_file, 'content_type', 'application/octet-stream')
                }
            else:
                # Fallback for other storage types
                path = Path(file_path)
                if path.exists():
                    return {
                        'name': path.name,
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime)
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage configuration information."""
        return {
            'storage_type': self.storage_type,
            'mongodb_configured': True,
            's3_configured': self.s3_client is not None,
            's3_bucket': config.s3_bucket if self.s3_client else None
        }

    async def upload_file(self, file_path: str, s3_key: str) -> bool:
        """Upload a file from local path to S3 (optional backup)."""
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                return False
            
            # Ensure the file exists
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Upload to S3
            self.s3_client.upload_file(str(path), config.s3_bucket, s3_key)
            logger.info(f"Successfully uploaded {file_path} to S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to S3: {e}")
            return False
    
    async def get_file_content(self, file_path: str) -> Optional[bytes]:
        """Get file content as bytes."""
        try:
            if file_path.startswith("mongodb://"):
                # Initialize GridFS if needed
                self._init_gridfs()
                if self.gridfs is None:
                    logger.error("GridFS not available - MongoDB not connected")
                    return None
                    
                file_id = file_path.replace("mongodb://", "")
                gridfs_file = self.gridfs.get(file_id)
                return gridfs_file.read()
            elif file_path.startswith("s3://"):
                if not self.s3_client:
                    logger.warning("S3 client not available")
                    return None
                
                # Parse s3://bucket/key format
                parts = file_path.replace("s3://", "").split("/", 1)
                if len(parts) != 2:
                    return None
                
                bucket, key = parts
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                return response['Body'].read()
            else:
                # Assume it's an S3 key (no s3:// prefix)
                if self.s3_client and config.s3_bucket:
                    try:
                        response = self.s3_client.get_object(Bucket=config.s3_bucket, Key=file_path)
                        return response['Body'].read()
                    except Exception as s3_error:
                        logger.error(f"Failed to get file from S3 bucket {config.s3_bucket}, key {file_path}: {s3_error}")
                        return None
                else:
                    # Fallback to local file
                    path = Path(file_path)
                    if path.exists():
                        return path.read_bytes()
                    return None
            
        except Exception as e:
            logger.error(f"Failed to get file content from {file_path}: {e}")
            return None

    async def upload_file_from_bytes(self, file_content: bytes, s3_key: str, content_type: str = None) -> str:
        """Upload file content from bytes to S3 (optional backup)."""
        try:
            if not self.s3_client:
                logger.warning("S3 client not available")
                raise StorageError("S3 client not available")
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': config.s3_bucket,
                'Key': s3_key,
                'Body': file_content
            }
            
            # Add content type if provided
            if content_type:
                upload_params['ContentType'] = content_type
            
            # Upload to S3
            self.s3_client.put_object(**upload_params)
            logger.info(f"Successfully uploaded {len(file_content)} bytes to S3: {s3_key}")
            
            return s3_key
            
        except Exception as e:
            logger.error(f"Failed to upload file content to S3 {s3_key}: {e}")
            raise StorageError(f"Failed to upload file content: {e}")
    
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
        }
        return content_types.get(extension.lower(), 'application/octet-stream')

# Global storage service instance - lazy loaded
_storage_service_instance = None

def get_storage_service():
    """Get the global storage service instance (lazy loaded)."""
    global _storage_service_instance
    if _storage_service_instance is None:
        _storage_service_instance = StorageService()
    return _storage_service_instance 