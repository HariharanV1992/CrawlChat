"""
S3 Upload Service - Single, clean service for all S3 upload operations
"""

import os
import boto3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class S3UploadService:
    """
    Single S3 upload service that handles all upload operations with Lambda compatibility.
    Uses temporary file + upload_file() method for reliable uploads in Lambda environment.
    """
    
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET', 'crawlchat-data')
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        logger.info(f"[S3_UPLOAD] Initialized with bucket: {self.bucket_name}, region: {self.region}")

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        s3_prefix: str = 'uploaded_documents',
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 using Lambda-compatible method (temporary file + upload_file).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User identifier
            content_type: MIME type (optional, auto-detected if not provided)
            s3_prefix: S3 prefix/folder
            metadata: Additional metadata
            
        Returns:
            Dict with upload result including s3_key, status, and error (if any)
        """
        temp_path = None
        try:
            # Validate inputs
            if not file_content or len(file_content) == 0:
                return {'status': 'error', 'error': 'File content is empty'}
            
            if not filename:
                return {'status': 'error', 'error': 'Filename is required'}
            
            if not user_id:
                return {'status': 'error', 'error': 'User ID is required'}
            
            # 🔍 EARLY SANITY CHECKS - Debug file content before processing
            logger.info(f"[DEBUG] file_content length: {len(file_content)}")
            logger.info(f"[DEBUG] file_content[:100]: {file_content[:100]}")
            logger.info(f"[DEBUG] file_content MD5: {hashlib.md5(file_content).hexdigest()}")
            
            # Check if it's a PDF and validate it
            if filename.lower().endswith('.pdf'):
                if file_content.startswith(b"%PDF") and b"%%EOF" in file_content:
                    logger.info("[DEBUG] PDF file looks valid - has PDF signature and EOF marker")
                else:
                    logger.warning("[DEBUG] PDF file missing PDF signature or EOF marker!")
                    logger.warning(f"[DEBUG] PDF header check: {file_content.startswith(b'%PDF')}")
                    logger.warning(f"[DEBUG] PDF EOF check: {b'%%EOF' in file_content}")
                    logger.warning(f"[DEBUG] First 20 bytes: {file_content[:20]}")
                    logger.warning(f"[DEBUG] Last 100 bytes: {file_content[-100:]}")
            
            # Generate S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"
            
            # Prepare body content
            if isinstance(file_content, str):
                body = file_content.encode('utf-8')
            elif isinstance(file_content, bytes):
                body = file_content
            else:
                body = str(file_content).encode('utf-8')
            
            # Log upload details
            logger.info(f"[S3_UPLOAD] Uploading: {filename} -> s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[S3_UPLOAD] Content size: {len(body):,} bytes")
            logger.info(f"[S3_UPLOAD] First 20 bytes: {body[:20].hex()}")
            logger.info(f"[S3_UPLOAD] Last 20 bytes: {body[-20:].hex()}")
            logger.info(f"[S3_UPLOAD] Content MD5: {hashlib.md5(body).hexdigest()}")
            
            # Create temporary file - use only the filename, not the full path
            safe_filename = os.path.basename(filename)
            temp_path = f"/tmp/{uuid4().hex}_{safe_filename}"
            logger.info(f"[S3_UPLOAD] Creating temp file: {temp_path}")
            
            # Write content to temporary file
            with open(temp_path, "wb") as f:
                f.write(body)
            
            # Verify temp file was written correctly
            temp_file_size = os.path.getsize(temp_path)
            logger.info(f"[S3_UPLOAD] Temp file size: {temp_file_size:,} bytes")
            
            if temp_file_size != len(body):
                raise Exception(f"Temp file size mismatch: expected {len(body)}, got {temp_file_size}")
            
            # Guess content type if not provided
            if not content_type:
                import mimetypes
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'
                logger.info(f"[DEBUG] Guessed content type: {content_type}")
            
            # Prepare metadata
            meta = metadata.copy() if metadata else {}
            meta.update({
                'original_filename': filename,
                'user_id': user_id,
                'upload_timestamp': str(timestamp),
                'file_size': str(len(body)),
                'content_md5': hashlib.md5(body).hexdigest(),
                'upload_method': 'temp_file_upload_file'
            })
            
            # Upload using upload_file (Lambda-compatible method)
            logger.info(f"[S3_UPLOAD] Uploading to S3: s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                temp_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': meta
                }
            )
            
            logger.info(f"[S3_UPLOAD] Upload successful: s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[S3_UPLOAD] File available at s3://{self.bucket_name}/{s3_key}")
            
            # Verify upload by downloading a small portion
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                downloaded_content = response['Body'].read()
                logger.info(f"[S3_UPLOAD] Verification - downloaded size: {len(downloaded_content):,} bytes")
                logger.info(f"[S3_UPLOAD] Verification - downloaded MD5: {hashlib.md5(downloaded_content).hexdigest()}")
                
                if len(downloaded_content) != len(body):
                    logger.error(f"[S3_UPLOAD] Verification failed - size mismatch: uploaded={len(body)}, downloaded={len(downloaded_content)}")
                    raise Exception("S3 upload verification failed - file size mismatch")
                
                logger.info(f"[S3_UPLOAD] Upload verification passed")
            except Exception as verify_error:
                logger.error(f"[S3_UPLOAD] Upload verification failed: {verify_error}")
                raise Exception(f"S3 upload verification failed: {str(verify_error)}")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': len(body),
                'filename': filename,
                's3_url': f"s3://{self.bucket_name}/{s3_key}",
                'upload_method': 'temp_file_upload_file'
            }
            
        except Exception as e:
            logger.error(f"[S3_UPLOAD] Upload failed: {e}")
            return {'status': 'error', 'error': str(e)}
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"[S3_UPLOAD] Temp file cleaned up: {temp_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[S3_UPLOAD] Failed to clean up temp file {temp_path}: {cleanup_error}")

    def upload_user_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a user document to the uploaded_documents folder.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User identifier
            content_type: MIME type (optional)
            task_id: Optional task ID for organization
            
        Returns:
            Dict with upload result
        """
        # Prepare metadata
        metadata = {}
        if task_id:
            metadata['task_id'] = task_id
        
        return self.upload_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            content_type=content_type,
            s3_prefix='uploaded_documents',
            metadata=metadata
        )

    def upload_temp_file(
        self,
        file_content: bytes,
        filename: str,
        purpose: str = "temp",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a temporary file for processing.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            purpose: Purpose of the temp file (e.g., "textract_pdf", "textract_image")
            user_id: User identifier (optional)
            
        Returns:
            Dict with upload result
        """
        # Prepare metadata
        metadata = {
            'purpose': purpose,
            'temp_file': 'true'
        }
        
        return self.upload_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id or 'anonymous',
            content_type=None,  # Auto-detect
            s3_prefix=f'temp_files/{purpose}',
            metadata=metadata
        )

    def get_file_content(self, s3_key: str) -> Optional[bytes]:
        """
        Get file content from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as bytes or None if failed
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"[S3_UPLOAD] Error getting file content: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"[S3_UPLOAD] Deleted file: s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"[S3_UPLOAD] Error deleting file: {e}")
            return False

    def verify_upload(self, s3_key: str) -> Dict[str, Any]:
        """
        Verify that a file was uploaded correctly.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict with verification result
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
            logger.error(f"[S3_UPLOAD] Verification failed: {e}")
            return {'status': 'error', 'error': str(e)}

    def _guess_content_type(self, ext: str) -> str:
        """Guess content type from file extension."""
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
        return content_types.get(ext.lower(), 'application/octet-stream')

# Global instance
s3_upload_service = S3UploadService() 