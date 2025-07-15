"""
Unified Storage Service
Uses the new direct S3 upload service for all operations.
"""

import logging
from typing import Optional, Dict, Any
from common.src.core.exceptions import StorageError

logger = logging.getLogger(__name__)

class UnifiedStorageService:
    """Unified storage service that uses the new direct S3 upload service."""
    def __init__(self):
        # No longer need to initialize S3 client here
        pass

    async def upload_user_document(self, file_content: bytes, filename: str, user_id: str, content_type: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload user document using the new direct S3 upload service."""
        from common.src.services.direct_s3_upload_service import s3_upload_service
        
        # Validate input
        if not file_content or len(file_content) == 0:
            raise StorageError("File content is empty")
        
        if not filename:
            raise StorageError("Filename is required")
        
        if not user_id:
            raise StorageError("User ID is required")
        
        # Prepare metadata
        metadata = {}
        if task_id:
            metadata['task_id'] = task_id
        
        # Use the new direct S3 upload service
        result = s3_upload_service.upload_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            content_type=content_type,
            s3_prefix='uploaded_documents',
            metadata=metadata
        )
        
        if result['status'] == 'success':
            return {
                "s3_key": result['s3_key'],
                "filename": filename,
                "file_size": len(file_content),
                "bucket": result['bucket']
            }
        else:
            raise StorageError(f"Failed to upload user document: {result.get('error', 'Unknown error')}")

    async def upload_temp_file(self, file_content: bytes, filename: str, purpose: str = "temp", user_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload temp file using the new direct S3 upload service."""
        from common.src.services.direct_s3_upload_service import s3_upload_service
        
        # Prepare metadata
        metadata = {
            'purpose': purpose,
            'temp_file': 'true'
        }
        
        # Use the new direct S3 upload service
        result = s3_upload_service.upload_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id or 'anonymous',
            content_type=None,  # Auto-detect
            s3_prefix=f'temp_files/{purpose}',
            metadata=metadata
        )
        
        if result['status'] == 'success':
            return {
                "s3_key": result['s3_key'],
                "filename": filename,
                "file_size": len(file_content)
            }
        else:
            raise StorageError(f"Failed to upload temp file: {result.get('error', 'Unknown error')}")

    async def get_file_content(self, s3_key: str) -> Optional[bytes]:
        """Get file content using the new direct S3 upload service."""
        from common.src.services.direct_s3_upload_service import s3_upload_service
        
        try:
            # Use boto3 directly for reading (since the new service is for uploads)
            import boto3
            import os
            bucket_name = os.getenv('S3_BUCKET', 'crawlchat-data')
            region = os.getenv('AWS_REGION', 'ap-south-1')
            s3_client = boto3.client('s3', region_name=region)
            
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None

    async def delete_file(self, s3_key: str) -> bool:
        """Delete file using the new direct S3 upload service."""
        try:
            # Use boto3 directly for deletion (since the new service is for uploads)
            import boto3
            import os
            bucket_name = os.getenv('S3_BUCKET', 'crawlchat-data')
            region = os.getenv('AWS_REGION', 'ap-south-1')
            s3_client = boto3.client('s3', region_name=region)
            
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            logger.info(f"Deleted file: s3://{bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False



# Global instance
unified_storage_service = UnifiedStorageService() 