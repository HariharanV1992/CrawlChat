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
        try:
            # 🔍 ENHANCED DEBUGGING - Track content at every step
            logger.info(f"[S3_DEBUG] === UPLOAD START ===")
            logger.info(f"[S3_DEBUG] Input file_content type: {type(file_content)}")
            logger.info(f"[S3_DEBUG] Input file_content length: {len(file_content) if file_content else 'None'}")
            logger.info(f"[S3_DEBUG] Input file_content is None: {file_content is None}")
            logger.info(f"[S3_DEBUG] Input file_content is empty: {not file_content}")
            
            if file_content:
                logger.info(f"[S3_DEBUG] Input file_content[:50]: {file_content[:50]}")
                logger.info(f"[S3_DEBUG] Input file_content MD5: {hashlib.md5(file_content).hexdigest()}")
            
            # Validate inputs
            if not file_content or len(file_content) == 0:
                logger.error(f"[S3_DEBUG] ❌ File content is empty or None")
                return {'status': 'error', 'error': 'File content is empty'}
            
            if not filename:
                logger.error(f"[S3_DEBUG] ❌ Filename is required")
                return {'status': 'error', 'error': 'Filename is required'}
            
            if not user_id:
                logger.error(f"[S3_DEBUG] ❌ User ID is required")
                return {'status': 'error', 'error': 'User ID is required'}
            
            # 🔍 EARLY SANITY CHECKS - Debug file content before processing
            logger.info(f"[S3_DEBUG] After validation - file_content length: {len(file_content)}")
            logger.info(f"[S3_DEBUG] After validation - file_content[:100]: {file_content[:100]}")
            logger.info(f"[S3_DEBUG] After validation - file_content MD5: {hashlib.md5(file_content).hexdigest()}")
            
            # Check if it's a PDF and validate it
            if filename.lower().endswith('.pdf'):
                if file_content.startswith(b"%PDF") and b"%%EOF" in file_content:
                    logger.info("[S3_DEBUG] PDF file looks valid - has PDF signature and EOF marker")
                else:
                    logger.warning("[S3_DEBUG] PDF file missing PDF signature or EOF marker!")
                    logger.warning(f"[S3_DEBUG] PDF header check: {file_content.startswith(b'%PDF')}")
                    logger.warning(f"[S3_DEBUG] PDF EOF check: {b'%%EOF' in file_content}")
                    logger.warning(f"[S3_DEBUG] First 20 bytes: {file_content[:20]}")
                    logger.warning(f"[S3_DEBUG] Last 100 bytes: {file_content[-100:]}")
            
            # Generate S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"
            
            logger.info(f"[S3_DEBUG] Generated S3 key: {s3_key}")
            
            # Prepare body content
            logger.info(f"[S3_DEBUG] Preparing body content...")
            logger.info(f"[S3_DEBUG] file_content type before body prep: {type(file_content)}")
            logger.info(f"[S3_DEBUG] file_content length before body prep: {len(file_content)}")
            
            if isinstance(file_content, str):
                body = file_content.encode('utf-8')
                logger.info(f"[S3_DEBUG] Converted string to bytes, body length: {len(body)}")
            elif isinstance(file_content, bytes):
                body = file_content
                logger.info(f"[S3_DEBUG] Using bytes directly, body length: {len(body)}")
            else:
                body = str(file_content).encode('utf-8')
                logger.info(f"[S3_DEBUG] Converted other type to bytes, body length: {len(body)}")
            
            # 🔍 CRITICAL CHECK - Verify body content after preparation
            logger.info(f"[S3_DEBUG] Body content type: {type(body)}")
            logger.info(f"[S3_DEBUG] Body content length: {len(body)}")
            logger.info(f"[S3_DEBUG] Body content is empty: {not body}")
            logger.info(f"[S3_DEBUG] Body content[:50]: {body[:50]}")
            logger.info(f"[S3_DEBUG] Body content MD5: {hashlib.md5(body).hexdigest()}")
            
            if not body or len(body) == 0:
                logger.error(f"[S3_DEBUG] ❌ Body content is empty after preparation!")
                return {'status': 'error', 'error': 'Body content is empty after preparation'}
            
            # Log upload details
            logger.info(f"[S3_UPLOAD] Uploading: {filename} -> s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[S3_UPLOAD] Content size: {len(body):,} bytes")
            logger.info(f"[S3_UPLOAD] First 20 bytes: {body[:20].hex()}")
            logger.info(f"[S3_UPLOAD] Last 20 bytes: {body[-20:].hex()}")
            logger.info(f"[S3_UPLOAD] Content MD5: {hashlib.md5(body).hexdigest()}")
            
            # Guess content type if not provided
            if not content_type:
                import mimetypes
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'
                logger.info(f"[S3_DEBUG] Guessed content type: {content_type}")
            
            # Prepare metadata
            meta = metadata.copy() if metadata else {}
            meta.update({
                'original_filename': filename,
                'user_id': user_id,
                'upload_timestamp': str(timestamp),
                'file_size': str(len(body)),
                'content_md5': hashlib.md5(body).hexdigest(),
                'upload_method': 'direct_put_object'
            })
            
            logger.info(f"[S3_DEBUG] Metadata prepared: {meta}")
            
            # 🔍 FINAL CHECK before S3 upload
            logger.info(f"[S3_DEBUG] === FINAL CHECK BEFORE S3 UPLOAD ===")
            logger.info(f"[S3_DEBUG] Body length: {len(body)}")
            logger.info(f"[S3_DEBUG] Body MD5: {hashlib.md5(body).hexdigest()}")
            logger.info(f"[S3_DEBUG] S3 Bucket: {self.bucket_name}")
            logger.info(f"[S3_DEBUG] S3 Key: {s3_key}")
            logger.info(f"[S3_DEBUG] Content Type: {content_type}")
            
            # Upload directly using put_object (more efficient)
            logger.info(f"[S3_UPLOAD] Uploading to S3: s3://{self.bucket_name}/{s3_key}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=body,
                ContentType=content_type,
                Metadata=meta
            )
            
            logger.info(f"[S3_UPLOAD] Upload successful: s3://{self.bucket_name}/{s3_key}")
            logger.info(f"[S3_UPLOAD] File available at s3://{self.bucket_name}/{s3_key}")
            
            # Verify upload by downloading a small portion
            try:
                logger.info(f"[S3_DEBUG] Starting upload verification...")
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
            
            logger.info(f"[S3_DEBUG] === UPLOAD COMPLETE ===")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': len(body),
                'filename': filename,
                's3_url': f"s3://{self.bucket_name}/{s3_key}",
                'upload_method': 'direct_put_object'
            }
            
        except Exception as e:
            logger.error(f"[S3_UPLOAD] Upload failed: {e}")
            logger.error(f"[S3_DEBUG] Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[S3_DEBUG] Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'error': str(e)}
        
        finally:
            # No temp files to clean up with direct put_object
            pass

    def upload_file_lambda_optimized(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        s3_prefix: str = 'uploaded_documents',
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 using Lambda-optimized method with temporary file.
        This method is specifically designed to prevent corruption in Lambda environments.
        
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
        import tempfile
        import os
        
        try:
            logger.info(f"[S3_LAMBDA] === LAMBDA-OPTIMIZED UPLOAD START ===")
            logger.info(f"[S3_LAMBDA] Input file_content length: {len(file_content) if file_content else 'None'}")
            logger.info(f"[S3_LAMBDA] Input file_content MD5: {hashlib.md5(file_content).hexdigest() if file_content else 'None'}")
            
            # Validate inputs
            if not file_content or len(file_content) == 0:
                logger.error(f"[S3_LAMBDA] ❌ File content is empty or None")
                return {'status': 'error', 'error': 'File content is empty'}
            
            if not filename:
                logger.error(f"[S3_LAMBDA] ❌ Filename is required")
                return {'status': 'error', 'error': 'Filename is required'}
            
            if not user_id:
                logger.error(f"[S3_LAMBDA] ❌ User ID is required")
                return {'status': 'error', 'error': 'User ID is required'}
            
            # Enhanced PDF validation for Lambda environment
            if filename.lower().endswith('.pdf'):
                logger.info(f"[S3_LAMBDA] PDF file detected - performing enhanced validation")
                logger.info(f"[S3_LAMBDA] PDF header check: {file_content.startswith(b'%PDF')}")
                logger.info(f"[S3_LAMBDA] PDF EOF check: {b'%%EOF' in file_content}")
                logger.info(f"[S3_LAMBDA] PDF size: {len(file_content):,} bytes")
                
                if not file_content.startswith(b'%PDF'):
                    logger.error(f"[S3_LAMBDA] ❌ Invalid PDF header: {file_content[:20]}")
                    return {'status': 'error', 'error': 'Invalid PDF file - missing PDF header'}
                
                if b'%%EOF' not in file_content[-1000:]:
                    logger.warning(f"[S3_LAMBDA] ⚠️ PDF EOF marker not found in last 1000 bytes")
                    # Don't fail for missing EOF, but log it
            
            # Generate S3 key
            timestamp = int(datetime.utcnow().timestamp())
            unique_id = hashlib.md5((filename + str(timestamp)).encode()).hexdigest()[:8]
            ext = os.path.splitext(filename)[1]
            s3_key = f"{s3_prefix}/{user_id}/{timestamp}_{unique_id}{ext}"
            
            logger.info(f"[S3_LAMBDA] Generated S3 key: {s3_key}")
            
            # Create temporary file in /tmp directory (required for Lambda)
            temp_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"upload_{timestamp}_{unique_id}{ext}")
            
            logger.info(f"[S3_LAMBDA] Creating temporary file: {temp_file_path}")
            
            # Write content to temporary file with proper error handling
            try:
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(file_content)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())  # Ensure data is written to disk
                
                logger.info(f"[S3_LAMBDA] Wrote {len(file_content)} bytes to temporary file")
                
                # Verify temporary file was written correctly
                if not os.path.exists(temp_file_path):
                    logger.error(f"[S3_LAMBDA] ❌ Temporary file was not created")
                    return {'status': 'error', 'error': 'Failed to create temporary file'}
                
                temp_file_size = os.path.getsize(temp_file_path)
                logger.info(f"[S3_LAMBDA] Temporary file size: {temp_file_size} bytes")
                
                if temp_file_size != len(file_content):
                    logger.error(f"[S3_LAMBDA] ❌ File size mismatch: expected {len(file_content)}, got {temp_file_size}")
                    return {'status': 'error', 'error': 'File size mismatch during temporary file creation'}
                
                # Verify temporary file content
                with open(temp_file_path, 'rb') as verify_file:
                    temp_content = verify_file.read()
                    temp_md5 = hashlib.md5(temp_content).hexdigest()
                    original_md5 = hashlib.md5(file_content).hexdigest()
                    logger.info(f"[S3_LAMBDA] Temporary file MD5: {temp_md5}")
                    logger.info(f"[S3_LAMBDA] Original file MD5: {original_md5}")
                    
                    if temp_md5 != original_md5:
                        logger.error(f"[S3_LAMBDA] ❌ MD5 mismatch between original and temporary file")
                        return {'status': 'error', 'error': 'File content corruption detected during temporary file creation'}
                
                logger.info(f"[S3_LAMBDA] ✅ Temporary file verification passed")
                
            except Exception as write_error:
                logger.error(f"[S3_LAMBDA] ❌ Error writing temporary file: {write_error}")
                return {'status': 'error', 'error': f'Failed to write temporary file: {str(write_error)}'}
            
            # Guess content type if not provided
            if not content_type:
                import mimetypes
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'
                logger.info(f"[S3_LAMBDA] Guessed content type: {content_type}")
            
            # Prepare metadata
            meta = metadata.copy() if metadata else {}
            meta.update({
                'original_filename': filename,
                'user_id': user_id,
                'upload_timestamp': str(timestamp),
                'file_size': str(len(file_content)),
                'content_md5': hashlib.md5(file_content).hexdigest(),
                'upload_method': 'lambda_optimized_temp_file',
                'lambda_environment': 'true'
            })
            
            logger.info(f"[S3_LAMBDA] Metadata prepared: {meta}")
            
            # Upload using upload_file method (more reliable in Lambda)
            logger.info(f"[S3_LAMBDA] Uploading to S3: s3://{self.bucket_name}/{s3_key}")
            try:
                self.s3_client.upload_file(
                    Filename=temp_file_path,
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': meta
                    }
                )
                
                logger.info(f"[S3_LAMBDA] ✅ Upload successful: s3://{self.bucket_name}/{s3_key}")
                
            except Exception as upload_error:
                logger.error(f"[S3_LAMBDA] ❌ S3 upload failed: {upload_error}")
                return {'status': 'error', 'error': f'S3 upload failed: {str(upload_error)}'}
            
            # Verify upload by downloading and comparing
            try:
                logger.info(f"[S3_LAMBDA] Starting upload verification...")
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                downloaded_content = response['Body'].read()
                logger.info(f"[S3_LAMBDA] Verification - downloaded size: {len(downloaded_content):,} bytes")
                logger.info(f"[S3_LAMBDA] Verification - downloaded MD5: {hashlib.md5(downloaded_content).hexdigest()}")
                
                if len(downloaded_content) != len(file_content):
                    logger.error(f"[S3_LAMBDA] ❌ Verification failed - size mismatch: uploaded={len(file_content)}, downloaded={len(downloaded_content)}")
                    raise Exception("S3 upload verification failed - file size mismatch")
                
                if hashlib.md5(downloaded_content).hexdigest() != hashlib.md5(file_content).hexdigest():
                    logger.error(f"[S3_LAMBDA] ❌ Verification failed - MD5 mismatch")
                    raise Exception("S3 upload verification failed - MD5 mismatch")
                
                logger.info(f"[S3_LAMBDA] ✅ Upload verification passed")
                
            except Exception as verify_error:
                logger.error(f"[S3_LAMBDA] ❌ Upload verification failed: {verify_error}")
                # Don't fail the upload if verification fails, but log it
                logger.warning(f"[S3_LAMBDA] ⚠️ Upload completed but verification failed - file may be corrupted")
            
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                logger.info(f"[S3_LAMBDA] ✅ Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[S3_LAMBDA] ⚠️ Failed to clean up temporary file: {cleanup_error}")
            
            logger.info(f"[S3_LAMBDA] === LAMBDA-OPTIMIZED UPLOAD COMPLETE ===")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': len(file_content),
                'filename': filename,
                's3_url': f"s3://{self.bucket_name}/{s3_key}",
                'upload_method': 'lambda_optimized_temp_file',
                'lambda_environment': True
            }
            
        except Exception as e:
            logger.error(f"[S3_LAMBDA] ❌ Upload failed: {e}")
            logger.error(f"[S3_LAMBDA] Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[S3_LAMBDA] Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'error': str(e)}

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
        Uses Lambda-optimized method when in Lambda environment.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User identifier
            content_type: MIME type (optional)
            task_id: Optional task ID for organization
            
        Returns:
            Dict with upload result
        """
        # Enhanced Lambda environment detection
        is_lambda = (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
            os.getenv('AWS_EXECUTION_ENV') or 
            os.getenv('LAMBDA_TASK_ROOT') or
            os.getenv('AWS_LAMBDA_RUNTIME_API') or
            '/var/task' in os.getcwd() or
            '/tmp' in os.getcwd()
        )
        
        logger.info(f"[S3_UPLOAD] Environment detection:")
        logger.info(f"[S3_UPLOAD]   AWS_LAMBDA_FUNCTION_NAME: {os.getenv('AWS_LAMBDA_FUNCTION_NAME')}")
        logger.info(f"[S3_UPLOAD]   AWS_EXECUTION_ENV: {os.getenv('AWS_EXECUTION_ENV')}")
        logger.info(f"[S3_UPLOAD]   LAMBDA_TASK_ROOT: {os.getenv('LAMBDA_TASK_ROOT')}")
        logger.info(f"[S3_UPLOAD]   AWS_LAMBDA_RUNTIME_API: {os.getenv('AWS_LAMBDA_RUNTIME_API')}")
        logger.info(f"[S3_UPLOAD]   Current working directory: {os.getcwd()}")
        logger.info(f"[S3_UPLOAD]   Is Lambda environment: {is_lambda}")
        
        # Prepare metadata
        metadata = {}
        if task_id:
            metadata['task_id'] = task_id
        
        # Always use Lambda-optimized method for PDFs in production to ensure reliability
        if is_lambda or (filename.lower().endswith('.pdf')):
            logger.info(f"[S3_UPLOAD] Using Lambda-optimized upload method (Lambda: {is_lambda}, PDF: {filename.lower().endswith('.pdf')})")
            return self.upload_file_lambda_optimized(
                file_content=file_content,
                filename=filename,
                user_id=user_id,
                content_type=content_type,
                s3_prefix='uploaded_documents',
                metadata=metadata
            )
        else:
            logger.info(f"[S3_UPLOAD] Using standard upload method")
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