import os
import boto3
import hashlib
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class DirectS3UploadService:
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET', 'crawlchat-data')
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.s3_client = boto3.client('s3', region_name=self.region)

    def upload_file(
        self,
        file_content,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        s3_prefix: Optional[str] = 'uploaded_documents',
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 using Lambda-compatible method (temporary file + upload_file).
        Args:
            file_content: bytes or str
            filename: original filename
            user_id: user identifier
            content_type: MIME type (optional)
            s3_prefix: S3 prefix/folder (optional)
            metadata: extra metadata (optional)
        Returns:
            dict with s3_key, status, and error (if any)
        """
        temp_path = None
        try:
            # Prepare S3 key
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

            # Log content info for debugging
            logger.info(f"[DIRECT_S3_UPLOAD] Content size: {len(body):,} bytes")
            logger.info(f"[DIRECT_S3_UPLOAD] First 20 bytes: {body[:20].hex()}")
            logger.info(f"[DIRECT_S3_UPLOAD] Last 20 bytes: {body[-20:].hex()}")
            logger.info(f"[DIRECT_S3_UPLOAD] Content MD5: {hashlib.md5(body).hexdigest()}")

            # Create temporary file
            temp_path = f"/tmp/{uuid4().hex}_{filename}"
            logger.info(f"[DIRECT_S3_UPLOAD] Creating temp file: {temp_path}")

            # Write content to temporary file
            with open(temp_path, "wb") as f:
                f.write(body)

            # Verify temp file was written correctly
            temp_file_size = os.path.getsize(temp_path)
            logger.info(f"[DIRECT_S3_UPLOAD] Temp file size: {temp_file_size:,} bytes")

            if temp_file_size != len(body):
                raise Exception(f"Temp file size mismatch: expected {len(body)}, got {temp_file_size}")

            # Guess content type if not provided
            if not content_type:
                content_type = self._guess_content_type(ext)

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
            logger.info(f"[DIRECT_S3_UPLOAD] Uploading to S3: s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                temp_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': meta
                }
            )

            logger.info(f"[DIRECT_S3_UPLOAD] Upload successful: s3://{self.bucket_name}/{s3_key}")

            # Verify upload by downloading a small portion
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                downloaded_content = response['Body'].read()
                logger.info(f"[DIRECT_S3_UPLOAD] Verification - downloaded size: {len(downloaded_content):,} bytes")
                logger.info(f"[DIRECT_S3_UPLOAD] Verification - downloaded MD5: {hashlib.md5(downloaded_content).hexdigest()}")
                
                if len(downloaded_content) != len(body):
                    logger.error(f"[DIRECT_S3_UPLOAD] Verification failed - size mismatch: uploaded={len(body)}, downloaded={len(downloaded_content)}")
                    raise Exception("S3 upload verification failed - file size mismatch")
                
                logger.info(f"[DIRECT_S3_UPLOAD] Upload verification passed")
            except Exception as verify_error:
                logger.error(f"[DIRECT_S3_UPLOAD] Upload verification failed: {verify_error}")
                raise Exception(f"S3 upload verification failed: {str(verify_error)}")

            return {
                'status': 'success', 
                's3_key': s3_key, 
                'bucket': self.bucket_name,
                'file_size': len(body),
                'upload_method': 'temp_file_upload_file'
            }

        except Exception as e:
            logger.error(f"[DIRECT_S3_UPLOAD] Upload failed: {e}")
            return {'status': 'error', 'error': str(e)}
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"[DIRECT_S3_UPLOAD] Temp file cleaned up: {temp_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[DIRECT_S3_UPLOAD] Failed to clean up temp file {temp_path}: {cleanup_error}")

    def _guess_content_type(self, ext: str) -> str:
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
s3_upload_service = DirectS3UploadService() 