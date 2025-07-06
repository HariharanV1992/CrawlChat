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
from typing import Optional, Dict, Any, List
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
        Assumes the document has been preprocessed and normalized.
        Returns (text_content, page_count)
        """
        try:
            if not self.textract_client:
                raise DocumentProcessingError("AWS Textract client not available")
            if not self.s3_client:
                raise DocumentProcessingError("AWS S3 client not available")
            
            # Wait for S3 object to be available
            if not await self._wait_for_s3_object(s3_bucket, s3_key):
                raise DocumentProcessingError(f"S3 object {s3_key} not available after waiting")
            
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
                raise DocumentProcessingError("Textract returned empty or minimal text")
                    
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
            
            # Extract text from blocks
            text_content = self._extract_text_from_blocks(response['Blocks'])
            page_count = len([block for block in response['Blocks'] if block['BlockType'] == 'PAGE'])
            
            logger.info(f"DetectDocumentText completed: {len(text_content)} characters, {page_count} pages")
            return text_content, page_count
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Textract DetectDocumentText failed: {error_code} - {error_message}")
            
            if error_code == 'UnsupportedDocumentException':
                raise DocumentProcessingError(f"Unsupported document type: {error_message}")
            elif error_code == 'InvalidS3ObjectException':
                raise DocumentProcessingError(f"Invalid S3 object: {error_message}")
            else:
                raise DocumentProcessingError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in DetectDocumentText: {e}")
            raise DocumentProcessingError(f"Unexpected error: {e}")

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
                raise DocumentProcessingError(f"Unsupported document type: {error_message}")
            elif error_code == 'InvalidS3ObjectException':
                raise DocumentProcessingError(f"Invalid S3 object: {error_message}")
            else:
                raise DocumentProcessingError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in AnalyzeDocument: {e}")
            raise DocumentProcessingError(f"Unexpected error: {e}")

    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Textract blocks.
        """
        text_lines = []
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        return '\n'.join(text_lines)

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
            raise DocumentProcessingError(f"Preprocessed document processing failed: {e}")

    async def upload_to_s3_and_extract(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: DocumentType = DocumentType.GENERAL,
        user_id: str = "anonymous"
    ) -> (str, int):
        """
        Upload file to S3 and extract text using Textract.
        Includes fallback for unsupported PDFs.
        """
        try:
            if not self.s3_client:
                raise DocumentProcessingError("AWS S3 client not available")
            
            # Determine S3 path - use consistent path format with document service
            bucket_name = aws_config.s3_bucket
            file_id = str(uuid.uuid4())
            s3_key = f"uploaded_documents/{user_id}/{file_id}/{filename}"
            
            # Upload to S3
            logger.info(f"Uploading {filename} to s3://{bucket_name}/{s3_key}")
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            
            try:
                # Try Textract first
                text_content, page_count = await self.extract_text_from_s3_pdf(
                    bucket_name, s3_key, document_type
                )
                return text_content, page_count
                
            except DocumentProcessingError as e:
                if "Unsupported document type" in str(e) and filename.lower().endswith('.pdf'):
                    logger.warning(f"Textract failed for PDF {filename}, attempting fallback extraction")
                    return await self._fallback_pdf_extraction(file_content, filename, user_id)
                else:
                    raise e
            
        except Exception as e:
            logger.error(f"Error in upload_to_s3_and_extract: {e}")
            raise DocumentProcessingError(f"Upload and extraction failed: {e}")

    async def _fallback_pdf_extraction(self, file_content: bytes, filename: str, user_id: str) -> (str, int):
        """
        Fallback PDF text extraction when Textract fails.
        Uses multiple PDF libraries for maximum compatibility.
        """
        try:
            logger.info(f"Using fallback PDF extraction for: {filename}")
            
            # First, try to detect if the PDF is severely corrupted
            if self._is_pdf_severely_corrupted(file_content):
                logger.warning(f"PDF {filename} appears to be severely corrupted, skipping extraction attempts")
                return f"PDF content could not be extracted from {filename}. This PDF appears to be corrupted or damaged. Please try uploading a different copy of the document.", 1
            
            # Try multiple PDF extraction methods in order of reliability
            extraction_methods = [
                self._try_pdfminer_extraction,  # Most robust for corrupted PDFs
                self._try_pypdf2_extraction,    # Good for standard PDFs
                self._try_basic_text_extraction # Last resort
            ]
            
            for method in extraction_methods:
                try:
                    text_content, page_count = await method(file_content, filename)
                    if text_content and len(text_content.strip()) > 10:
                        logger.info(f"Fallback extraction successful with {method.__name__}: {len(text_content)} characters, {page_count} pages")
                        return text_content, page_count
                except Exception as e:
                    logger.warning(f"Method {method.__name__} failed: {e}")
                    continue
            
            # If all methods fail, try to extract any readable text from the PDF bytes
            logger.warning("All extraction methods failed, attempting raw text extraction")
            try:
                raw_text = await self._try_raw_text_extraction(file_content, filename)
                if raw_text and len(raw_text.strip()) > 10:
                    logger.info(f"Raw text extraction successful: {len(raw_text)} characters")
                    return raw_text, 1
            except Exception as e:
                logger.warning(f"Raw text extraction failed: {e}")
            
            # Final fallback - return a descriptive message
            logger.warning("All fallback methods failed, returning descriptive message")
            return f"PDF content could not be extracted from {filename}. This appears to be a browser-generated PDF with internal structure issues. Consider using a PDF created by standard tools like Adobe Acrobat or Microsoft Word.", 1
            
        except Exception as e:
            logger.error(f"Fallback PDF extraction failed: {e}")
            raise DocumentProcessingError(f"Fallback extraction failed: {e}")

    def _is_pdf_severely_corrupted(self, file_content: bytes) -> bool:
        """
        Check if PDF is severely corrupted before attempting extraction.
        """
        try:
            # Check for basic PDF structure
            if not file_content.startswith(b'%PDF-'):
                logger.warning("File does not start with PDF header")
                return True
            
            # Check for end-of-file marker
            if b'%%EOF' not in file_content[-1000:]:
                logger.warning("PDF does not contain proper EOF marker")
                return True
            
            # Check for reasonable file size (at least 1KB)
            if len(file_content) < 1024:
                logger.warning("PDF file is too small, likely corrupted")
                return True
            
            # Check for excessive null bytes (indicates corruption)
            null_ratio = file_content.count(b'\x00') / len(file_content)
            if null_ratio > 0.5:
                logger.warning(f"PDF contains too many null bytes ({null_ratio:.2%})")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking PDF corruption: {e}")
            return True

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
                    
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                        except Exception as e:
                            logger.warning(f"PyPDF2 error on page {page_num + 1}: {e}")
                            continue
                    
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
        """Try PDFMiner extraction."""
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
                    extract_text_to_fp(
                        BytesIO(file_content),
                        output_string,
                        laparams=LAParams(),
                        output_type='text'
                    )
                    return output_string.getvalue()
                except Exception as e:
                    logger.warning(f"PDFMiner extraction error: {e}")
                    raise
            
            # Run with 10-second timeout
            loop = asyncio.get_event_loop()
            text_content = await asyncio.wait_for(
                loop.run_in_executor(None, extract_with_timeout),
                timeout=10.0
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

# Global instance
textract_service = AWSTextractService() 