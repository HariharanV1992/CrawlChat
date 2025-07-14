"""
AWS Textract Service for document text extraction
Clean version with all syntax errors fixed
"""

import logging
import os
import boto3
import time
import json
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import asyncio
import io
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter
import tempfile

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document types for API selection."""
    GENERAL = "general"
    FORM = "form"
    INVOICE = "invoice"
    TABLE_HEAVY = "table_heavy"

class TextractError(Exception):
    """Custom exception for Textract errors."""
    pass

class AWSTextractService:
    """AWS Textract service for document text extraction."""
    
    def __init__(self):
        """Initialize the Textract service."""
        self.textract_client = None
        self.s3_client = None
        self._clients_initialized = False
    
    def _init_clients(self):
        """Initialize AWS clients."""
        try:
            # Get region from environment or config
            region = os.getenv('AWS_REGION', 'ap-south-1')
            
            # Check if running in Lambda environment
            is_lambda = (
                os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
                os.getenv('AWS_EXECUTION_ENV') or 
                os.getenv('LAMBDA_TASK_ROOT')
            )
            
            if is_lambda:
                # Running in Lambda - use IAM role
                logger.info("🔧 AWS Textract: Initializing clients in Lambda environment")
                self.textract_client = boto3.client('textract', region_name=region)
                self.s3_client = boto3.client('s3', region_name=region)
            else:
                # Running locally - use credentials if available
                access_key = os.getenv('AWS_ACCESS_KEY_ID')
                secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                
                if access_key and secret_key:
                    logger.info("🔧 AWS Textract: Initializing clients locally")
                    self.textract_client = boto3.client(
                        'textract',
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region
                    )
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region
                    )
                else:
                    logger.warning("AWS Textract: No credentials available for local environment")
                    self.textract_client = None
                    self.s3_client = None
            
            if self.textract_client and self.s3_client:
                logger.info("✅ AWS Textract: Clients initialized successfully")
            else:
                logger.error("❌ AWS Textract: Client initialization failed")
                
        except Exception as e:
            logger.error(f"❌ AWS Textract: Failed to initialize clients: {e}")
            self.textract_client = None
            self.s3_client = None
    
    def _ensure_clients_initialized(self):
        """Ensure AWS clients are initialized (lazy initialization)."""
        if not self._clients_initialized:
            self._init_clients()
            self._clients_initialized = True

    def _is_running_in_lambda(self) -> bool:
        """Check if running in AWS Lambda environment."""
        return bool(
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
            os.getenv('AWS_EXECUTION_ENV') or 
            os.getenv('LAMBDA_TASK_ROOT')
        )

    def _validate_s3_file(self, s3_bucket: str, s3_key: str) -> bool:
        """
        Validate that S3 file exists and has content.
        Returns True if file is valid, False otherwise.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.s3_client:
                logger.error("❌ AWS Textract: S3 client not available for file validation")
                return False
            
            # Check if file exists and get its size
            response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
            file_size = response.get('ContentLength', 0)
            
            logger.info(f"📦 AWS Textract: S3 file validation - size: {file_size} bytes")
            
            if file_size == 0:
                logger.error("❌ AWS Textract: S3 file is empty (0 bytes)")
                return False
            
            # Try to read a small portion to verify access
            obj = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            content_sample = obj['Body'].read(1024)  # Read first 1KB
            
            logger.info(f"📦 AWS Textract: S3 file access verified - sample size: {len(content_sample)} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: S3 file validation failed: {e}")
            return False

    def _check_aws_permissions(self) -> Dict[str, bool]:
        """
        Check AWS permissions for Textract and S3 operations.
        Returns a dictionary with permission status for each service.
        """
        permissions = {
            "s3_read": False,
            "s3_write": False,
            "textract_sync": False,
            "textract_async": False,
            "iam_role": False
        }
        
        try:
            self._ensure_clients_initialized()
            
            # Check if running in Lambda with IAM role
            is_lambda = self._is_running_in_lambda()
            if is_lambda:
                try:
                    # Try to get caller identity to verify IAM role
                    sts_client = boto3.client('sts')
                    identity = sts_client.get_caller_identity()
                    role_arn = identity.get('Arn', '')
                    permissions["iam_role"] = True
                    logger.info(f"🔐 AWS Textract: IAM Role verified - {role_arn}")
                except Exception as e:
                    logger.error(f"❌ AWS Textract: IAM Role check failed: {e}")
                    permissions["iam_role"] = False
            
            # Test S3 read permissions
            if self.s3_client:
                try:
                    # Try to list buckets (basic S3 permission)
                    self.s3_client.list_buckets()
                    permissions["s3_read"] = True
                    logger.info("✅ AWS Textract: S3 read permissions verified")
                except Exception as e:
                    logger.error(f"❌ AWS Textract: S3 read permission check failed: {e}")
                    permissions["s3_read"] = False
                
                # Test S3 write permissions (try to upload a small test file)
                try:
                    from common.src.core.config import config
                    test_key = f"permission_test_{int(time.time())}.txt"
                    test_content = b"Permission test file"
                    
                    self.s3_client.put_object(
                        Bucket=config.s3_bucket,
                        Key=test_key,
                        Body=test_content
                    )
                    
                    # Clean up test file
                    self.s3_client.delete_object(Bucket=config.s3_bucket, Key=test_key)
                    permissions["s3_write"] = True
                    logger.info("✅ AWS Textract: S3 write permissions verified")
                except Exception as e:
                    logger.error(f"❌ AWS Textract: S3 write permission check failed: {e}")
                    permissions["s3_write"] = False
            
            # Test Textract sync permissions
            if self.textract_client:
                try:
                    # Create a simple test image for Textract
                    from PIL import Image, ImageDraw, ImageFont
                    import io
                    
                    # Create a test image with text
                    img = Image.new('RGB', (200, 100), color='white')
                    draw = ImageDraw.Draw(img)
                    draw.text((10, 40), "Test", fill='black')
                    
                    # Convert to bytes
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    # Test sync Textract call
                    self.textract_client.detect_document_text(
                        Document={'Bytes': img_bytes.getvalue()}
                    )
                    permissions["textract_sync"] = True
                    logger.info("✅ AWS Textract: Textract sync permissions verified")
                except Exception as e:
                    logger.error(f"❌ AWS Textract: Textract sync permission check failed: {e}")
                    permissions["textract_sync"] = False
                
                # Test Textract async permissions (just check if we can start a job)
                try:
                    # Upload test image to S3 for async test
                    from common.src.core.config import config
                    test_img_key = f"textract_test_{int(time.time())}.png"
                    
                    self.s3_client.put_object(
                        Bucket=config.s3_bucket,
                        Key=test_img_key,
                        Body=img_bytes.getvalue()
                    )
                    
                    # Try to start async job
                    response = self.textract_client.start_document_analysis(
                        DocumentLocation={'S3Object': {'Bucket': config.s3_bucket, 'Name': test_img_key}},
                        FeatureTypes=['TABLES']
                    )
                    
                    job_id = response['JobId']
                    logger.info(f"✅ AWS Textract: Textract async permissions verified - Job ID: {job_id}")
                    
                    # Cancel the job immediately to avoid charges
                    try:
                        self.textract_client.cancel_document_analysis(JobId=job_id)
                        logger.info(f"✅ AWS Textract: Cancelled test job {job_id}")
                    except:
                        pass  # Job might have already started
                    
                    permissions["textract_async"] = True
                    
                    # Clean up test image
                    try:
                        self.s3_client.delete_object(Bucket=config.s3_bucket, Key=test_img_key)
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"❌ AWS Textract: Textract async permission check failed: {e}")
                    permissions["textract_async"] = False
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Permission check failed: {e}")
        
        return permissions

    def _log_environment_diagnostics(self):
        """
        Log comprehensive environment diagnostics for troubleshooting.
        """
        try:
            logger.info("🔍 AWS Textract: === ENVIRONMENT DIAGNOSTICS ===")
            
            # Environment detection
            is_lambda = self._is_running_in_lambda()
            logger.info(f"🔧 AWS Textract: Environment: {'Lambda' if is_lambda else 'Local'}")
            
            # AWS Configuration
            region = os.getenv('AWS_REGION', 'ap-south-1')
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            logger.info(f"🌍 AWS Textract: Region: {region}")
            logger.info(f"🔑 AWS Textract: Access Key: {'Set' if access_key else 'Not Set'}")
            logger.info(f"🔑 AWS Textract: Secret Key: {'Set' if secret_key else 'Not Set'}")
            
            # Lambda-specific environment variables
            if is_lambda:
                lambda_function = os.getenv('AWS_LAMBDA_FUNCTION_NAME', 'Unknown')
                lambda_version = os.getenv('AWS_LAMBDA_FUNCTION_VERSION', 'Unknown')
                lambda_memory = os.getenv('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'Unknown')
                lambda_timeout = os.getenv('AWS_LAMBDA_FUNCTION_TIMEOUT', 'Unknown')
                
                logger.info(f"⚡ AWS Textract: Lambda Function: {lambda_function}")
                logger.info(f"⚡ AWS Textract: Lambda Version: {lambda_version}")
                logger.info(f"⚡ AWS Textract: Lambda Memory: {lambda_memory}MB")
                logger.info(f"⚡ AWS Textract: Lambda Timeout: {lambda_timeout}s")
            
            # Check permissions
            permissions = self._check_aws_permissions()
            logger.info("🔐 AWS Textract: === PERMISSION STATUS ===")
            for permission, status in permissions.items():
                status_emoji = "✅" if status else "❌"
                logger.info(f"{status_emoji} AWS Textract: {permission}: {status}")
            
            # Client status
            logger.info("🔧 AWS Textract: === CLIENT STATUS ===")
            logger.info(f"{'✅' if self.textract_client else '❌'} AWS Textract: Textract Client: {'Available' if self.textract_client else 'Not Available'}")
            logger.info(f"{'✅' if self.s3_client else '❌'} AWS Textract: S3 Client: {'Available' if self.s3_client else 'Not Available'}")
            
            # Configuration
            try:
                from common.src.core.config import config
                logger.info(f"📁 AWS Textract: S3 Bucket: {config.s3_bucket}")
                logger.info(f"🌍 AWS Textract: Config Region: {getattr(config, 'aws_region', 'Not Set')}")
            except Exception as e:
                logger.error(f"❌ AWS Textract: Config access failed: {e}")
            
            logger.info("🔍 AWS Textract: === END DIAGNOSTICS ===")
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Environment diagnostics failed: {e}")

    def _log_textract_job_diagnostics(self, job_id: str, s3_bucket: str, s3_key: str):
        """
        Log detailed diagnostics for Textract job processing.
        """
        try:
            logger.info(f"🔍 AWS Textract: === JOB DIAGNOSTICS for {job_id} ===")
            logger.info(f"📦 AWS Textract: S3 Location: s3://{s3_bucket}/{s3_key}")
            
            # Check S3 file status
            try:
                if self.s3_client:
                    response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                    file_size = response.get('ContentLength', 0)
                    last_modified = response.get('LastModified')
                    content_type = response.get('ContentType', 'Unknown')
                    
                    logger.info(f"📦 AWS Textract: File Size: {file_size} bytes")
                    logger.info(f"📦 AWS Textract: Last Modified: {last_modified}")
                    logger.info(f"📦 AWS Textract: Content Type: {content_type}")
                    
                    if file_size == 0:
                        logger.error("❌ AWS Textract: WARNING - File is empty!")
                    elif file_size < 1024:
                        logger.warning("⚠️ AWS Textract: WARNING - File is very small (< 1KB)")
                    elif file_size > 50 * 1024 * 1024:  # 50MB
                        logger.warning("⚠️ AWS Textract: WARNING - File is very large (> 50MB)")
                else:
                    logger.error("❌ AWS Textract: S3 client not available for file check")
            except Exception as e:
                logger.error(f"❌ AWS Textract: S3 file check failed: {e}")
            
            # Check job status
            try:
                if self.textract_client:
                    result = self.textract_client.get_document_analysis(JobId=job_id)
                    status = result.get('JobStatus', 'Unknown')
                    status_message = result.get('StatusMessage', 'No message')
                    job_tag = result.get('JobTag', 'No tag')
                    
                    logger.info(f"📊 AWS Textract: Job Status: {status}")
                    logger.info(f"📊 AWS Textract: Status Message: {status_message}")
                    logger.info(f"📊 AWS Textract: Job Tag: {job_tag}")
                    
                    if status == 'FAILED':
                        logger.error(f"❌ AWS Textract: Job failed with message: {status_message}")
                    elif status == 'IN_PROGRESS':
                        logger.info("⏳ AWS Textract: Job is still in progress")
                    elif status == 'SUCCEEDED':
                        logger.info("✅ AWS Textract: Job completed successfully")
                else:
                    logger.error("❌ AWS Textract: Textract client not available for job check")
            except Exception as e:
                logger.error(f"❌ AWS Textract: Job status check failed: {e}")
            
            logger.info(f"🔍 AWS Textract: === END JOB DIAGNOSTICS ===")
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Job diagnostics failed: {e}")

    def _log_block_analysis_diagnostics(self, blocks: List[Dict[str, Any]], job_id: str):
        """
        Log detailed analysis of Textract blocks for debugging.
        """
        try:
            logger.info(f"🔍 AWS Textract: === BLOCK ANALYSIS for {job_id} ===")
            
            if not blocks:
                logger.warning("⚠️ AWS Textract: No blocks returned from Textract")
                return
            
            # Count block types
            block_types = {}
            page_count = 0
            line_count = 0
            word_count = 0
            
            for block in blocks:
                btype = block.get('BlockType', 'UNKNOWN')
                block_types[btype] = block_types.get(btype, 0) + 1
                
                if btype == 'PAGE':
                    page_count += 1
                elif btype == 'LINE':
                    line_count += 1
                elif btype == 'WORD':
                    word_count += 1
            
            logger.info(f"📊 AWS Textract: Total Blocks: {len(blocks)}")
            logger.info(f"📊 AWS Textract: Page Count: {page_count}")
            logger.info(f"📊 AWS Textract: Line Count: {line_count}")
            logger.info(f"📊 AWS Textract: Word Count: {word_count}")
            
            # Log block type distribution
            logger.info("📊 AWS Textract: Block Type Distribution:")
            for btype, count in sorted(block_types.items()):
                percentage = (count / len(blocks)) * 100
                logger.info(f"   {btype}: {count} ({percentage:.1f}%)")
            
            # Check for potential issues
            if line_count == 0:
                logger.error("❌ AWS Textract: CRITICAL - No LINE blocks found!")
                logger.error("❌ AWS Textract: This indicates the document may be:")
                logger.error("   - A scanned image with no OCR text")
                logger.error("   - An image-based PDF")
                logger.error("   - A document with very low quality")
                logger.error("   - A document in an unsupported format")
            elif line_count < 5:
                logger.warning("⚠️ AWS Textract: Very few LINE blocks found - document may have limited text")
            
            if word_count == 0:
                logger.error("❌ AWS Textract: CRITICAL - No WORD blocks found!")
            elif word_count < 10:
                logger.warning("⚠️ AWS Textract: Very few WORD blocks found - document may have minimal text")
            
            # Sample some LINE blocks for content analysis
            if line_count > 0:
                logger.info("📝 AWS Textract: Sample LINE blocks:")
                sample_lines = [block for block in blocks if block.get('BlockType') == 'LINE'][:5]
                for i, line_block in enumerate(sample_lines):
                    text = line_block.get('Text', '')
                    confidence = line_block.get('Confidence', 0)
                    logger.info(f"   Line {i+1}: '{text[:50]}{'...' if len(text) > 50 else ''}' (Confidence: {confidence:.1f}%)")
            
            logger.info(f"🔍 AWS Textract: === END BLOCK ANALYSIS ===")
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Block analysis diagnostics failed: {e}")

    # === NEW ASYNC DOCUMENT ANALYSIS METHODS (from working reference code) ===
    
    async def start_document_analysis_job(self, s3_bucket: str, s3_key: str, feature_types: List[str] = None) -> str:
        """
        Start an async document analysis job.
        Returns the job ID.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            if feature_types is None:
                feature_types = ["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
            
            logger.info(f"🚀 AWS Textract: Starting async job for s3://{s3_bucket}/{s3_key}")
            
            response = self.textract_client.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
                FeatureTypes=feature_types
            )
            
            job_id = response['JobId']
            logger.info(f"✅ AWS Textract: Job started successfully - ID: {job_id}")
            
            return job_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to start document analysis job: {error_code} - {error_message}")
            raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error starting document analysis job: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def wait_for_job_completion(self, job_id: str, poll_interval: int = 5) -> None:
        """
        Wait for a document analysis job to complete.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            logger.info(f"⏳ AWS Textract: Waiting for job completion - {job_id}")
            
            while True:
                result = self.textract_client.get_document_analysis(JobId=job_id)
                status = result['JobStatus']
                
                if status == 'SUCCEEDED':
                    logger.info(f"✅ AWS Textract: Job {job_id} completed successfully")
                    return
                elif status == 'FAILED':
                    error_message = result.get('StatusMessage', 'Unknown error')
                    logger.error(f"❌ AWS Textract: Job {job_id} failed: {error_message}")
                    raise TextractError(f"Textract job failed: {error_message}")
                elif status == 'IN_PROGRESS':
                    await asyncio.sleep(poll_interval)
                else:
                    logger.warning(f"⚠️ AWS Textract: Unknown job status: {status}")
                    await asyncio.sleep(poll_interval)
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Error checking job status: {error_code} - {error_message}")
            raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error waiting for job completion: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def get_all_blocks_from_job(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks from a completed document analysis job.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            logger.info(f"📥 AWS Textract: Retrieving blocks from job {job_id}")
            
            blocks = []
            next_token = None
            page_count = 0
            
            while True:
                if next_token:
                    response = self.textract_client.get_document_analysis(
                        JobId=job_id, 
                        NextToken=next_token
                    )
                else:
                    response = self.textract_client.get_document_analysis(JobId=job_id)
                
                current_blocks = response['Blocks']
                blocks.extend(current_blocks)
                
                # Count block types for debugging
                block_types = {}
                for block in current_blocks:
                    btype = block.get('BlockType', 'UNKNOWN')
                    block_types[btype] = block_types.get(btype, 0) + 1
                
                logger.info(f"📊 AWS Textract: Retrieved {len(current_blocks)} blocks in this batch")
                logger.info(f"📊 AWS Textract: Block types in this batch: {block_types}")
                
                next_token = response.get("NextToken")
                
                if not next_token:
                    break
            
            # Final analysis of all blocks
            total_block_types = {}
            for block in blocks:
                btype = block.get('BlockType', 'UNKNOWN')
                total_block_types[btype] = total_block_types.get(btype, 0) + 1
            
            logger.info(f"✅ AWS Textract: Retrieved {len(blocks)} total blocks from job {job_id}")
            logger.info(f"📊 AWS Textract: Total block types: {total_block_types}")
            
            # Check for potential issues
            if len(blocks) == 0:
                logger.warning("⚠️ AWS Textract: No blocks returned from Textract job")
            elif 'LINE' not in total_block_types:
                logger.warning("⚠️ AWS Textract: No LINE blocks found - document may be image-based")
            elif total_block_types.get('LINE', 0) == 0:
                logger.warning("⚠️ AWS Textract: 0 LINE blocks found - document may be scanned")
            
            return blocks
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Error retrieving blocks: {error_code} - {error_message}")
            raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving blocks: {e}")
            raise TextractError(f"Unexpected error: {e}")

    def organize_blocks_by_type(self, blocks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize blocks by their type for easier processing.
        """
        try:
            organized = {}
            for block in blocks:
                btype = block['BlockType']
                if btype not in organized:
                    organized[btype] = []
                
                organized[btype].append({
                    "Text": block.get("Text", ""),
                    "Confidence": block.get("Confidence"),
                    "Id": block.get("Id"),
                    "Page": block.get("Page"),
                    "TextType": block.get("TextType", ""),
                    "Geometry": block.get("Geometry", {}),
                    "EntityTypes": block.get("EntityTypes", []),
                    "SelectionStatus": block.get("SelectionStatus", ""),
                    "RowIndex": block.get("RowIndex"),
                    "ColumnIndex": block.get("ColumnIndex"),
                    "RowSpan": block.get("RowSpan"),
                    "ColumnSpan": block.get("ColumnSpan"),
                    "Relationships": block.get("Relationships", [])
                })
            
            logger.info(f"📊 AWS Textract: Organized {len(blocks)} blocks into {len(organized)} types")
            return organized
            
        except Exception as e:
            logger.error(f"Error organizing blocks: {e}")
            return {}

    async def process_document_async_comprehensive(self, s3_bucket: str, s3_key: str, 
                                                 feature_types: List[str] = None,
                                                 save_organized_blocks: bool = False,
                                                 output_file: str = None) -> Dict[str, Any]:
        """
        Process document using comprehensive async analysis (from working reference code).
        This is the main method that combines all async functionality.
        """
        try:
            logger.info(f"🚀 AWS Textract: Starting comprehensive processing for s3://{s3_bucket}/{s3_key}")
            
            # Run environment diagnostics first
            self._log_environment_diagnostics()
            
            if feature_types is None:
                feature_types = ["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
            
            # Start the async job
            job_id = await self.start_document_analysis_job(s3_bucket, s3_key, feature_types)
            
            # Log job diagnostics
            self._log_textract_job_diagnostics(job_id, s3_bucket, s3_key)
            
            # Wait for completion
            await self.wait_for_job_completion(job_id)
            
            # Get all blocks
            all_blocks = await self.get_all_blocks_from_job(job_id)
            
            # Log detailed block analysis
            self._log_block_analysis_diagnostics(all_blocks, job_id)
            
            # Organize blocks by type
            organized_blocks = self.organize_blocks_by_type(all_blocks)
            
            # Debug: Log block details
            logger.info(f"🔍 AWS Textract: Block analysis - Total: {len(all_blocks)}")
            for block_type, blocks in organized_blocks.items():
                logger.info(f"🔍 AWS Textract: {block_type}: {len(blocks)} blocks")
            
            # Prepare results
            results = {
                "job_id": job_id,
                "total_blocks": len(all_blocks),
                "organized_blocks": organized_blocks,
                "processing_method": "async_comprehensive",
                "feature_types": feature_types,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key
            }
            
            # Extract specific data types
            results.update(self._extract_specific_data_types(organized_blocks))
            
            # Save organized blocks if requested
            if save_organized_blocks:
                output_filename = output_file or f"textract_blocks_{job_id}.json"
                try:
                    with open(output_filename, "w") as f:
                        json.dump(organized_blocks, f, indent=2, ensure_ascii=False)
                    logger.info(f"💾 AWS Textract: Organized blocks saved to {output_filename}")
                    results["output_file"] = output_filename
                except Exception as e:
                    logger.error(f"❌ AWS Textract: Failed to save organized blocks: {e}")
            
            logger.info(f"✅ AWS Textract: Comprehensive processing completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive async document processing failed: {e}")
            raise TextractError(f"Async processing failed: {e}")

    def _extract_specific_data_types(self, organized_blocks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Extract specific data types from organized blocks.
        """
        extracted_data = {
            "text_lines": [],
            "paragraphs": [],
            "paragraphs_for_vector": [],
            "form_data": {},
            "tables": [],
            "signatures": [],
            "page_count": 0
        }
        
        try:
            # Extract text lines
            if "LINE" in organized_blocks:
                extracted_data["text_lines"] = [
                    block["Text"] for block in organized_blocks["LINE"] 
                    if block["Text"].strip()
                ]
            
            # Extract paragraphs (optimized for vector storage and AI generation)
            if "LINE" in organized_blocks:
                extracted_data["paragraphs"] = self.extract_paragraphs_from_blocks(organized_blocks)
                extracted_data["paragraphs_for_vector"] = self.extract_paragraphs_for_vector_storage(organized_blocks)
            
            # Extract page count
            if "PAGE" in organized_blocks:
                extracted_data["page_count"] = len(organized_blocks["PAGE"])
            
            # Extract form data (key-value pairs)
            if "KEY_VALUE_SET" in organized_blocks:
                extracted_data["form_data"] = self._extract_form_data_from_blocks(organized_blocks)
            
            # Extract tables
            if "TABLE" in organized_blocks:
                extracted_data["tables"] = self._extract_tables_from_blocks(organized_blocks)
            
            # Extract signatures
            if "SIGNATURE" in organized_blocks:
                extracted_data["signatures"] = [
                    block for block in organized_blocks["SIGNATURE"]
                ]
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error extracting specific data types: {e}")
        
        return extracted_data

    def _extract_form_data_from_blocks(self, organized_blocks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[str]]:
        """
        Extract form data (key-value pairs) from organized blocks.
        """
        try:
            from collections import defaultdict
            
            key_map = {}
            value_map = {}
            block_map = {}
            
            # Build block map
            for block_type, blocks in organized_blocks.items():
                for block in blocks:
                    block_map[block["Id"]] = block
            
            # Separate keys and values
            if "KEY_VALUE_SET" in organized_blocks:
                for block in organized_blocks["KEY_VALUE_SET"]:
                    if "KEY" in block.get("EntityTypes", []):
                        key_map[block["Id"]] = block
                    else:
                        value_map[block["Id"]] = block
            
            # Build key-value relationships
            kvs = defaultdict(list)
            for block_id, key_block in key_map.items():
                value_block = self._find_value_block_for_key(key_block, value_map)
                key = self._get_text_from_block(key_block, block_map)
                val = self._get_text_from_block(value_block, block_map)
                if key and val:
                    kvs[key].append(val)
            
            return dict(kvs)
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error extracting form data: {e}")
            return {}

    def _find_value_block_for_key(self, key_block: Dict[str, Any], value_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find the value block associated with a key block.
        """
        try:
            for relationship in key_block.get("Relationships", []):
                if relationship["Type"] == "VALUE":
                    for value_id in relationship["Ids"]:
                        if value_id in value_map:
                            return value_map[value_id]
            return {}
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error finding value block: {e}")
            return {}

    def _get_text_from_block(self, block: Dict[str, Any], block_map: Dict[str, Any]) -> str:
        """
        Extract text from a block by following relationships.
        """
        try:
            text = ""
            if "Relationships" in block:
                for relationship in block["Relationships"]:
                    if relationship["Type"] == "CHILD":
                        for child_id in relationship["Ids"]:
                            if child_id in block_map:
                                child_block = block_map[child_id]
                                if child_block["BlockType"] == "WORD":
                                    text += child_block["Text"] + " "
                                elif child_block["BlockType"] == "SELECTION_ELEMENT":
                                    if child_block.get("SelectionStatus") == "SELECTED":
                                        text += "X"
            return text.strip()
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error getting text from block: {e}")
            return ""

    def _extract_tables_from_blocks(self, organized_blocks: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Extract table data from organized blocks.
        """
        try:
            tables = []
            
            if "TABLE" in organized_blocks:
                for table_block in organized_blocks["TABLE"]:
                    table_data = {
                        "table_id": table_block["Id"],
                        "page": table_block.get("Page", 1),
                        "rows": [],
                        "cells": []
                    }
                    
                    # Extract cells for this table
                    if "Relationships" in table_block:
                        for relationship in table_block["Relationships"]:
                            if relationship["Type"] == "CHILD":
                                for cell_id in relationship["Ids"]:
                                    # Find cell block in organized blocks
                                    for block_type, blocks in organized_blocks.items():
                                        if block_type == "CELL":
                                            for cell_block in blocks:
                                                if cell_block["Id"] == cell_id:
                                                    table_data["cells"].append(cell_block)
                    
                    tables.append(table_data)
            
            return tables
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error extracting tables: {e}")
            return []

    def extract_paragraphs_from_blocks(self, organized_blocks: Dict[str, List[Dict[str, Any]]], 
                                     max_line_distance: float = 50.0,
                                     min_paragraph_length: int = 10) -> List[Dict[str, Any]]:
        """
        Extract paragraphs from organized blocks by combining related lines.
        This is optimized for vector storage and AI generation.
        
        Args:
            organized_blocks: Organized blocks by type
            max_line_distance: Maximum vertical distance between lines to consider them part of same paragraph
            min_paragraph_length: Minimum character length for a paragraph to be included
            
        Returns:
            List of paragraph objects with text, page, and metadata
        """
        try:
            paragraphs = []
            
            if "LINE" not in organized_blocks:
                logger.warning("⚠️ AWS Textract: No LINE blocks found for paragraph extraction")
                return paragraphs
            
            # Group lines by page
            lines_by_page = {}
            for line_block in organized_blocks["LINE"]:
                page = line_block.get("Page", 1)
                if page not in lines_by_page:
                    lines_by_page[page] = []
                lines_by_page[page].append(line_block)
            
            # Process each page separately
            for page_num, page_lines in lines_by_page.items():
                # Sort lines by vertical position (top to bottom)
                sorted_lines = sorted(page_lines, key=lambda x: x.get("Geometry", {}).get("BoundingBox", {}).get("Top", 0))
                
                current_paragraph = {
                    "text": "",
                    "page": page_num,
                    "lines": [],
                    "start_line_id": None,
                    "end_line_id": None,
                    "confidence": 0.0,
                    "word_count": 0
                }
                
                for i, line_block in enumerate(sorted_lines):
                    line_text = line_block.get("Text", "").strip()
                    if not line_text:
                        continue
                    
                    # Get line geometry
                    line_geometry = line_block.get("Geometry", {}).get("BoundingBox", {})
                    line_top = line_geometry.get("Top", 0)
                    line_height = line_geometry.get("Height", 0)
                    line_confidence = line_block.get("Confidence", 0)
                    
                    # Check if this line should be part of current paragraph
                    should_combine = False
                    
                    if current_paragraph["text"]:
                        # Get previous line geometry
                        prev_line = current_paragraph["lines"][-1] if current_paragraph["lines"] else None
                        if prev_line:
                            prev_geometry = prev_line.get("Geometry", {}).get("BoundingBox", {})
                            prev_top = prev_geometry.get("Top", 0)
                            prev_height = prev_geometry.get("Height", 0)
                            
                            # Calculate distance between lines
                            distance = abs(line_top - (prev_top + prev_height))
                            
                            # Combine if lines are close vertically and have similar formatting
                            should_combine = (
                                distance <= max_line_distance and
                                abs(line_height - prev_height) <= 0.1  # Similar line heights
                            )
                    
                    if should_combine:
                        # Add to current paragraph
                        current_paragraph["text"] += " " + line_text
                        current_paragraph["lines"].append(line_block)
                        current_paragraph["end_line_id"] = line_block["Id"]
                        current_paragraph["confidence"] = (current_paragraph["confidence"] + line_confidence) / 2
                        current_paragraph["word_count"] += len(line_text.split())
                    else:
                        # Save current paragraph if it meets minimum length
                        if len(current_paragraph["text"]) >= min_paragraph_length:
                            paragraphs.append(current_paragraph.copy())
                        
                        # Start new paragraph
                        current_paragraph = {
                            "text": line_text,
                            "page": page_num,
                            "lines": [line_block],
                            "start_line_id": line_block["Id"],
                            "end_line_id": line_block["Id"],
                            "confidence": line_confidence,
                            "word_count": len(line_text.split())
                        }
                
                # Don't forget the last paragraph
                if len(current_paragraph["text"]) >= min_paragraph_length:
                    paragraphs.append(current_paragraph)
            
            return paragraphs
            
        except Exception as e:
            logger.error(f"Error extracting paragraphs: {e}")
            return []

    def extract_paragraphs_for_vector_storage(self, organized_blocks: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Extract paragraphs optimized for vector storage and AI generation.
        This method creates meaningful text chunks that are ideal for embedding.
        """
        try:
            paragraphs = self.extract_paragraphs_from_blocks(organized_blocks)
            
            # Enhance paragraphs with additional metadata for vector storage
            enhanced_paragraphs = []
            
            for i, paragraph in enumerate(paragraphs):
                enhanced_paragraph = {
                    "id": f"paragraph_{i+1}",
                    "text": paragraph["text"],
                    "page": paragraph["page"],
                    "paragraph_index": i + 1,
                    "word_count": paragraph["word_count"],
                    "confidence": paragraph["confidence"],
                    "metadata": {
                        "start_line_id": paragraph["start_line_id"],
                        "end_line_id": paragraph["end_line_id"],
                        "line_count": len(paragraph["lines"]),
                        "processing_method": "paragraph_extraction",
                        "content_type": "paragraph"
                    }
                }
                
                # Add content type classification
                text_lower = paragraph["text"].lower()
                if any(word in text_lower for word in ["invoice", "bill", "payment", "amount", "total"]):
                    enhanced_paragraph["metadata"]["content_type"] = "financial"
                elif any(word in text_lower for word in ["date", "time", "schedule", "appointment"]):
                    enhanced_paragraph["metadata"]["content_type"] = "temporal"
                elif any(word in text_lower for word in ["name", "address", "contact", "phone", "email"]):
                    enhanced_paragraph["metadata"]["content_type"] = "contact"
                else:
                    enhanced_paragraph["metadata"]["content_type"] = "general"
                
                enhanced_paragraphs.append(enhanced_paragraph)
            
            return enhanced_paragraphs
            
        except Exception as e:
            logger.error(f"Error enhancing paragraphs for vector storage: {e}")
            return []

    # === EXISTING METHODS (keeping for backward compatibility) ===

    async def detect_document_text_lambda_style(self, s3_bucket: str, s3_key: str) -> Tuple[List[str], int]:
        """
        Extract text from document using Lambda-style DetectDocumentText approach.
        Returns list of text lines and page count.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                }
            )
            
            # Extract text using LINE blocks (Lambda-style)
            line_text = self._extract_text_lambda_style(response, extract_by="LINE")
            page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
            
            return line_text, page_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Lambda-style DetectDocumentText failed: {error_code} - {error_message}")
            raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in Lambda-style DetectDocumentText: {e}")
            raise TextractError(f"Unexpected error: {e}")

    def _extract_text_lambda_style(self, response: Dict[str, Any], extract_by: str = "LINE") -> List[str]:
        """
        Extract text from Textract response using Lambda-style approach.
        """
        try:
            line_text = []
            for block in response["Blocks"]:
                if block["BlockType"] == extract_by:
                    line_text.append(block["Text"])
            return line_text
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error extracting text Lambda-style: {e}")
            return []

    async def analyze_document_forms_lambda_style(self, s3_bucket: str, s3_key: str) -> Dict[str, List[str]]:
        """
        Analyze document for forms using Lambda-style approach.
        Returns key-value pairs extracted from forms.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            # Get key-value maps using Lambda-style approach
            key_map, value_map, block_map = await self._get_kv_map_lambda_style(s3_bucket, s3_key)
            
            # Get key-value relationships
            kvs = self._get_kv_relationship_lambda_style(key_map, value_map, block_map)
            
            return kvs
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Lambda-style form analysis failed: {error_code} - {error_message}")
            raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in Lambda-style form analysis: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def _get_kv_map_lambda_style(self, bucket: str, key: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Get key-value maps using Lambda-style approach.
        """
        try:
            # Process using image bytes
            response = self.textract_client.analyze_document(
                Document={'S3Object': {'Bucket': bucket, "Name": key}}, 
                FeatureTypes=['FORMS']
            )

            # Get the text blocks
            blocks = response['Blocks']

            # Get key and value maps
            key_map = {}
            value_map = {}
            block_map = {}
            
            for block in blocks:
                block_id = block['Id']
                block_map[block_id] = block
                if block['BlockType'] == "KEY_VALUE_SET":
                    if 'KEY' in block['EntityTypes']:
                        key_map[block_id] = block
                    else:
                        value_map[block_id] = block

            return key_map, value_map, block_map
            
        except Exception as e:
            logger.error(f"Error getting KV maps Lambda-style: {e}")
            return {}, {}, {}

    def _get_kv_relationship_lambda_style(self, key_map: Dict[str, Any], value_map: Dict[str, Any], block_map: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get key-value relationships using Lambda-style approach.
        """
        try:
            from collections import defaultdict
            kvs = defaultdict(list)
            
            for block_id, key_block in key_map.items():
                value_block = self._find_value_block_lambda_style(key_block, value_map)
                key = self._get_text_lambda_style(key_block, block_map)
                val = self._get_text_lambda_style(value_block, block_map)
                kvs[key].append(val)
            
            return dict(kvs)
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error getting KV relationships Lambda-style: {e}")
            return {}

    def _find_value_block_lambda_style(self, key_block: Dict[str, Any], value_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find value block for a key block using Lambda-style approach.
        """
        try:
            for relationship in key_block['Relationships']:
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        if value_id in value_map:
                            return value_map[value_id]
            return {}
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error finding value block Lambda-style: {e}")
            return {}

    def _get_text_lambda_style(self, result: Dict[str, Any], blocks_map: Dict[str, Any]) -> str:
        """
        Get text from a block using Lambda-style approach.
        """
        try:
            text = ''
            if 'Relationships' in result:
                for relationship in result['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            if child_id in blocks_map:
                                word = blocks_map[child_id]
                                if word['BlockType'] == 'WORD':
                                    text += word['Text'] + ' '
                                if word['BlockType'] == 'SELECTION_ELEMENT':
                                    if word['SelectionStatus'] == 'SELECTED':
                                        text += 'X'
            return text.strip()
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error getting text Lambda-style: {e}")
            return ""

    async def process_document_lambda_style(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        """
        Process document using Lambda-style approach combining text detection and form analysis.
        """
        try:
            results = {
                "text_lines": [],
                "form_data": {},
                "page_count": 0,
                "processing_method": "lambda_style"
            }
            
            # Try text detection first
            try:
                text_lines, page_count = await self.detect_document_text_lambda_style(s3_bucket, s3_key)
                results["text_lines"] = text_lines
                results["page_count"] = page_count
            except Exception as e:
                logger.warning(f"⚠️ AWS Textract: Lambda-style text detection failed: {e}")
            
            # Try form analysis
            try:
                form_data = await self.analyze_document_forms_lambda_style(s3_bucket, s3_key)
                results["form_data"] = form_data
            except Exception as e:
                logger.warning(f"⚠️ AWS Textract: Lambda-style form analysis failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Lambda-style document processing failed: {e}")
            raise TextractError(f"Lambda-style processing failed: {e}")

    async def process_preprocessed_document(self, s3_bucket: str, s3_key: str, document_type: DocumentType = DocumentType.GENERAL) -> Tuple[str, int]:
        """
        Process a preprocessed document using Textract.
        This method is called by document_service.py for preprocessed documents.
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 key for the document
            document_type: Type of document to process
            
        Returns:
            Tuple of (text_content, page_count)
        """
        try:
            logger.info(f"📄 AWS Textract: Processing preprocessed document s3://{s3_bucket}/{s3_key} (type: {document_type.value})")
            
            # Use the comprehensive async processing for preprocessed documents
            results = await self.process_document_async_comprehensive(
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                feature_types=["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
            )
            
            # Extract text content from paragraphs for better quality
            text_content = ""
            if results.get("paragraphs_for_vector"):
                # Use vector-optimized paragraphs for better text quality
                paragraph_texts = [p["text"] for p in results["paragraphs_for_vector"]]
                text_content = "\n\n".join(paragraph_texts)
            elif results.get("text_lines"):
                # Fallback to text lines if paragraphs not available
                text_content = "\n".join(results["text_lines"])
            
            page_count = results.get("page_count", 1)
            
            logger.info(f"✅ AWS Textract: Preprocessed document completed - {len(text_content)} chars, {page_count} pages")
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Error processing preprocessed document: {e}")
            raise TextractError(f"Failed to process preprocessed document: {e}")

    async def upload_to_s3_and_extract(self, content: bytes, filename: str, document_type: DocumentType = DocumentType.GENERAL, user_id: str = "anonymous") -> Tuple[str, int]:
        """
        Upload document content to S3 and extract text using Textract.
        This method is called by document_service.py for direct document processing.
        
        Args:
            content: Document content as bytes
            filename: Original filename
            document_type: Type of document to process
            user_id: User ID for organization
            
        Returns:
            Tuple of (text_content, page_count)
        """
        try:
            logger.info(f"📤 AWS Textract: Uploading and extracting {filename} (type: {document_type.value})")
            
            # Import unified storage service
            from common.src.services.unified_storage_service import unified_storage_service
            
            # Upload to S3
            upload_result = await unified_storage_service.upload_temp_file(
                file_content=content,
                filename=filename,
                purpose="textract_processing",
                user_id=user_id
            )
            
            s3_key = upload_result["s3_key"]
            
            # Import config here to avoid reference before assignment error
            from common.src.core.config import config
            
            complete_s3_path = f"s3://{config.s3_bucket}/{s3_key}"
            logger.info(f"📁 AWS Textract: Document uploaded to S3")
            logger.info(f"📁 AWS Textract: Complete S3 path: {complete_s3_path}")
            logger.info(f"📁 AWS Textract: S3 key: {s3_key}")
            logger.info(f"📁 AWS Textract: Processing purpose: textract_processing")
            
            # Process with Textract using environment-appropriate method
            is_lambda = self._is_running_in_lambda()
            
            if is_lambda:
                # Use Lambda-optimized processing
                logger.info(f"⚡ AWS Textract: Using Lambda-optimized processing for direct upload")
                text_content, page_count = await self.process_document_lambda_optimized(
                    s3_bucket=config.s3_bucket,
                    s3_key=s3_key,
                    document_type=document_type
                )
            else:
                # Use regular processing for local environment
                text_content, page_count = await self.process_preprocessed_document(
                    s3_bucket=config.s3_bucket,
                    s3_key=s3_key,
                    document_type=document_type
                )
            
            # If no text content extracted, try PDF to image fallback (only for local environment)
            if not is_lambda and (not text_content or len(text_content.strip()) == 0):
                logger.warning("⚠️ AWS Textract: No text content extracted — trying PDF to image fallback")
                try:
                    text_content, page_count = await self.fallback_textract_on_pdf_images(
                        content, config.s3_bucket, document_type
                    )
                except Exception as fallback_error:
                    logger.error(f"❌ AWS Textract: PDF to image fallback failed: {fallback_error}")
                    # Continue with empty content as last resort
            
            # Clean up temporary file
            try:
                await unified_storage_service.delete_file(s3_key)
                logger.info(f"🧹 AWS Textract: Cleaned up temporary file: {s3_key}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ AWS Textract: Failed to cleanup temporary file {s3_key}: {cleanup_error}")
            
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Error uploading and extracting document: {e}")
            raise TextractError(f"Failed to upload and extract document: {e}")

    async def process_document_lambda_optimized(self, s3_bucket: str, s3_key: str, document_type: DocumentType = DocumentType.GENERAL) -> Tuple[str, int]:
        """
        Lambda-optimized document processing that uses sync Textract calls for faster processing.
        This method is designed to complete within Lambda timeout limits.
        """
        try:
            logger.info(f"⚡ AWS Textract: Lambda-optimized processing for s3://{s3_bucket}/{s3_key}")
            
            # Check Lambda timeout constraints
            import time
            start_time = time.time()
            max_processing_time = 25  # Leave 5 seconds buffer for Lambda timeout
            
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            # Try sync text detection first (faster than async)
            try:
                logger.info(f"⚡ AWS Textract: Attempting sync text detection")
                response = self.textract_client.detect_document_text(
                    Document={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}}
                )
                
                # Check if we got meaningful text
                line_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'LINE']
                word_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'WORD']
                
                logger.info(f"⚡ AWS Textract: Sync detection found {len(line_blocks)} lines, {len(word_blocks)} words")
                
                if line_blocks:
                    # Extract text from LINE blocks
                    text_lines = [block['Text'] for block in line_blocks]
                    text_content = '\n'.join(text_lines)
                    page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
                    
                    logger.info(f"✅ AWS Textract: Lambda-optimized sync processing completed - {len(text_content)} chars, {page_count} pages")
                    return text_content, page_count
                
            except Exception as sync_error:
                logger.warning(f"⚠️ AWS Textract: Sync detection failed: {sync_error}")
            
            # Check timeout
            if time.time() - start_time > max_processing_time:
                logger.error("❌ AWS Textract: Processing timeout - switching to fallback")
                return await self._quick_fallback_processing(s3_bucket, s3_key, document_type)
            
            # Try sync form analysis if no text found
            try:
                logger.info(f"⚡ AWS Textract: Attempting sync form analysis")
                response = self.textract_client.analyze_document(
                    Document={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
                    FeatureTypes=['FORMS']
                )
                
                # Extract text from form blocks
                text_content = self._extract_text_from_form_blocks(response['Blocks'])
                
                if text_content:
                    page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
                    logger.info(f"✅ AWS Textract: Lambda-optimized form processing completed - {len(text_content)} chars, {page_count} pages")
                    return text_content, page_count
                
            except Exception as form_error:
                logger.warning(f"⚠️ AWS Textract: Form analysis failed: {form_error}")
            
            # Check timeout again
            if time.time() - start_time > max_processing_time:
                logger.error("❌ AWS Textract: Processing timeout - switching to fallback")
                return await self._quick_fallback_processing(s3_bucket, s3_key, document_type)
            
            # If we still have time, try one page of PDF to image conversion
            logger.warning("⚠️ AWS Textract: No text found with sync methods - trying single page conversion")
            return await self._quick_fallback_processing(s3_bucket, s3_key, document_type)
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Lambda-optimized processing failed: {e}")
            raise TextractError(f"Lambda-optimized processing failed: {e}")

    def _extract_text_from_form_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract text from form analysis blocks.
        """
        try:
            text_lines = []
            
            # Extract text from KEY_VALUE_SET blocks
            for block in blocks:
                if block['BlockType'] == 'KEY_VALUE_SET':
                    # Get the text from key-value relationships
                    if 'Relationships' in block:
                        for relationship in block['Relationships']:
                            if relationship['Type'] == 'CHILD':
                                for child_id in relationship['Ids']:
                                    # Find the child block
                                    child_block = next((b for b in blocks if b['Id'] == child_id), None)
                                    if child_block and child_block['BlockType'] == 'WORD':
                                        text_lines.append(child_block['Text'])
            
            # Also extract from regular LINE blocks
            for block in blocks:
                if block['BlockType'] == 'LINE':
                    text_lines.append(block['Text'])
            
            return ' '.join(text_lines)
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Error extracting text from form blocks: {e}")
            return ""

    async def _quick_fallback_processing(self, s3_bucket: str, s3_key: str, document_type: DocumentType) -> Tuple[str, int]:
        """
        Quick fallback processing that converts only the first page to image for speed.
        """
        try:
            logger.info(f"⚡ AWS Textract: Quick fallback processing - converting first page only")
            
            # Download PDF content
            self._ensure_clients_initialized()
            pdf_obj = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            pdf_bytes = pdf_obj["Body"].read()
            
            # Convert only first page to image
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=1)  # Only first page
                
                if not images:
                    logger.warning("⚠️ AWS Textract: No images generated from PDF")
                    return "", 1
                
                image = images[0]
                
                # Save image to temporary file
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    image.save(tmp_file.name, "PNG")
                    
                    # Read image bytes
                    with open(tmp_file.name, "rb") as img_file:
                        image_bytes = img_file.read()
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                
                # Use sync text detection on the image
                response = self.textract_client.detect_document_text(
                    Document={'Bytes': image_bytes}
                )
                
                # Extract text
                line_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'LINE']
                text_lines = [block['Text'] for block in line_blocks]
                text_content = '\n'.join(text_lines)
                
                logger.info(f"✅ AWS Textract: Quick fallback completed - {len(text_content)} chars, 1 page")
                return text_content, 1
                
            except ImportError:
                logger.error("❌ AWS Textract: pdf2image not available for quick fallback")
                return "", 1
            except Exception as e:
                logger.error(f"❌ AWS Textract: Quick fallback failed: {e}")
                return "", 1
                
        except Exception as e:
            logger.error(f"❌ AWS Textract: Quick fallback processing failed: {e}")
            return "", 1

    async def extract_text_from_s3_pdf(self, s3_bucket: str, s3_key: str, document_type: DocumentType = DocumentType.GENERAL) -> Tuple[str, int]:
        """
        Extract text from PDF stored in S3 using Textract.
        This method is called by unified_document_processor.py.
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 key for the PDF
            document_type: Type of document to process
            
        Returns:
            Tuple of (text_content, page_count)
        """
        try:
            logger.info(f"📄 AWS Textract: Extracting text from S3 PDF s3://{s3_bucket}/{s3_key} (type: {document_type.value})")
            
            # Environment detection
            is_lambda = self._is_running_in_lambda()
            logger.info(f"🔧 AWS Textract: Running in {'Lambda' if is_lambda else 'Local'} environment")
            
            # Use Lambda-optimized processing in Lambda environment
            if is_lambda:
                logger.info(f"⚡ AWS Textract: Using Lambda-optimized processing")
                return await self.process_document_lambda_optimized(s3_bucket, s3_key, document_type)
            
            # Run comprehensive diagnostics for local environment
            self._log_environment_diagnostics()
            
            # Validate S3 file before processing
            if not self._validate_s3_file(s3_bucket, s3_key):
                logger.error("❌ AWS Textract: S3 file validation failed, cannot proceed")
                raise TextractError("S3 file validation failed")
            
            # Use the comprehensive async processing for local environment
            results = await self.process_document_async_comprehensive(
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                feature_types=["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
            )
            
            # Check if we got any LINE blocks (text content)
            organized_blocks = results.get("organized_blocks", {})
            line_count = len(organized_blocks.get("LINE", []))
            total_blocks = results.get("total_blocks", 0)
            
            logger.info(f"🔍 AWS Textract: Found block types: {list(organized_blocks.keys())}")
            logger.info(f"🔍 AWS Textract: Total blocks: {total_blocks}")
            logger.info(f"🔍 AWS Textract: LINE blocks found: {line_count}")
            
            # Fallback logic for local environment
            if line_count == 0:
                logger.warning("⚠️ AWS Textract: No LINE blocks found — fallback to image conversion")
                try:
                    # Download PDF content from S3
                    self._ensure_clients_initialized()
                    pdf_obj = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
                    pdf_bytes = pdf_obj["Body"].read()
                    return await self.fallback_textract_on_pdf_images(pdf_bytes, s3_bucket, document_type)
                except Exception as fallback_error:
                    logger.error(f"❌ AWS Textract: PDF to image fallback failed: {fallback_error}")
                    # Continue with normal processing as last resort
            
            # Extract text content from paragraphs for better quality
            text_content = ""
            
            if results.get("paragraphs_for_vector"):
                # Use vector-optimized paragraphs for better text quality
                paragraph_texts = [p["text"] for p in results["paragraphs_for_vector"]]
                text_content = "\n\n".join(paragraph_texts)
                logger.info(f"📝 AWS Textract: Using paragraphs_for_vector - {len(paragraph_texts)} paragraphs")
            elif results.get("text_lines"):
                # Fallback to text lines if paragraphs not available
                text_content = "\n".join(results["text_lines"])
                logger.info(f"📝 AWS Textract: Using text_lines - {len(results['text_lines'])} lines")
            else:
                logger.warning(f"⚠️ AWS Textract: No text content found in any format")
            
            page_count = results.get("page_count", 1)
            
            logger.info(f"✅ AWS Textract: S3 PDF extraction completed - {len(text_content)} chars, {page_count} pages")
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Error extracting text from S3 PDF: {e}")
            raise TextractError(f"Failed to extract text from S3 PDF: {e}")

    async def _try_pypdf2_extraction(self, file_content: bytes, filename: str) -> Tuple[str, int]:
        """
        Try PyPDF2 extraction as a fallback method.
        This method is called by unified_document_processor.py.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (text_content, page_count)
        """
        try:
            logger.info(f"🔄 AWS Textract: Trying PyPDF2 fallback for {filename}")
            
            # Import PyPDF2
            try:
                import PyPDF2
            except ImportError:
                logger.warning("⚠️ AWS Textract: PyPDF2 not available, skipping extraction")
                return "", 0
            
            # Create PDF reader from bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            # Extract text from all pages
            text_content = ""
            page_count = len(pdf_reader.pages)
            
            for page_num in range(page_count):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                except Exception as page_error:
                    logger.warning(f"⚠️ AWS Textract: Error extracting text from page {page_num}: {page_error}")
                    continue
            
            logger.info(f"✅ AWS Textract: PyPDF2 fallback completed - {len(text_content)} chars, {page_count} pages")
            return text_content.strip(), page_count
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return "", 0

    async def _try_aggressive_text_extraction(self, file_content: bytes, filename: str) -> str:
        """
        Try aggressive text extraction using regex patterns.
        This method is called by unified_document_processor.py.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"🔄 AWS Textract: Trying aggressive text extraction for {filename}")
            
            # Try to decode as text first
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    logger.warning("⚠️ AWS Textract: Could not decode file content as text")
                    return ""
            
            # Apply aggressive cleaning
            import re
            
            # Remove common PDF artifacts
            text_content = re.sub(r'\x00', '', text_content)  # Remove null bytes
            text_content = re.sub(r'[^\x20-\x7E\n\r\t]', '', text_content)  # Keep only printable ASCII
            
            # Remove excessive whitespace
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)  # Multiple newlines to double newlines
            text_content = re.sub(r' +', ' ', text_content)  # Multiple spaces to single space
            
            # Remove common PDF headers/footers
            text_content = re.sub(r'Page \d+ of \d+', '', text_content)
            text_content = re.sub(r'^\d+$', '', text_content, flags=re.MULTILINE)  # Remove standalone page numbers
            
            # Clean up
            text_content = text_content.strip()
            
            logger.info(f"✅ AWS Textract: Aggressive text extraction completed - {len(text_content)} chars")
            return text_content
            
        except Exception as e:
            logger.error(f"Aggressive text extraction failed: {e}")
            return ""

    async def _try_raw_text_extraction(self, file_content: bytes, filename: str) -> str:
        """
        Try raw text extraction for image files.
        This method is called by unified_document_processor.py.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"🔄 AWS Textract: Trying raw text extraction for {filename}")
            
            # For images, we can't extract text without OCR
            # This is a placeholder for future OCR implementation
            logger.warning("⚠️ AWS Textract: Raw text extraction not implemented for images (requires OCR)")
            return ""
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: Raw text extraction failed: {e}")
            return ""

    async def fallback_textract_on_pdf_images(self, pdf_content: bytes, s3_bucket: str, document_type: DocumentType) -> Tuple[str, int]:
        """
        Fallback method: Convert PDF to images and process with Textract.
        This handles scanned PDFs that don't have extractable text.
        """
        try:
            logger.warning("🌀 AWS Textract: Converting PDF to images and re-processing...")
            
            # Try to import pdf2image
            try:
                from pdf2image import convert_from_bytes
            except ImportError:
                logger.error("❌ AWS Textract: pdf2image not available. Install with: pip install pdf2image")
                raise TextractError("pdf2image not available for PDF to image conversion")
            
            # Convert PDF to images
            images = convert_from_bytes(pdf_content, dpi=300)
            combined_text = []
            page_count = len(images)
            
            logger.info(f"🔄 AWS Textract: Converted PDF to {page_count} images")
            
            for i, image in enumerate(images):
                logger.info(f"🔄 AWS Textract: Processing page {i+1}/{page_count}")
                
                # Save image to temporary file
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    image.save(tmp_file.name, "PNG")
                    
                    # Read image bytes
                    with open(tmp_file.name, "rb") as img_file:
                        image_bytes = img_file.read()
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                
                # Upload image to S3
                from common.src.services.unified_storage_service import unified_storage_service
                upload_result = await unified_storage_service.upload_temp_file(
                    file_content=image_bytes,
                    filename=f"fallback_page_{i+1}.png",
                    purpose="textract_fallback",
                    user_id="system"
                )
                s3_key = upload_result["s3_key"]
                
                # Process image with Textract
                try:
                    text_content, _ = await self.process_preprocessed_document(
                        s3_bucket=s3_bucket,
                        s3_key=s3_key,
                        document_type=document_type
                    )
                    combined_text.append(text_content)
                    logger.info(f"✅ AWS Textract: Page {i+1} processed - {len(text_content)} chars")
                except Exception as page_error:
                    logger.warning(f"⚠️ AWS Textract: Error processing page {i+1}: {page_error}")
                    combined_text.append("")  # Empty text for failed pages
                finally:
                    # Clean up temporary image
                    try:
                        await unified_storage_service.delete_file(s3_key)
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ AWS Textract: Failed to cleanup temp image {s3_key}: {cleanup_error}")
            
            final_text = "\n\n".join(combined_text)
            logger.info(f"✅ AWS Textract: PDF to image fallback completed - {len(final_text)} chars, {page_count} pages")
            return final_text, page_count
            
        except Exception as e:
            logger.error(f"❌ AWS Textract: PDF to image fallback failed: {e}")
            raise TextractError(f"PDF to image fallback failed: {e}")

# Global instance
textract_service = AWSTextractService() 