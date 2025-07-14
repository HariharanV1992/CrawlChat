"""
Simplified Unified Storage Service
Handles S3 uploads, downloads, and deletes for user and temp files only.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from common.src.core.config import config
from common.src.core.exceptions import StorageError

logger = logging.getLogger(__name__)

class UnifiedStorageService:
    def __init__(self):
        self.s3_client = self._init_s3_client()

    def _init_s3_client(self):
        try:
            import boto3
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                return boto3.client('s3', region_name=config.s3_region)
            else:
                if hasattr(config, 's3_access_key') and hasattr(config, 's3_secret_key') and config.s3_access_key and config.s3_secret_key:
                    return boto3.client(
                        's3',
                        aws_access_key_id=config.s3_access_key,
                        aws_secret_access_key=config.s3_secret_key,
                        region_name=config.s3_region
                    )
                else:
                    logger.error("S3 credentials missing for local environment.")
                    return None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None

    async def upload_user_document(self, file_content: bytes, filename: str, user_id: str, content_type: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.s3_client:
            raise StorageError("S3 client not available")
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(filename).suffix
        s3_key = f"uploaded_documents/{user_id}/{task_id}/{timestamp}_{unique_id}{file_extension}" if task_id else f"uploaded_documents/{user_id}/{timestamp}_{unique_id}{file_extension}"
        content_type = content_type or self._get_content_type(file_extension)
        try:
            self.s3_client.put_object(
                Bucket=config.s3_bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'user_id': user_id,
                    'task_id': task_id or 'no_task',
                    'upload_timestamp': str(timestamp),
                    'file_size': str(len(file_content))
                }
            )
            logger.info(f"Uploaded user document: s3://{config.s3_bucket}/{s3_key}")
            return {"s3_key": s3_key, "filename": filename, "file_size": len(file_content)}
        except Exception as e:
            logger.error(f"Error uploading user document: {e}")
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
            logger.info(f"Uploaded temp file: s3://{config.s3_bucket}/{s3_key}")
            return {"s3_key": s3_key, "filename": filename, "file_size": len(file_content)}
        except Exception as e:
            logger.error(f"Error uploading temp file: {e}")
            raise StorageError(f"Failed to upload temp file: {e}")

    async def get_file_content(self, s3_key: str) -> Optional[bytes]:
        if not self.s3_client:
            logger.error("S3 client not available")
            return None
        try:
            response = self.s3_client.get_object(Bucket=config.s3_bucket, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None

    async def delete_file(self, s3_key: str) -> bool:
        if not self.s3_client:
            logger.error("S3 client not available")
            return False
        try:
            self.s3_client.delete_object(Bucket=config.s3_bucket, Key=s3_key)
            logger.info(f"Deleted file: s3://{config.s3_bucket}/{s3_key}")
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