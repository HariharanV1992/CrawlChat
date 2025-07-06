"""
AWS Textract Service for document text extraction
Implements the recommended architecture with S3-based processing
"""

import logging
import os
import io
import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.core.aws_config import aws_config
from src.core.exceptions import DocumentProcessingError

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
        Returns (text_content, page_count)
        """
        try:
            if not self.textract_client:
                raise DocumentProcessingError("AWS Textract client not available")
            if not self.s3_client:
                raise DocumentProcessingError("AWS S3 client not available")
            api_type = self._select_api_type(document_type)
            logger.info(f"Processing document {s3_key} with API: {api_type.value}")
            if api_type == TextractAPI.DETECT_DOCUMENT_TEXT:
                return await self._detect_document_text_with_retry(s3_bucket, s3_key)
            else:
                return await self._analyze_document_with_retry(s3_bucket, s3_key)
        except Exception as e:
            logger.error(f"Error extracting text from S3 PDF {s3_key}: {e}")
            raise DocumentProcessingError(f"Textract extraction failed: {e}")

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
                response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                wait_time = time.time() - start_time
                logger.info(f"DEBUG: S3 object {s3_key} is available after {wait_time:.2f}s (attempt {attempt})")
                logger.info(f"DEBUG: S3 object size: {response.get('ContentLength', 'unknown')} bytes")
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

    async def _extract_with_retry(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        document_type: DocumentType, 
        max_retries: int = 3
    ) -> (str, int):
        """
        Extract text with retry logic for S3 object availability issues.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"DEBUG: Textract extraction attempt {attempt + 1}/{max_retries}")
                
                # Re-check S3 object availability before each attempt
                if not await self._wait_for_s3_object(s3_bucket, s3_key, max_wait=5):
                    logger.warning(f"DEBUG: S3 object not available on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait 2 seconds before retry
                        continue
                    else:
                        raise DocumentProcessingError(f"S3 object not available after {max_retries} attempts")
                
                # Call the appropriate Textract API
                api_type = self._select_api_type(document_type)
                if api_type == TextractAPI.DETECT_DOCUMENT_TEXT:
                    return await self._detect_document_text(s3_bucket, s3_key)
                else:
                    return await self._analyze_document(s3_bucket, s3_key)
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'InvalidS3ObjectException':
                    last_error = e
                    logger.warning(f"DEBUG: InvalidS3ObjectException on attempt {attempt + 1}: {e.response['Error'].get('Message', '')}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)  # Wait 3 seconds before retry
                        continue
                    else:
                        raise DocumentProcessingError(f"S3 object not available or invalid after {max_retries} attempts: {s3_key}")
                else:
                    # Other AWS errors, don't retry
                    raise DocumentProcessingError(f"AWS Textract error: {error_code}")
            except Exception as e:
                last_error = e
                logger.error(f"DEBUG: Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    raise DocumentProcessingError(f"Textract processing failed after {max_retries} attempts: {e}")
        
        # This should never be reached, but just in case
        if last_error:
            raise DocumentProcessingError(f"Textract extraction failed: {last_error}")
        else:
            raise DocumentProcessingError("Textract extraction failed for unknown reason")
    
    def _select_api_type(self, document_type: DocumentType) -> TextractAPI:
        """
        Select the appropriate Textract API based on document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            TextractAPI enum value
        """
        if document_type in [DocumentType.FORM, DocumentType.INVOICE, DocumentType.TABLE_HEAVY]:
            logger.info(f"Using AnalyzeDocument API for {document_type.value} document")
            return TextractAPI.ANALYZE_DOCUMENT
        else:
            logger.info(f"Using DetectDocumentText API for {document_type.value} document")
            return TextractAPI.DETECT_DOCUMENT_TEXT
    
    async def _detect_document_text(self, s3_bucket: str, s3_key: str) -> (str, int):
        try:
            logger.info(f"Calling DetectDocumentText for {s3_bucket}/{s3_key}")
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                }
            )
            text_content = self._extract_text_from_blocks(response['Blocks'])
            # Count unique pages
            page_numbers = set()
            for block in response['Blocks']:
                if block['BlockType'] == 'PAGE':
                    page_numbers.add(block['Page'])
                elif 'Page' in block:
                    page_numbers.add(block['Page'])
            page_count = len(page_numbers) if page_numbers else 1
            logger.info(f"Successfully extracted {len(text_content)} characters using DetectDocumentText, pages: {page_count}")
            return text_content, page_count
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidDocumentException':
                raise DocumentProcessingError(f"Invalid document format: {s3_key}")
            elif error_code == 'DocumentTooLargeException':
                raise DocumentProcessingError(f"Document too large for Textract: {s3_key}")
            elif error_code == 'UnsupportedDocumentException':
                raise DocumentProcessingError(f"Unsupported document type: {s3_key}")
            elif error_code == 'InvalidS3ObjectException':
                raise DocumentProcessingError(f"S3 object not available or invalid: {s3_key}. Please try again in a few seconds.")
            else:
                raise DocumentProcessingError(f"AWS Textract error: {error_code}")
        except Exception as e:
            logger.error(f"Error in DetectDocumentText: {e}")
            raise DocumentProcessingError(f"Textract processing failed: {e}")
    
    async def _analyze_document(self, s3_bucket: str, s3_key: str) -> (str, int):
        try:
            logger.info(f"Calling AnalyzeDocument for {s3_bucket}/{s3_key}")
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            text_content = self._extract_structured_text_from_blocks(response['Blocks'])
            # Count unique pages
            page_numbers = set()
            for block in response['Blocks']:
                if block['BlockType'] == 'PAGE':
                    page_numbers.add(block['Page'])
                elif 'Page' in block:
                    page_numbers.add(block['Page'])
            page_count = len(page_numbers) if page_numbers else 1
            logger.info(f"Successfully extracted structured content using AnalyzeDocument, pages: {page_count}")
            return text_content, page_count
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidDocumentException':
                raise DocumentProcessingError(f"Invalid document format: {s3_key}")
            elif error_code == 'DocumentTooLargeException':
                raise DocumentProcessingError(f"Document too large for Textract: {s3_key}")
            elif error_code == 'UnsupportedDocumentException':
                raise DocumentProcessingError(f"Unsupported document type: {s3_key}")
            elif error_code == 'InvalidS3ObjectException':
                raise DocumentProcessingError(f"S3 object not available or invalid: {s3_key}. Please try again in a few seconds.")
            else:
                raise DocumentProcessingError(f"AWS Textract error: {error_code}")
        except Exception as e:
            logger.error(f"Error in AnalyzeDocument: {e}")
            raise DocumentProcessingError(f"Textract processing failed: {e}")
    
    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Textract blocks (DetectDocumentText response).
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            Extracted text content
        """
        text_lines = []
        
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        
        return '\n'.join(text_lines)
    
    def _extract_structured_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract structured text from Textract blocks (AnalyzeDocument response).
        Includes forms, tables, and regular text.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            Extracted structured text content
        """
        text_content = []
        
        # Extract regular text lines
        text_lines = []
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        
        if text_lines:
            text_content.append("Document Text:")
            text_content.append('\n'.join(text_lines))
            text_content.append("")
        
        # Extract form key-value pairs
        form_data = self._extract_form_data(blocks)
        if form_data:
            text_content.append("Form Data:")
            for key, value in form_data.items():
                text_content.append(f"{key}: {value}")
            text_content.append("")
        
        # Extract table data
        table_data = self._extract_table_data(blocks)
        if table_data:
            text_content.append("Table Data:")
            for i, table in enumerate(table_data):
                text_content.append(f"Table {i+1}:")
                for row in table:
                    text_content.append(" | ".join(row))
                text_content.append("")
        
        return '\n'.join(text_content)
    
    def _extract_form_data(self, blocks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Extract key-value pairs from form blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            Dictionary of key-value pairs
        """
        form_data = {}
        
        # Find key-value relationships
        key_value_relationships = {}
        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block['EntityTypes']:
                    key_value_relationships[block['Id']] = {
                        'key': block.get('Text', ''),
                        'value': ''
                    }
                elif 'VALUE' in block['EntityTypes']:
                    # Find the key this value belongs to
                    for relationship in block.get('Relationships', []):
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                if value_id in key_value_relationships:
                                    key_value_relationships[value_id]['value'] = block.get('Text', '')
        
        # Convert to dictionary
        for kv in key_value_relationships.values():
            if kv['key'] and kv['value']:
                form_data[kv['key']] = kv['value']
        
        return form_data
    
    def _extract_table_data(self, blocks: List[Dict[str, Any]]) -> List[List[List[str]]]:
        """
        Extract table data from table blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            List of tables, each table is a list of rows, each row is a list of cells
        """
        tables = []
        
        # Group blocks by table
        table_blocks = {}
        for block in blocks:
            if block['BlockType'] == 'TABLE':
                table_id = block['Id']
                table_blocks[table_id] = {
                    'table': block,
                    'cells': []
                }
        
        # Find cells for each table
        for block in blocks:
            if block['BlockType'] == 'CELL':
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            if child_id in table_blocks:
                                table_blocks[child_id]['cells'].append(block)
        
        # Process each table
        for table_id, table_info in table_blocks.items():
            table = self._process_table(table_info['table'], table_info['cells'])
            if table:
                tables.append(table)
        
        return tables
    
    def _process_table(self, table_block: Dict[str, Any], cell_blocks: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Process a single table into a 2D array.
        
        Args:
            table_block: Table block from Textract
            cell_blocks: List of cell blocks for this table
            
        Returns:
            2D array representing the table
        """
        # This is a simplified implementation
        # In a full implementation, you would need to handle complex table structures
        # including merged cells, spanning rows/columns, etc.
        
        rows = []
        current_row = []
        
        for cell in cell_blocks:
            cell_text = cell.get('Text', '')
            current_row.append(cell_text)
            
            # Simple heuristic: if we have many cells, assume it's a new row
            if len(current_row) >= 5:  # Adjust based on your documents
                rows.append(current_row)
                current_row = []
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    async def upload_to_s3_and_extract(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: DocumentType = DocumentType.GENERAL
    ) -> (str, int):
        try:
            if not self.s3_client:
                raise DocumentProcessingError("S3 client not available")
            import uuid
            file_id = str(uuid.uuid4())
            # Use centralized S3 path generation for consistency
            s3_key = aws_config.generate_temp_s3_key(filename, file_id)
            s3_bucket = aws_config.s3_bucket_name
            
            logger.info(f"DEBUG: S3 Bucket: {s3_bucket}")
            logger.info(f"DEBUG: S3 Key: {s3_key}")
            logger.info(f"DEBUG: Full S3 Path: s3://{s3_bucket}/{s3_key}")
            logger.info(f"DEBUG: File size: {len(file_content)} bytes")
            logger.info(f"DEBUG: Content type: {self._get_content_type(filename)}")
            logger.info(f"DEBUG: Deployment timestamp: {time.time()}")
            
            logger.info(f"Uploading {filename} to S3 as {s3_key}")
            try:
                response = self.s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=self._get_content_type(filename)
                )
                logger.info(f"DEBUG: File uploaded successfully to S3")
                logger.info(f"DEBUG: S3 upload response ETag: {response.get('ETag', 'none')}")
                logger.info(f"DEBUG: S3 upload response VersionId: {response.get('VersionId', 'none')}")
            except Exception as e:
                logger.error(f"DEBUG: S3 upload failed: {e}")
                raise DocumentProcessingError(f"S3 upload failed: {e}")
            
            # Wait for S3 object to be available before calling Textract
            logger.info(f"DEBUG: Waiting for S3 object availability before Textract extraction")
            if not await self._wait_for_s3_object(s3_bucket, s3_key, max_wait=20):
                raise DocumentProcessingError(f"S3 object not available after upload: {s3_key}")
            
            logger.info(f"DEBUG: Starting Textract extraction for s3://{s3_bucket}/{s3_key}")
            
            # Use retry mechanism for Textract calls
            text_content, page_count = await self._extract_with_retry(
                s3_bucket,
                s3_key,
                document_type,
                max_retries=3
            )
            
            try:
                self.s3_client.delete_object(
                    Bucket=s3_bucket,
                    Key=s3_key
                )
                logger.info(f"Cleaned up S3 file: {s3_key}")
            except Exception as e:
                logger.warning(f"Failed to clean up S3 file {s3_key}: {e}")
            return text_content, page_count
        except Exception as e:
            logger.error(f"Error in upload_to_s3_and_extract: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename."""
        import os
        extension = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def estimate_cost(self, document_type: DocumentType, page_count: int = 1) -> Dict[str, Any]:
        """
        Estimate the cost of Textract processing.
        
        Args:
            document_type: Type of document
            page_count: Number of pages
            
        Returns:
            Cost estimation dictionary
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

# Global instance
textract_service = AWSTextractService() 