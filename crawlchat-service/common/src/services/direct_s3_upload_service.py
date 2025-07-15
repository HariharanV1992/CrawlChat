import os
import boto3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import logging

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
        Upload a file to S3 with robust handling (modeled after crawler service).
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
        try:
            # Prepare S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"

            # Prepare body
            if isinstance(file_content, str):
                body = file_content.encode('utf-8')
            elif isinstance(file_content, bytes):
                body = file_content
            else:
                body = str(file_content).encode('utf-8')

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
                'content_md5': hashlib.md5(body).hexdigest()
            })

            # Upload
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=body,
                ContentType=content_type,
                Metadata=meta
            )
            logger.info(f"[DIRECT_S3_UPLOAD] Uploaded: s3://{self.bucket_name}/{s3_key}")
            return {'status': 'success', 's3_key': s3_key, 'bucket': self.bucket_name}
        except Exception as e:
            logger.error(f"[DIRECT_S3_UPLOAD] Upload failed: {e}")
            return {'status': 'error', 'error': str(e)}

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