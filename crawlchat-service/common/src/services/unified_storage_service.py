"""
Simplified Unified Storage Service
Handles S3 uploads, downloads, and deletes for user and temp files only.
"""

import logging
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from common.src.core.config import config
from common.src.core.aws_config import aws_config
from common.src.core.exceptions import StorageError

logger = logging.getLogger(__name__)

class UnifiedStorageService:
    def __init__(self):
        self.s3_client = self._init_s3_client()

    def _init_s3_client(self):
        try:
            import boto3
            from common.src.core.aws_config import aws_config
            
            # Use AWS config which handles both Lambda IAM roles and explicit credentials
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # In Lambda, use IAM role - no explicit credentials needed
                logger.info("Initializing S3 client for Lambda environment")
                return boto3.client('s3', region_name=aws_config.region)
            else:
                # For local development, try explicit credentials first
                access_key = aws_config.access_key_id
                secret_key = aws_config.secret_access_key
                
                if access_key and secret_key:
                    logger.info("Initializing S3 client with explicit credentials")
                    return boto3.client(
                        's3',
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=aws_config.region
                    )
                else:
                    # Fall back to boto3 default credential chain
                    logger.info("Initializing S3 client with boto3 default credential chain")
                    return boto3.client('s3', region_name=aws_config.region)
                    
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None

    async def upload_user_document(self, file_content: bytes, filename: str, user_id: str, content_type: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.s3_client:
            raise StorageError("S3 client not available")
        
        # Validate input
        if not file_content or len(file_content) == 0:
            raise StorageError("File content is empty")
        
        if not filename:
            raise StorageError("Filename is required")
        
        if not user_id:
            raise StorageError("User ID is required")
        
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(filename).suffix
        
        # Generate S3 key
        if task_id:
            s3_key = f"uploaded_documents/{user_id}/{task_id}/{timestamp}_{unique_id}{file_extension}"
        else:
            s3_key = f"uploaded_documents/{user_id}/{timestamp}_{unique_id}{file_extension}"
        
        # Determine content type
        content_type = content_type or self._get_content_type(file_extension)
        
        # Enhanced logging for debugging
        logger.info(f"[STORAGE] Uploading file: {filename}")
        logger.info(f"[STORAGE] File size: {len(file_content):,} bytes")
        logger.info(f"[STORAGE] Content type: {content_type}")
        logger.info(f"[STORAGE] S3 key: {s3_key}")
        logger.info(f"[STORAGE] File MD5: {hashlib.md5(file_content).hexdigest()}")
        
        # Validate PDF files
        if filename.lower().endswith('.pdf'):
            if not file_content.startswith(b'%PDF-'):
                logger.error(f"[STORAGE] Invalid PDF header: {file_content[:10]}")
                raise StorageError("Invalid PDF file - missing PDF header")
            
            if b'%%EOF' not in file_content[-1000:]:
                logger.warning(f"[STORAGE] PDF EOF marker not found in last 1000 bytes")
            
            logger.info(f"[STORAGE] PDF validation passed")
        
        try:
            # Prepare body for S3 upload (using crawler service method)
            if isinstance(file_content, str):
                body = file_content.encode('utf-8')
            elif isinstance(file_content, bytes):
                body = file_content
            else:
                body = str(file_content).encode('utf-8')
            
            logger.info(f"[STORAGE] Final body type: {type(body)}, length: {len(body)}")
            
            # Upload to S3 with proper metadata (using crawler service approach)
            response = self.s3_client.put_object(
                Bucket=aws_config.s3_bucket,
                Key=s3_key,
                Body=body,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'user_id': user_id,
                    'task_id': task_id or 'no_task',
                    'upload_timestamp': str(timestamp),
                    'file_size': str(len(file_content)),
                    'content_md5': hashlib.md5(file_content).hexdigest()
                }
            )
            
            # Verify upload was successful
            if not response.get('ETag'):
                raise StorageError("S3 upload failed - no ETag returned")
            
            logger.info(f"[STORAGE] Successfully uploaded: s3://{aws_config.s3_bucket}/{s3_key}")
            logger.info(f"[STORAGE] S3 ETag: {response.get('ETag')}")
            
            return {
                "s3_key": s3_key, 
                "filename": filename, 
                "file_size": len(file_content),
                "etag": response.get('ETag'),
                "bucket": aws_config.s3_bucket
            }
            
        except Exception as e:
            logger.error(f"[STORAGE] Error uploading user document: {e}")
            raise StorageError(f"Failed to upload user document: {e}")

    async def upload_temp_file(self, file_content: bytes, filename: str, purpose: str = "temp", user_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.s3_client:
            raise StorageError("S3 client not available")
        unique_id = str(uuid.uuid4())
        s3_key = f"temp_files/{purpose}/{unique_id}/{filename}"
        file_extension = Path(filename).suffix
        content_type = self._get_content_type(file_extension)
        try:
            self.s3_client.put_object(
                Bucket=aws_config.s3_bucket,
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
            logger.info(f"Uploaded temp file: s3://{aws_config.s3_bucket}/{s3_key}")
            return {"s3_key": s3_key, "filename": filename, "file_size": len(file_content)}
        except Exception as e:
            logger.error(f"Error uploading temp file: {e}")
            raise StorageError(f"Failed to upload temp file: {e}")

    async def get_file_content(self, s3_key: str) -> Optional[bytes]:
        if not self.s3_client:
            logger.error("S3 client not available")
            return None
        try:
            response = self.s3_client.get_object(Bucket=aws_config.s3_bucket, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None

    async def delete_file(self, s3_key: str) -> bool:
        if not self.s3_client:
            logger.error("S3 client not available")
            return False
        try:
            self.s3_client.delete_object(Bucket=aws_config.s3_bucket, Key=s3_key)
            logger.info(f"Deleted file: s3://{aws_config.s3_bucket}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def _get_content_type(self, extension: str) -> str:
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

# Global instance
unified_storage_service = UnifiedStorageService() 