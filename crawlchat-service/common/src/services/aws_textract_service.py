"""
AWS Textract Service for document text extraction
Implements the recommended architecture with S3-based processing
"""

import logging
import os
import io
import asyncio
import time
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.aws_config import aws_config
from ..core.exceptions import TextractError
from .storage_service import get_storage_service


logger = logging.getLogger(__name__)

class TextractAPI(Enum):
    """Textract API types for different use cases."""
    DETECT_DOCUMENT_TEXT = "detect_document_text"  # Default, cheaper
    ANALYZE_DOCUMENT = "analyze_document"  # For forms/tables, more expensive

class DocumentType(Enum):
    """Document types for API selection."""
    GENERAL = "general"  # Use DetectDocumentText
    FORM = "form"  # Use AnalyzeDocument
    INVOICE = "invoice"  # Use AnalyzeDocument
    TABLE_HEAVY = "table_heavy"  # Use AnalyzeDocument

class AWSTextractService:
    """AWS Textract service for document text extraction."""
    
    def __init__(self):
        """Initialize the Textract service."""
        self.textract_client = None
        self.s3_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients."""
        try:
            # Initialize Textract client
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                logger.info("Running in Lambda environment, using IAM role for AWS clients")
                self.textract_client = boto3.client('textract', region_name=aws_config.textract_region)
                self.s3_client = boto3.client('s3', region_name=aws_config.region)
            else:
                # Running locally - use credentials if available
                if aws_config.access_key_id and aws_config.secret_access_key:
                    logger.info("Running locally, using provided AWS credentials")
                    self.textract_client = boto3.client(
                        'textract',
                        aws_access_key_id=aws_config.access_key_id,
                        aws_secret_access_key=aws_config.secret_access_key,
                        region_name=aws_config.textract_region
                    )
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=aws_config.access_key_id,
                        aws_secret_access_key=aws_config.secret_access_key,
                        region_name=aws_config.region
                    )
                else:
                    logger.warning("AWS credentials not available for local environment")
                    self.textract_client = None
                    self.s3_client = None
            
            if self.textract_client:
                logger.info(f"Textract client initialized successfully in region: {aws_config.textract_region}")
            if self.s3_client:
                logger.info(f"S3 client initialized successfully in region: {aws_config.region}")
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.textract_client = None
            self.s3_client = None
    
    async def extract_text_from_s3_pdf(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        document_type: DocumentType = DocumentType.GENERAL
    ) -> (str, int):
        """
        Extract text from PDF stored in S3 using AWS Textract.
        Assumes the document has been preprocessed and normalized.
        Returns (text_content, page_count)
        """
        try:
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            if not self.s3_client:
                raise TextractError("AWS S3 client not available")
            
            # Wait for S3 object to be available
            if not await self._wait_for_s3_object(s3_bucket, s3_key):
                raise TextractError(f"S3 object {s3_key} not available after waiting")
            
            # Process with Textract
            logger.info(f"Processing document {s3_key} with Textract")
            api_type = self._select_api_type(document_type)
            logger.info(f"Using API: {api_type.value}")
            
            if api_type == TextractAPI.DETECT_DOCUMENT_TEXT:
                text_content, page_count = await self._detect_document_text_with_retry(s3_bucket, s3_key)
            else:
                text_content, page_count = await self._analyze_document_with_retry(s3_bucket, s3_key)
            
            # Check if we got meaningful text
            if text_content and len(text_content.strip()) > 10:
                logger.info(f"✅ Textract succeeded: {len(text_content)} characters extracted")
                return text_content, page_count
            else:
                raise TextractError("Textract returned empty or minimal text")
                    
        except Exception as e:
            logger.error(f"Error extracting text from S3 PDF {s3_key}: {e}")
            raise TextractError(f"Textract extraction failed: {e}")

    async def _wait_for_s3_object(self, s3_bucket: str, s3_key: str, max_wait: int = 10) -> bool:
        """
        Wait for S3 object to be available before calling Textract.
        This is the proper fix for S3 eventual consistency.
        """
        logger.info(f"DEBUG: Waiting for S3 object s3://{s3_bucket}/{s3_key} (max wait: {max_wait}s)")
        start_time = time.time()
        attempt = 0
        while time.time() - start_time < max_wait:
            attempt += 1
            try:
                # Use head_object to check if the object exists and is accessible
                logger.info(f"DEBUG: Attempt {attempt} - checking S3 object availability")
                response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                wait_time = time.time() - start_time
                logger.info(f"DEBUG: S3 object {s3_key} is available after {wait_time:.2f}s (attempt {attempt})")
                logger.info(f"DEBUG: S3 object size: {response.get('ContentLength', 'unknown')} bytes")
                logger.info(f"DEBUG: S3 object ETag: {response.get('ETag', 'unknown')}")
                logger.info(f"DEBUG: S3 object LastModified: {response.get('LastModified', 'unknown')}")
                return True
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404' or error_code == 'NoSuchKey':
                    # Object not found yet, wait and retry
                    elapsed = time.time() - start_time
                    logger.info(f"DEBUG: S3 object not found yet, waiting... (elapsed: {elapsed:.2f}s, attempt {attempt})")
                    await asyncio.sleep(1.0)  # Check every 1 second
                    continue
                else:
                    # Other S3 error, don't retry
                    logger.error(f"DEBUG: S3 error checking object {s3_key}: {error_code} - {e.response['Error'].get('Message', '')}")
                    return False
            except Exception as e:
                logger.error(f"DEBUG: Unexpected error checking S3 object {s3_key}: {e}")
                return False
        
        logger.warning(f"DEBUG: S3 object {s3_key} not available after {max_wait}s ({attempt} attempts)")
        return False

    async def _detect_document_text_with_retry(self, s3_bucket: str, s3_key: str, max_retries: int = 3) -> (str, int):
        """
        Call DetectDocumentText with retry logic.
        S3 object availability is checked before calling this method.
        """
        return await self._detect_document_text(s3_bucket, s3_key)

    async def _analyze_document_with_retry(self, s3_bucket: str, s3_key: str, max_retries: int = 3) -> (str, int):
        """
        Call AnalyzeDocument with retry logic.
        S3 object availability is checked before calling this method.
        """
        return await self._analyze_document(s3_bucket, s3_key)

    def _select_api_type(self, document_type: DocumentType) -> TextractAPI:
        """
        Select the appropriate Textract API based on document type.
        """
        if document_type in [DocumentType.FORM, DocumentType.INVOICE, DocumentType.TABLE_HEAVY]:
            return TextractAPI.ANALYZE_DOCUMENT
        else:
            return TextractAPI.DETECT_DOCUMENT_TEXT

    async def _detect_document_text(self, s3_bucket: str, s3_key: str) -> (str, int):
        """
        Call AWS Textract DetectDocumentText API.
        """
        try:
            logger.info(f"Calling DetectDocumentText for s3://{s3_bucket}/{s3_key}")
            
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                }
            )
            
            # Log response structure for debugging
            logger.info(f"Textract response keys: {list(response.keys())}")
            logger.info(f"Number of blocks returned: {len(response.get('Blocks', []))}")
            
            # Extract text from blocks
            text_content = self._extract_text_from_blocks(response['Blocks'])
            page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
            
            logger.info(f"DetectDocumentText completed: {len(text_content)} characters, {page_count} pages")
            
            # Check if we got meaningful text
            if not text_content or len(text_content.strip()) < 10:
                logger.warning(f"Textract returned minimal text for {s3_key}: '{text_content[:100]}...'")
                # Log some block details for debugging
                block_types = {}
                for block in response['Blocks'][:10]:  # First 10 blocks
                    block_type = block.get('BlockType', 'UNKNOWN')
                    block_types[block_type] = block_types.get(block_type, 0) + 1
                logger.info(f"First 10 block types: {block_types}")
                
                # Try to get any text from blocks
                all_text = []
                for block in response['Blocks']:
                    if 'Text' in block and block['Text'].strip():
                        all_text.append(block['Text'])
                
                if all_text:
                    fallback_text = ' '.join(all_text)
                    logger.info(f"Fallback text extraction: {len(fallback_text)} characters")
                    return fallback_text, page_count
                else:
                    raise TextractError("Textract returned empty or minimal text")
            
            return text_content, page_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Textract DetectDocumentText failed: {error_code} - {error_message}")
            
            if error_code == 'UnsupportedDocumentException':
                raise TextractError(f"Unsupported document type: {error_message}")
            elif error_code == 'InvalidS3ObjectException':
                raise TextractError(f"Invalid S3 object: {error_message}")
            else:
                raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in DetectDocumentText: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def _detect_document_text_with_enhanced_params(self, s3_bucket: str, s3_key: str) -> (str, int):
        """
        Call AWS Textract DetectDocumentText API with enhanced parameters for better image processing.
        """
        try:
            logger.info(f"Calling DetectDocumentText with enhanced params for s3://{s3_bucket}/{s3_key}")
            
            # Try with different parameters for better image processing
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                # Add parameters for better image processing
                FeatureTypes=['TABLES', 'FORMS']  # This might help with complex images
            )
            
            # Log response structure for debugging
            logger.info(f"Enhanced Textract response keys: {list(response.keys())}")
            logger.info(f"Number of blocks returned: {len(response.get('Blocks', []))}")
            
            # Extract text from blocks
            text_content = self._extract_text_from_blocks(response['Blocks'])
            page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
            
            logger.info(f"Enhanced DetectDocumentText completed: {len(text_content)} characters, {page_count} pages")
            
            return text_content, page_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Enhanced Textract DetectDocumentText failed: {error_code} - {error_message}")
            raise TextractError(f"Enhanced Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in enhanced DetectDocumentText: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def _try_enhanced_image_extraction(self, s3_bucket: str, s3_key: str) -> (str, int):
        """
        Try enhanced image extraction with different Textract parameters.
        """
        try:
            # First try the standard method
            text_content, page_count = await self._detect_document_text(s3_bucket, s3_key)
            
            # If we got meaningful text, return it
            if text_content and len(text_content.strip()) > 10:
                return text_content, page_count
            
            # If standard method failed, try enhanced parameters
            logger.info(f"Standard Textract failed, trying enhanced parameters for {s3_key}")
            return await self._detect_document_text_with_enhanced_params(s3_bucket, s3_key)
            
        except Exception as e:
            logger.warning(f"Enhanced image extraction failed: {e}")
            raise

    async def _analyze_document(self, s3_bucket: str, s3_key: str) -> (str, int):
        """
        Call AWS Textract AnalyzeDocument API.
        """
        try:
            logger.info(f"Calling AnalyzeDocument for s3://{s3_bucket}/{s3_key}")
            
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            # Extract structured text from blocks
            text_content = self._extract_structured_text_from_blocks(response['Blocks'])
            page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
            
            logger.info(f"AnalyzeDocument completed: {len(text_content)} characters, {page_count} pages")
            return text_content, page_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Textract AnalyzeDocument failed: {error_code} - {error_message}")
            
            if error_code == 'UnsupportedDocumentException':
                raise TextractError(f"Unsupported document type: {error_message}")
            elif error_code == 'InvalidS3ObjectException':
                raise TextractError(f"Invalid S3 object: {error_message}")
            else:
                raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in AnalyzeDocument: {e}")
            raise TextractError(f"Unexpected error: {e}")

    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Textract blocks.
        """
        try:
            # Log block types for debugging
            block_types = {}
            for block in blocks:
                block_type = block.get('BlockType', 'UNKNOWN')
                block_types[block_type] = block_types.get(block_type, 0) + 1
            
            logger.info(f"Textract returned blocks: {block_types}")
            
            text_lines = []
            current_line = []
            current_line_id = None
            
            # Sort blocks by page, then by geometry (top to bottom, left to right)
            sorted_blocks = sorted(blocks, key=lambda b: (
                b.get('Page', 0),
                b.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0),
                b.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0)
            ))
            
            for block in sorted_blocks:
                if block['BlockType'] == 'LINE':
                    # Extract all words in this line
                    line_text = block.get('Text', '')
                    if 'Relationships' in block:
                        for relationship in block['Relationships']:
                            if relationship['Type'] == 'CHILD':
                                for child_id in relationship['Ids']:
                                    child_block = next((b for b in blocks if b['Id'] == child_id), None)
                                    if child_block and child_block['BlockType'] == 'WORD':
                                        line_text += ' ' + child_block.get('Text', '')
                    
                    if line_text.strip():
                        text_lines.append(line_text.strip())
                        
                elif block['BlockType'] == 'WORD':
                    # If we're getting individual words, group them by line
                    word_text = block.get('Text', '')
                    if word_text.strip():
                        current_line.append(word_text)
                        
                        # Check if this word belongs to a different line
                        line_id = block.get('LineId', None)
                        if line_id != current_line_id:
                            if current_line:
                                text_lines.append(' '.join(current_line))
                                current_line = []
                            current_line_id = line_id
                            current_line.append(word_text)
            
            # Add the last line if there are remaining words
            if current_line:
                text_lines.append(' '.join(current_line))
            
            extracted_text = '\n'.join(text_lines)
            logger.info(f"Extracted {len(extracted_text)} characters from {len(text_lines)} lines")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from blocks: {e}")
            # Fallback: try to extract any text from blocks
            fallback_text = []
            for block in blocks:
                if 'Text' in block:
                    fallback_text.append(block['Text'])
            return ' '.join(fallback_text)

    def _extract_structured_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract structured text from Textract blocks, including forms and tables.
        """
        text_content = []
        
        # Extract form data
        form_data = self._extract_form_data(blocks)
        if form_data:
            text_content.append("=== FORM DATA ===")
            for key, value in form_data.items():
                text_content.append(f"{key}: {value}")
            text_content.append("")
        
        # Extract table data
        table_data = self._extract_table_data(blocks)
        if table_data:
            text_content.append("=== TABLES ===")
            for table_idx, table in enumerate(table_data):
                text_content.append(f"Table {table_idx + 1}:")
                for row in table:
                    text_content.append(" | ".join(row))
                text_content.append("")
        
        # Extract plain text
        plain_text = self._extract_text_from_blocks(blocks)
        if plain_text:
            text_content.append("=== TEXT CONTENT ===")
            text_content.append(plain_text)
        
        return '\n'.join(text_content)

    def _extract_form_data(self, blocks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Extract key-value pairs from form blocks.
        """
        form_data = {}
        key_blocks = [block for block in blocks if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block['EntityTypes']]
        
        for key_block in key_blocks:
            key_text = ""
            value_text = ""
            
            # Extract key text
            if 'Relationships' in key_block:
                for relationship in key_block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in blocks if b['Id'] == child_id), None)
                            if child_block and child_block['BlockType'] == 'WORD':
                                key_text += child_block['Text'] + " "
            
            # Extract value text
            if 'Relationships' in key_block:
                for relationship in key_block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            value_block = next((b for b in blocks if b['Id'] == value_id), None)
                            if value_block and 'Relationships' in value_block:
                                for value_rel in value_block['Relationships']:
                                    if value_rel['Type'] == 'CHILD':
                                        for child_id in value_rel['Ids']:
                                            child_block = next((b for b in blocks if b['Id'] == child_id), None)
                                            if child_block and child_block['BlockType'] == 'WORD':
                                                value_text += child_block['Text'] + " "
            
            if key_text.strip() and value_text.strip():
                form_data[key_text.strip()] = value_text.strip()
        
        return form_data

    def _extract_table_data(self, blocks: List[Dict[str, Any]]) -> List[List[List[str]]]:
        """
        Extract table data from table blocks.
        """
        tables = []
        table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
        
        for table_block in table_blocks:
            table = self._process_table(table_block, blocks)
            if table:
                tables.append(table)
        
        return tables

    def _process_table(self, table_block: Dict[str, Any], blocks: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Process a single table block into a 2D array.
        """
        table = []
        cell_blocks = []
        
        # Get all cells in this table
        if 'Relationships' in table_block:
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        cell_block = next((b for b in blocks if b['Id'] == cell_id), None)
                        if cell_block and cell_block['BlockType'] == 'CELL':
                            cell_blocks.append(cell_block)
        
        # Sort cells by row and column
        cell_blocks.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
        
        # Build table structure
        current_row = []
        current_row_index = None
        
        for cell_block in cell_blocks:
            row_index = cell_block.get('RowIndex', 0)
            column_index = cell_block.get('ColumnIndex', 0)
            
            # Extract cell text
            cell_text = ""
            if 'Relationships' in cell_block:
                for relationship in cell_block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in blocks if b['Id'] == child_id), None)
                            if child_block and child_block['BlockType'] == 'WORD':
                                cell_text += child_block['Text'] + " "
            
            # Start new row if needed
            if current_row_index is None or row_index != current_row_index:
                if current_row:
                    table.append(current_row)
                current_row = []
                current_row_index = row_index
            
            current_row.append(cell_text.strip())
        
        # Add the last row
        if current_row:
            table.append(current_row)
        
        return table

    async def process_preprocessed_document(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        document_type: DocumentType = DocumentType.GENERAL
    ) -> (str, int):
        """
        Process a document that has been preprocessed and normalized by the preprocessing service.
        This is the recommended approach for production use.
        """
        try:
            logger.info(f"Processing preprocessed document: s3://{s3_bucket}/{s3_key}")
            
            # Extract text using Textract
            text_content, page_count = await self.extract_text_from_s3_pdf(
                s3_bucket, s3_key, document_type
            )
            
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Error processing preprocessed document {s3_key}: {e}")
            raise TextractError(f"Preprocessed document processing failed: {e}")

    async def upload_to_s3_and_extract(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: DocumentType = DocumentType.GENERAL,
        user_id: str = "anonymous"
    ) -> (str, int):
        """
        Upload file to S3 and extract text using AWS Textract.
        For PDFs: Convert to images first, then process with Textract.
        For images: Process directly with Textract.
        """
        try:
            if not self.s3_client:
                raise TextractError("AWS S3 client not available")
            
            bucket_name = aws_config.s3_bucket_name
            
            if filename.lower().endswith('.pdf'):
                # For PDFs: Convert to images and process each image with Textract
                logger.info(f"🔄 Converting PDF {filename} to images for Textract processing")
                image_keys = await self._convert_pdf_to_images_and_upload(file_content, filename, bucket_name, user_id)
                
                if not image_keys:
                    raise TextractError("Failed to convert PDF to images")
                
                # Process all images with Textract
                text_content, page_count = await self.extract_text_from_image_manifest(bucket_name, image_keys, document_type)
                
                # Clean up image files
                await self._cleanup_s3_objects(bucket_name, image_keys)
                
                return text_content, page_count
            else:
                # For images: Upload directly and process with Textract
                s3_key = aws_config.generate_temp_s3_key(filename)
                
                logger.info(f"Uploading {filename} to S3: s3://{bucket_name}/{s3_key}")
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=self._get_content_type(filename)
                )
                
                # Extract text using Textract
                text_content, page_count = await self.extract_text_from_s3_pdf(bucket_name, s3_key, document_type)
                
                # Clean up S3 object
                await self._cleanup_s3_objects(bucket_name, [s3_key])
                
                return text_content, page_count
            
        except Exception as e:
            logger.error(f"Upload and extraction failed: {e}")
            raise TextractError(f"Upload and extraction failed: {e}")

    async def _convert_pdf_to_images_and_upload(
        self, 
        pdf_content: bytes, 
        filename: str, 
        bucket_name: str, 
        user_id: str
    ) -> List[str]:
        """
        Convert PDF to images and upload to S3. Return list of S3 keys.
        """
        try:
            # Convert PDF to images
            image_files = await self._convert_pdf_to_images_local(pdf_content, filename)
            
            if not image_files:
                logger.error("Failed to convert PDF to images")
                return []
            
            # Upload images to S3
            uploaded_keys = []
            for i, (image_content, image_filename) in enumerate(image_files):
                s3_key = f"temp-documents/{user_id}/images/{os.path.splitext(filename)[0]}_page_{i+1}.png"
                
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=image_content,
                    ContentType='image/png'
                )
                uploaded_keys.append(s3_key)
                logger.info(f"Uploaded image {i+1}/{len(image_files)}: {s3_key}")
            
            return uploaded_keys
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    async def _convert_pdf_to_images_local(
        self, 
        pdf_content: bytes, 
        filename: str
    ) -> List[Tuple[bytes, str]]:
        """
        Convert PDF to images locally using pdf2image.
        """
        try:
            import pdf2image
            from PIL import Image
            import io
            
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(
                pdf_content,
                dpi=200,  # Good balance between quality and size
                fmt='PNG',
                thread_count=1  # Single thread for Lambda compatibility
            )
            
            image_files = []
            for i, image in enumerate(images):
                # Convert PIL image to bytes
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG', optimize=True)
                img_bytes = img_buffer.getvalue()
                
                image_filename = f"{os.path.splitext(filename)[0]}_page_{i+1}.png"
                image_files.append((img_bytes, image_filename))
                
                logger.info(f"Converted page {i+1} to image: {len(img_bytes)} bytes")
            
            return image_files
            
        except Exception as e:
            logger.error(f"Error converting PDF to images locally: {e}")
            return []

    async def _cleanup_s3_objects(self, bucket_name: str, s3_keys: List[str]):
        """
        Clean up S3 objects after processing.
        """
        for s3_key in s3_keys:
            try:
                self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                logger.info(f"Cleaned up S3 object: {s3_key}")
            except Exception as e:
                logger.warning(f"Failed to clean up S3 object {s3_key}: {e}")

    async def _hybrid_pdf_extraction(
        self, 
        file_content: bytes, 
        filename: str, 
        bucket_name: str, 
        s3_key: str, 
        document_type: DocumentType,
        user_id: str
    ) -> (str, int):
        """
        Hybrid PDF extraction: Convert to images and use Textract.
        """
        logger.info(f"Starting PDF-to-image extraction for {filename}")

        try:
            # Convert PDF to images and process with Textract
            logger.info(f"🔄 Converting PDF {filename} to images for Textract")
            image_keys = await self._convert_pdf_to_images_and_upload(file_content, filename, bucket_name, user_id)
            
            if not image_keys:
                raise Exception("Failed to convert PDF to images")
            
            # Process all images with Textract
            text_content, page_count = await self.extract_text_from_image_manifest(bucket_name, image_keys, document_type)
            
            if text_content and len(text_content.strip()) > 10:
                logger.info(f"✅ Textract extraction successful: {len(text_content)} characters")
                logger.info(f"📄 First 100 chars: {text_content[:100]}")
                
                # Clean up image files
                await self._cleanup_s3_objects(bucket_name, image_keys)
                
                return text_content, page_count
            else:
                logger.warning(f"⚠ Textract returned minimal content ({len(text_content.strip())} chars)")
                return self._generate_textract_fallback_message(filename, text_content), 1
                
        except Exception as e:
            logger.warning(f"⚠ PDF-to-image extraction failed: {e}")

        # Final fallback: Raw text extraction
        try:
            logger.info(f"🔄 Attempting raw text extraction for {filename}")
            text_content = await self._try_raw_text_extraction(file_content, filename)
            if text_content and len(text_content.strip()) > 10:
                logger.info(f"✅ Raw text extraction successful: {len(text_content)} characters")
                logger.info(f"📄 First 100 chars: {text_content[:100]}")
                return text_content, 1
        except Exception as e:
            logger.warning(f"⚠ Raw text extraction failed: {e}")

        logger.error(f"❌ All extraction methods failed for {filename}")
        return (
            f"PDF content could not be extracted from {filename}. Possible reasons:\n"
            "- The PDF is corrupted or damaged\n"
            "- The PDF has no embedded text content\n"
            "- AWS Textract is not available or configured\n"
            "Please try uploading a different document format.",
            1
        )

    def _generate_textract_fallback_message(self, filename: str, text_content: str) -> str:
        """
        Generate a helpful message when Textract returns minimal content.
        """
        content_length = len(text_content.strip()) if text_content else 0
        
        if content_length == 0:
            return (
                f"⚠️ Textract could not extract text from {filename}.\n\n"
                "This usually means the PDF is:\n"
                "• A scanned document (image-based)\n"
                "• Created by a browser or certain tools\n"
                "• Has embedded images instead of text\n\n"
                "**Solutions:**\n"
                "1. Upload the original source file (Word, Excel, etc.)\n"
                "2. Convert the PDF to images (PNG/JPEG) and upload those\n"
                "3. Use a PDF with embedded text content\n"
                "4. Re-generate the PDF using Adobe Acrobat or Microsoft Word\n\n"
                "The document may still be readable visually, but text extraction failed."
            )
        elif content_length < 50:
            return (
                f"⚠️ Textract extracted very little text from {filename} ({content_length} characters).\n\n"
                "This suggests the PDF is mostly image-based or has minimal text content.\n\n"
                "**Extracted content:**\n"
                f"'{text_content.strip()}'\n\n"
                "**Recommendations:**\n"
                "1. Upload the original source file instead\n"
                "2. Convert to image format and upload those\n"
                "3. Try a different PDF with more text content"
            )
        else:
            return (
                f"⚠️ Textract extracted limited text from {filename} ({content_length} characters).\n\n"
                "**Extracted content:**\n"
                f"'{text_content.strip()}'\n\n"
                "This may be sufficient for basic analysis, but consider uploading the original source file for better results."
            )

    async def _try_aggressive_text_extraction(self, file_content: bytes, filename: str) -> str:
        """Try very aggressive text extraction from PDF bytes."""
        try:
            # Try multiple encodings and extraction strategies
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
            
            best_text = ""
            best_score = 0
            
            for encoding in encodings:
                try:
                    content_str = file_content.decode(encoding, errors='ignore')
                    
                    # Look for various text patterns
                    import re
                    
                    # Find words (2+ letters)
                    words = re.findall(r'\b[A-Za-z]{2,}\b', content_str)
                    
                    # Find numbers and prices
                    numbers = re.findall(r'\$\d+\.?\d*|\d+\.?\d*', content_str)
                    
                    # Find domain names and emails
                    domains = re.findall(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content_str)
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content_str)
                    
                    # Find dates
                    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', content_str)
                    
                    # Calculate score based on found patterns
                    score = len(words) + len(numbers) * 2 + len(domains) * 3 + len(emails) * 5 + len(dates) * 2
                    
                    if score > best_score:
                        best_score = score
                        # Combine all found text
                        extracted_parts = []
                        if words:
                            extracted_parts.extend(words[:100])  # Limit words
                        if numbers:
                            extracted_parts.extend(numbers[:50])  # Limit numbers
                        if domains:
                            extracted_parts.extend(domains[:20])  # Limit domains
                        if emails:
                            extracted_parts.extend(emails[:10])  # Limit emails
                        if dates:
                            extracted_parts.extend(dates[:10])  # Limit dates
                        
                        best_text = " ".join(extracted_parts)
                        
                except Exception as e:
                    logger.debug(f"Encoding {encoding} failed: {e}")
                    continue
            
            if best_text and best_score > 10:
                logger.info(f"Aggressive extraction found {best_score} text elements")
                return best_text
            
            return ""
            
        except Exception as e:
            logger.warning(f"Aggressive text extraction failed: {e}")
            return ""

    async def _try_raw_text_extraction(self, file_content: bytes, filename: str) -> str:
        """Try to extract any readable text from PDF bytes using multiple encodings."""
        try:
            # Try different encodings and text extraction methods
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    content_str = file_content.decode(encoding, errors='ignore')
                    
                    # Look for text patterns that indicate readable content
                    import re
                    
                    # Find words (3+ letters)
                    words = re.findall(r'\b[A-Za-z]{3,}\b', content_str)
                    
                    # Find numbers and prices
                    numbers = re.findall(r'\$\d+\.?\d*', content_str)
                    
                    # Find domain names
                    domains = re.findall(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content_str)
                    
                    # Combine all found text
                    extracted_parts = []
                    if words:
                        extracted_parts.extend(words[:50])  # Limit to first 50 words
                    if numbers:
                        extracted_parts.extend(numbers[:20])  # Limit to first 20 numbers
                    if domains:
                        extracted_parts.extend(domains[:10])  # Limit to first 10 domains
                    
                    if extracted_parts:
                        result = " ".join(extracted_parts)
                        logger.info(f"Raw text extraction found {len(extracted_parts)} text elements using {encoding}")
                        return result
                        
                except Exception as e:
                    logger.debug(f"Encoding {encoding} failed: {e}")
                    continue
            
            return ""
            
        except Exception as e:
            logger.warning(f"Raw text extraction failed: {e}")
            return ""

    async def _try_pypdf2_extraction(self, file_content: bytes, filename: str) -> (str, int):
        """Try PyPDF2 extraction."""
        try:
            import asyncio
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            def extract_with_timeout():
                try:
                    pdf_file = BytesIO(file_content)
                    reader = PdfReader(pdf_file)
                    text_content = ""
                    page_count = len(reader.pages)
                    
                    logger.info(f"PyPDF2: Processing {page_count} pages")
                    
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                                logger.debug(f"PyPDF2: Page {page_num + 1} extracted {len(page_text)} characters")
                            else:
                                logger.debug(f"PyPDF2: Page {page_num + 1} returned no text")
                        except Exception as e:
                            logger.warning(f"PyPDF2 error on page {page_num + 1}: {e}")
                            continue
                    
                    logger.info(f"PyPDF2: Total extracted {len(text_content)} characters from {page_count} pages")
                    return text_content, page_count
                except Exception as e:
                    logger.warning(f"PyPDF2 extraction error: {e}")
                    raise
            
            # Run with 5-second timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, extract_with_timeout),
                timeout=5.0
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning("PyPDF2 extraction timed out (likely corrupted PDF)")
            raise Exception("Extraction timed out")
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            raise

    async def _try_pdfminer_extraction(self, file_content: bytes, filename: str) -> (str, int):
        """Try PDFMiner extraction.."""
        try:
            import asyncio
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
            from io import BytesIO, StringIO
            
            # Create output string buffer
            output_string = StringIO()
            
            # Run PDFMiner extraction with timeout to prevent hanging on corrupted PDFs
            def extract_with_timeout():
                try:
                    logger.info(f"PDFMiner: Starting extraction for {filename}")
                    
                    # Try with different LAParams for corrupted PDFs
                    laparams_options = [
                        LAParams(),  # Default
                        LAParams(line_margin=0.5, word_margin=0.1),  # More lenient
                        LAParams(line_margin=1.0, word_margin=0.2, char_margin=2.0)  # Very lenient
                    ]
                    
                    for i, laparams in enumerate(laparams_options):
                        try:
                            output_string.seek(0)
                            output_string.truncate(0)
                            
                            extract_text_to_fp(
                                BytesIO(file_content),
                                output_string,
                                laparams=laparams,
                                output_type='text'
                            )
                            text_content = output_string.getvalue()
                            
                            if text_content and len(text_content.strip()) > 10:
                                logger.info(f"PDFMiner: Success with params {i+1}, extracted {len(text_content)} characters")
                                return text_content
                            else:
                                logger.debug(f"PDFMiner: Params {i+1} returned minimal content")
                                
                        except Exception as e:
                            logger.debug(f"PDFMiner: Params {i+1} failed: {e}")
                            continue
                    
                    # If all params failed, try one more time with the most lenient settings
                    output_string.seek(0)
                    output_string.truncate(0)
                    
                    extract_text_to_fp(
                        BytesIO(file_content),
                        output_string,
                        laparams=LAParams(line_margin=2.0, word_margin=0.5, char_margin=5.0),
                        output_type='text'
                    )
                    text_content = output_string.getvalue()
                    logger.info(f"PDFMiner: Final attempt extracted {len(text_content)} characters")
                    return text_content
                    
                except Exception as e:
                    logger.warning(f"PDFMiner extraction error: {e}")
                    raise
            
            # Run with 15-second timeout (increased for multiple attempts)
            loop = asyncio.get_event_loop()
            text_content = await asyncio.wait_for(
                loop.run_in_executor(None, extract_with_timeout),
                timeout=15.0
            )
            
            page_count = 1  # PDFMiner doesn't provide page count easily
            
            return text_content, page_count
            
        except asyncio.TimeoutError:
            logger.warning("PDFMiner extraction timed out (likely corrupted PDF)")
            raise Exception("Extraction timed out")
        except Exception as e:
            logger.warning(f"PDFMiner extraction failed: {e}")
            raise

    async def _try_basic_text_extraction(self, file_content: bytes, filename: str) -> (str, int):
        """Try basic text extraction from PDF content."""
        try:
            # Try to extract any text-like content from the PDF bytes
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Look for text patterns
            import re
            text_patterns = [
                r'[A-Za-z]{3,}',  # Words with 3+ letters
                r'\d+',           # Numbers
                r'[A-Za-z0-9\s]{10,}'  # Longer text sequences
            ]
            
            extracted_text = ""
            for pattern in text_patterns:
                matches = re.findall(pattern, content_str)
                if matches:
                    extracted_text += " ".join(matches[:100]) + "\n"  # Limit to first 100 matches
            
            if extracted_text.strip():
                return extracted_text, 1
            else:
                raise Exception("No text patterns found")
                
        except Exception as e:
            logger.warning(f"Basic text extraction failed: {e}")
            raise

    def _get_content_type(self, filename: str) -> str:
        """
        Get the appropriate content type for a file.
        """
        if filename.lower().endswith('.pdf'):
            return 'application/pdf'
        elif filename.lower().endswith('.png'):
            return 'image/png'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            return 'image/jpeg'
        elif filename.lower().endswith('.tiff') or filename.lower().endswith('.tif'):
            return 'image/tiff'
        else:
            return 'application/octet-stream'

    def get_textract_compatibility_guide(self) -> Dict[str, Any]:
        """
        Get compatibility information for Textract.
        """
        return {
            "supported_formats": [
                "PDF (unencrypted, standard format)",
                "PNG (image files)",
                "JPEG (image files)", 
                "TIFF (image files)"
            ],
            "unsupported_formats": [
                "Encrypted or password-protected PDFs",
                "Corrupted or damaged files",
                "Browser-generated PDFs (Chrome 'Save as PDF')",
                "PDFs with unusual internal structures",
                "Very large files (>5MB for synchronous, >500MB for asynchronous)",
                "Files with non-standard encoding"
            ],
            "recommendations": [
                "Use PDFs created by standard PDF generators (Adobe, Word, etc.)",
                "Avoid browser-generated PDFs",
                "Ensure files are not encrypted",
                "Keep file sizes reasonable (<5MB for best results)",
                "Test with simple, text-based documents first",
                "Use preprocessing service to normalize problematic PDFs"
            ],
            "troubleshooting": [
                "If you get 'Unsupported document type', use preprocessing service",
                "Convert browser-generated PDFs to standard PDFs",
                "Use image files (PNG/JPEG) as an alternative",
                "Check if the PDF is encrypted or corrupted",
                "Preprocessing service handles PDF normalization"
            ]
        }
    
    def estimate_cost(self, document_type: DocumentType, page_count: int = 1) -> Dict[str, Any]:
        """
        Estimate the cost of Textract processing.
        """
        api_type = self._select_api_type(document_type)
        
        if api_type == TextractAPI.DETECT_DOCUMENT_TEXT:
            cost_per_1000_pages = 1.50
        else:
            cost_per_1000_pages = 5.00
        
        estimated_cost = (page_count / 1000) * cost_per_1000_pages
        
        return {
            "api_type": api_type.value,
            "page_count": page_count,
            "cost_per_1000_pages": cost_per_1000_pages,
            "estimated_cost": estimated_cost,
            "currency": "USD"
        }

    def analyze_pdf_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze PDF content to determine its type and extraction strategy.
        """
        try:
            analysis = {
                "filename": filename,
                "file_size": len(file_content),
                "pdf_type": "unknown",
                "page_count": 0,
                "text_pages": 0,
                "image_pages": 0,
                "text_content_length": 0,
                "recommendation": "unknown"
            }
            
            # Basic analysis without PyMuPDF
            try:
                # Try to extract text using PyPDF2
                import PyPDF2
                from io import BytesIO
                
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                analysis["page_count"] = len(pdf_reader.pages)
                
                total_text_length = 0
                text_pages = 0
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    text_length = len(text.strip())
                    total_text_length += text_length
                    
                    if text_length > 50:  # Meaningful text content
                        text_pages += 1
                
                analysis["text_content_length"] = total_text_length
                analysis["text_pages"] = text_pages
                analysis["image_pages"] = analysis["page_count"] - text_pages
                
                # Determine PDF type and recommendation
                if text_pages > 0 and analysis["image_pages"] == 0:
                    analysis["pdf_type"] = "text_based"
                    analysis["recommendation"] = "Textract should work well"
                elif text_pages > 0 and analysis["image_pages"] > 0:
                    analysis["pdf_type"] = "mixed_content"
                    analysis["recommendation"] = "Textract may work, but consider original source"
                elif text_pages == 0 and analysis["image_pages"] > 0:
                    analysis["pdf_type"] = "image_based"
                    analysis["recommendation"] = "Use original source file or convert to images"
                elif total_text_length == 0:
                    analysis["pdf_type"] = "empty_or_corrupted"
                    analysis["recommendation"] = "File may be corrupted or empty"
                else:
                    analysis["pdf_type"] = "minimal_text"
                    analysis["recommendation"] = "Limited text content, consider alternative"
                    
            except Exception as e:
                logger.warning(f"PyPDF2 analysis failed: {e}")
                analysis["pdf_type"] = "unknown"
                analysis["recommendation"] = "Unable to analyze PDF content"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {filename}: {e}")
            return {
                "filename": filename,
                "file_size": len(file_content),
                "pdf_type": "error",
                "recommendation": f"Analysis failed: {e}"
            }

    async def extract_text_from_image_manifest(
        self,
        s3_bucket: str,
        image_keys: list,
        document_type: DocumentType = DocumentType.GENERAL
    ) -> (str, int):
        """
        Extract text from a list of image S3 keys (manifest) using Textract and aggregate results.
        Returns (combined_text_content, page_count)
        """
        all_text = []
        total_pages = 0
        for idx, image_key in enumerate(image_keys):
            try:
                logger.info(f"Processing image page {idx+1}/{len(image_keys)}: s3://{s3_bucket}/{image_key}")
                
                # Use enhanced image extraction for better results
                text_content, page_count = await self._try_enhanced_image_extraction(s3_bucket, image_key)
                
                if text_content and text_content.strip():
                    all_text.append(f"--- Page {idx+1} ---\n{text_content}")
                    total_pages += page_count
                else:
                    logger.warning(f"No text extracted from page {idx+1} ({image_key})")
                    all_text.append(f"--- Page {idx+1} ---\n[No text detected]")
                    
            except Exception as e:
                logger.warning(f"Textract failed for page {idx+1} ({image_key}): {e}")
                all_text.append(f"--- Page {idx+1} ---\n[Textract failed: {e}]")
        
        combined_text = "\n\n".join(all_text)
        logger.info(f"Image manifest processing completed: {len(combined_text)} total characters from {total_pages} pages")
        return combined_text, total_pages

# Global instance
textract_service = AWSTextractService() 