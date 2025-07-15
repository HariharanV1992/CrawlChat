"""
Simple S3 Upload Service - Direct file upload approach
"""

import os
import boto3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleS3UploadService:
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET', 'crawlchat-data')
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.s3_client = boto3.client('s3', region_name=self.region)

    def upload_file_from_path(self, file_path: str, user_id: str, s3_prefix: str = 'uploaded_documents') -> Dict[str, Any]:
        """
        Upload a file from disk path to S3 (like the working script).
        """
        try:
            if not os.path.exists(file_path):
                return {'status': 'error', 'error': f'File not found: {file_path}'}
            
            # Get file info
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Generate S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"
            
            logger.info(f"[SIMPLE_S3] Uploading file: {file_path} -> s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[SIMPLE_S3] File size: {file_size:,} bytes")
            
            # Upload using upload_file (like the working script)
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            
            logger.info(f"[SIMPLE_S3] Upload successful: s3://{self.bucket_name}/{s3_key}")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': file_size,
                'filename': filename,
                's3_url': f"s3://{self.bucket_name}/{s3_key}"
            }
            
        except Exception as e:
            logger.error(f"[SIMPLE_S3] Upload failed: {e}")
            return {'status': 'error', 'error': str(e)}

    def upload_file_from_memory(self, file_content: bytes, filename: str, user_id: str, s3_prefix: str = 'uploaded_documents') -> Dict[str, Any]:
        """
        Upload file content from memory to S3.
        """
        try:
            # Generate S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"
            
            logger.info(f"[SIMPLE_S3] Uploading from memory: {filename} -> s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[SIMPLE_S3] Content size: {len(file_content):,} bytes")
            
            # Upload using put_object
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._guess_content_type(ext)
            )
            
            logger.info(f"[SIMPLE_S3] Upload successful: s3://{self.bucket_name}/{s3_key}")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': len(file_content),
                'filename': filename,
                's3_url': f"s3://{self.bucket_name}/{s3_key}"
            }
            
        except Exception as e:
            logger.error(f"[SIMPLE_S3] Upload failed: {e}")
            return {'status': 'error', 'error': str(e)}

    def verify_upload(self, s3_key: str) -> Dict[str, Any]:
        """
        Verify that a file was uploaded correctly.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read()
            
            return {
                'status': 'success',
                'file_size': len(content),
                'content_md5': hashlib.md5(content).hexdigest(),
                'first_bytes': content[:20].hex(),
                'last_bytes': content[-20:].hex()
            }
            
        except Exception as e:
            logger.error(f"[SIMPLE_S3] Verification failed: {e}")
            return {'status': 'error', 'error': str(e)}

    def _guess_content_type(self, ext: str) -> str:
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff'
        }
        return content_types.get(ext.lower(), 'application/octet-stream')

# Global instance
simple_s3_upload_service = SimpleS3UploadService() 