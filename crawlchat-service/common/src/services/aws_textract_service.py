"""
AWS Textract Service for document text extraction
Simple implementation based on AWS documentation
"""

import logging
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import asyncio
from io import BytesIO

from ..core.aws_config import aws_config
from ..core.exceptions import TextractError

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document types for API selection."""
    GENERAL = "general"
    FORM = "form"
    INVOICE = "invoice"
    TABLE_HEAVY = "table_heavy"

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
            logger.info(f"Initializing AWS clients in region: {region}")
            
            # Check if running in Lambda environment
            is_lambda = (
                os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
                os.getenv('AWS_EXECUTION_ENV') or 
                os.getenv('LAMBDA_TASK_ROOT')
            )
            
            if is_lambda:
                # Running in Lambda - use IAM role
                logger.info("Running in Lambda environment, using IAM role")
                self.textract_client = boto3.client('textract', region_name=region)
                self.s3_client = boto3.client('s3', region_name=region)
            else:
                # Running locally - use credentials if available
                if aws_config.access_key_id and aws_config.secret_access_key:
                    logger.info("Running locally, using provided AWS credentials")
                    self.textract_client = boto3.client(
                        'textract',
                        aws_access_key_id=aws_config.access_key_id,
                        aws_secret_access_key=aws_config.secret_access_key,
                        region_name=region
                    )
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=aws_config.access_key_id,
                        aws_secret_access_key=aws_config.secret_access_key,
                        region_name=region
                    )
                else:
                    logger.warning("AWS credentials not available for local environment")
                    self.textract_client = None
                    self.s3_client = None
            
            if self.textract_client:
                logger.info("Textract client initialized successfully")
            else:
                logger.error("Textract client initialization failed")
                
            if self.s3_client:
                logger.info("S3 client initialized successfully")
            else:
                logger.error("S3 client initialization failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.textract_client = None
            self.s3_client = None
    
    def _ensure_clients_initialized(self):
        """Ensure AWS clients are initialized (lazy initialization)."""
        if not self._clients_initialized:
            logger.info("Initializing AWS clients (lazy initialization)...")
            self._init_clients()
            self._clients_initialized = True

    async def extract_text_from_s3_pdf(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        document_type: DocumentType = DocumentType.GENERAL
    ) -> Tuple[str, int]:
        """
        Extract text from PDF stored in S3 using AWS Textract.
        Returns (text_content, page_count)
        """
        try:
            # Ensure clients are initialized
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            if not self.s3_client:
                raise TextractError("AWS S3 client not available")
            
            # Get document size to decide on sync vs async
            try:
                response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                document_size = response.get('ContentLength', 0)
                logger.info(f"Document size: {document_size} bytes")
                
                # Use sync API for documents up to 5MB
                if document_size <= 5 * 1024 * 1024:
                    logger.info(f"Using sync Textract API for document ({document_size} bytes)")
                    return await self._extract_text_sync(s3_bucket, s3_key, document_type)
                else:
                    logger.warning(f"Document too large for sync API ({document_size} bytes)")
                    raise TextractError("Document too large for synchronous processing (max 5MB)")
                    
            except Exception as size_e:
                logger.warning(f"Could not determine document size: {size_e}, using sync API")
                return await self._extract_text_sync(s3_bucket, s3_key, document_type)
                    
        except Exception as e:
            logger.error(f"Error extracting text from S3 PDF {s3_key}: {e}")
            raise TextractError(f"Textract extraction failed: {e}")

    async def _extract_text_sync(self, s3_bucket: str, s3_key: str, document_type: DocumentType) -> Tuple[str, int]:
        """
        Extract text using AWS Textract synchronous API.
        """
        try:
            logger.info(f"Processing document {s3_key} with AWS Textract")
            
            # Strategy 1: Try DetectDocumentText (most reliable for basic text extraction)
            logger.info("Strategy 1: Trying DetectDocumentText...")
            try:
                text_content, page_count = await self._detect_document_text(s3_bucket, s3_key)
                if text_content and len(text_content.strip()) > 10:
                    logger.info(f"✅ DetectDocumentText succeeded: {len(text_content)} characters extracted")
                    return text_content, page_count
                else:
                    logger.warning("DetectDocumentText returned minimal text, trying AnalyzeDocument...")
            except Exception as e:
                logger.warning(f"DetectDocumentText failed: {e}, trying AnalyzeDocument...")
            
            # Strategy 2: Try AnalyzeDocument with TABLES and FORMS
            logger.info("Strategy 2: Trying AnalyzeDocument with TABLES and FORMS...")
            try:
                text_content, page_count = await self._analyze_document(s3_bucket, s3_key)
                if text_content and len(text_content.strip()) > 10:
                    logger.info(f"✅ AnalyzeDocument succeeded: {len(text_content)} characters extracted")
                    return text_content, page_count
                else:
                    logger.warning("AnalyzeDocument returned minimal text")
            except Exception as e:
                logger.warning(f"AnalyzeDocument failed: {e}")
            
            # Strategy 3: Convert PDF to images and extract
            logger.info("Strategy 3: Converting PDF to images and extracting...")
            try:
                text_content, page_count = await self._convert_pdf_to_images_and_extract(s3_bucket, s3_key)
                if text_content and len(text_content.strip()) > 10:
                    logger.info(f"✅ PDF-to-image extraction succeeded: {len(text_content)} characters extracted")
                    return text_content, page_count
                else:
                    logger.warning("PDF-to-image extraction returned minimal text")
            except Exception as e:
                logger.warning(f"PDF-to-image extraction failed: {e}")
            
            # If all strategies failed, raise error
            raise TextractError("All Textract strategies failed for this document")
                
        except Exception as e:
            logger.error(f"Sync Textract extraction failed: {e}")
            raise TextractError(f"Textract extraction failed: {e}")

    async def _detect_document_text(self, s3_bucket: str, s3_key: str) -> Tuple[str, int]:
        """
        Call AWS Textract DetectDocumentText API.
        This is the most reliable method for basic text extraction from PDFs.
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
                raise TextractError(f"Unsupported document type: {error_message}")
            elif error_code == 'InvalidS3ObjectException':
                raise TextractError(f"Invalid S3 object: {error_message}")
            else:
                raise TextractError(f"Textract error: {error_code} - {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error in DetectDocumentText: {e}")
            raise TextractError(f"Unexpected error: {e}")

    async def _analyze_document(self, s3_bucket: str, s3_key: str) -> Tuple[str, int]:
        """
        Call AWS Textract AnalyzeDocument API with TABLES and FORMS.
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
            
            # Extract text from blocks
            text_content = self._extract_text_from_blocks(response['Blocks'])
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

    async def _convert_pdf_to_images_and_extract(self, s3_bucket: str, s3_key: str) -> Tuple[str, int]:
        """
        Convert PDF to images and extract text using Textract.
        This is a fallback method when direct PDF processing fails.
        """
        try:
            logger.info(f"Converting PDF to images for Textract processing: s3://{s3_bucket}/{s3_key}")
            
            # Download the PDF from S3
            response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            pdf_content = response['Body'].read()
            
            # Convert PDF to images
            image_keys = await self._convert_pdf_to_images_and_upload(pdf_content, s3_bucket, s3_key)
            
            if not image_keys:
                raise TextractError("Failed to convert PDF to images")
            
            # Process all images with Textract
            all_text_content = []
            total_pages = len(image_keys)
            
            logger.info(f"Processing {len(image_keys)} images with Textract...")
            
            for i, image_key in enumerate(image_keys):
                try:
                    logger.info(f"Processing image {i + 1}/{len(image_keys)}: {image_key}")
                    
                    # Use DetectDocumentText for images
                    response = self.textract_client.detect_document_text(
                        Document={
                            'S3Object': {
                                'Bucket': s3_bucket,
                                'Name': image_key
                            }
                        }
                    )
                    
                    # Extract text from blocks
                    blocks = response.get('Blocks', [])
                    page_text = ""
                    for block in blocks:
                        if block['BlockType'] == 'LINE':
                            page_text += block.get('Text', '') + '\n'
                    
                    if page_text.strip():
                        all_text_content.append(f"--- Page {i + 1} ---\n{page_text.strip()}")
                        logger.info(f"✅ Page {i + 1} extracted: {len(page_text)} characters")
                    else:
                        logger.warning(f"⚠️ Page {i + 1} returned no text")
                        all_text_content.append(f"--- Page {i + 1} ---\n[No text detected]")
                    
                except Exception as e:
                    logger.warning(f"Failed to process image {i + 1}: {e}")
                    all_text_content.append(f"--- Page {i + 1} ---\n[Processing failed: {e}]")
                    continue
            
            # Combine all text
            combined_text = '\n\n'.join(all_text_content)
            
            # Clean up image files
            logger.info("Cleaning up image files...")
            await self._cleanup_s3_objects(s3_bucket, image_keys)
            
            if combined_text.strip():
                logger.info(f"✅ PDF-to-image extraction successful: {len(combined_text)} characters from {total_pages} pages")
                return combined_text, total_pages
            else:
                raise TextractError("No text extracted from images")
                
        except Exception as e:
            logger.error(f"PDF-to-image extraction failed: {e}")
            raise TextractError(f"PDF-to-image extraction failed: {e}")

    async def _convert_pdf_to_images_and_upload(self, pdf_content: bytes, s3_bucket: str, s3_key: str) -> List[str]:
        """
        Convert PDF to images and upload to S3. Return list of S3 keys.
        """
        try:
            # Try pdf2image first (if available)
            try:
                import pdf2image
                
                logger.info(f"Converting PDF to images with pdf2image...")
                images = pdf2image.convert_from_bytes(
                    pdf_content,
                    dpi=200,  # Good balance between quality and size
                    fmt='PNG',
                    thread_count=1,  # Single thread for Lambda compatibility
                    transparent=False,
                    grayscale=False
                )
                
                image_keys = []
                
                for page_num, image in enumerate(images):
                    # Convert PIL image to bytes
                    img_buffer = BytesIO()
                    image.save(img_buffer, format='PNG', optimize=True)
                    img_data = img_buffer.getvalue()
                    
                    # Upload image to S3
                    image_key = f"{s3_key.replace('.pdf', '')}_page_{page_num + 1}.png"
                    self.s3_client.put_object(
                        Bucket=s3_bucket,
                        Key=image_key,
                        Body=img_data,
                        ContentType='image/png'
                    )
                    image_keys.append(image_key)
                    
                    logger.info(f"Uploaded page {page_num + 1} as image: {image_key}")
                
                return image_keys
                
            except ImportError:
                logger.warning("pdf2image not available, trying alternative method...")
                return await self._convert_pdf_alternative_method(pdf_content, s3_bucket, s3_key)
            except Exception as e:
                logger.error(f"pdf2image conversion failed: {e}")
                return await self._convert_pdf_alternative_method(pdf_content, s3_bucket, s3_key)
                
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    async def _convert_pdf_alternative_method(self, pdf_content: bytes, s3_bucket: str, s3_key: str) -> List[str]:
        """
        Alternative PDF processing method when pdf2image fails.
        """
        try:
            logger.info("Using alternative PDF processing method...")
            
            # Try PyPDF2 to get page count
            try:
                import PyPDF2
                pdf_file = BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                page_count = len(pdf_reader.pages)
                
                logger.info(f"PDF has {page_count} pages")
                
                # Create simple text-based images for each page
                image_keys = []
                
                for page_num in range(page_count):
                    try:
                        # Extract text from page
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        
                        if page_text.strip():
                            # Create a simple image with the text
                            from PIL import Image, ImageDraw, ImageFont
                            
                            # Split text into lines
                            lines = page_text.split('\n')[:50]  # Limit lines
                            
                            # Calculate image size
                            max_line_length = max(len(line) for line in lines if line.strip())
                            num_lines = len([line for line in lines if line.strip()])
                            
                            char_width = 8
                            line_height = 20
                            padding = 40
                            
                            img_width = min(max_line_length * char_width + padding, 1200)
                            img_height = min(num_lines * line_height + padding, 1600)
                            
                            # Create image
                            img = Image.new('RGB', (img_width, img_height), color='white')
                            draw = ImageDraw.Draw(img)
                            
                            # Add text
                            y = 20
                            for line in lines:
                                if line.strip():
                                    display_line = line[:150] if len(line) > 150 else line
                                    draw.text((20, y), display_line, fill='black')
                                    y += line_height
                                    if y > img_height - 40:
                                        break
                            
                            # Convert to bytes
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='PNG', optimize=True)
                            img_bytes = img_buffer.getvalue()
                            
                            # Upload to S3
                            image_key = f"{s3_key.replace('.pdf', '')}_page_{page_num + 1}.png"
                            self.s3_client.put_object(
                                Bucket=s3_bucket,
                                Key=image_key,
                                Body=img_bytes,
                                ContentType='image/png'
                            )
                            image_keys.append(image_key)
                            
                            logger.info(f"Created text-based image for page {page_num + 1}: {image_key}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to process page {page_num + 1}: {e}")
                        continue
                
                return image_keys
                
            except Exception as e:
                logger.error(f"Alternative PDF processing failed: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Alternative PDF processing failed: {e}")
            return []

    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract text from Textract blocks preserving block structure and spatial relationships.
        """
        try:
            # Log block types for debugging
            block_types = {}
            for block in blocks:
                block_type = block.get('BlockType', 'UNKNOWN')
                block_types[block_type] = block_types.get(block_type, 0) + 1
            
            logger.info(f"Textract returned blocks: {block_types}")
            
            # Group blocks by page
            pages = {}
            for block in blocks:
                page_num = block.get('Page', 1)
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(block)
            
            all_text_content = []
            
            for page_num in sorted(pages.keys()):
                page_blocks = pages[page_num]
                logger.info(f"Processing page {page_num} with {len(page_blocks)} blocks")
                
                # Extract different block types with spatial awareness
                page_text = self._extract_structured_text_from_page(page_blocks)
                all_text_content.append(f"--- Page {page_num} ---\n{page_text}")
            
            extracted_text = '\n\n'.join(all_text_content)
            logger.info(f"Extracted {len(extracted_text)} characters with block structure from {len(pages)} pages")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from blocks: {e}")
            # Fallback: try to extract any text from blocks
            fallback_text = []
            for block in blocks:
                if 'Text' in block:
                    fallback_text.append(block['Text'])
            return ' '.join(fallback_text)

    def _extract_structured_text_from_page(self, page_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract structured text from page blocks preserving layout and relationships.
        """
        try:
            # Separate blocks by type
            tables = [b for b in page_blocks if b['BlockType'] == 'TABLE']
            key_value_sets = [b for b in page_blocks if b['BlockType'] == 'KEY_VALUE_SET']
            lines = [b for b in page_blocks if b['BlockType'] == 'LINE']
            words = [b for b in page_blocks if b['BlockType'] == 'WORD']
            
            text_sections = []
            
            # 1. Extract tables with structure
            if tables:
                logger.info(f"Found {len(tables)} tables on page")
                for i, table_block in enumerate(tables):
                    table_text = self._extract_table_structure(table_block, page_blocks)
                    if table_text:
                        text_sections.append(f"TABLE {i+1}:\n{table_text}")
            
            # 2. Extract key-value pairs (forms)
            if key_value_sets:
                logger.info(f"Found {len(key_value_sets)} key-value sets on page")
                form_text = self._extract_form_structure(key_value_sets, page_blocks)
                if form_text:
                    text_sections.append(f"FORM DATA:\n{form_text}")
            
            # 3. Extract lines with spatial positioning
            if lines:
                logger.info(f"Found {len(lines)} lines on page")
                lines_text = self._extract_lines_with_positioning(lines)
                if lines_text:
                    text_sections.append(f"TEXT CONTENT:\n{lines_text}")
            
            # 4. If no structured blocks, reconstruct from words
            if not text_sections and words:
                logger.info(f"No structured blocks found, reconstructing from {len(words)} words")
                words_text = self._extract_words_with_positioning(words)
                if words_text:
                    text_sections.append(f"TEXT CONTENT:\n{words_text}")
            
            return '\n\n'.join(text_sections)
            
        except Exception as e:
            logger.error(f"Error extracting structured text from page: {e}")
            return ""

    def _extract_table_structure(self, table_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract table structure preserving rows, columns, and cell relationships.
        """
        try:
            table_id = table_block['Id']
            table_text = []
            
            # Find all cells in this table
            cells = []
            for block in all_blocks:
                if (block['BlockType'] == 'CELL' and 
                    'Relationships' in block and 
                    any(rel['Type'] == 'CHILD' and table_id in rel.get('Ids', []) 
                        for rel in block['Relationships'])):
                    cells.append(block)
            
            if not cells:
                return ""
            
            # Sort cells by row and column
            cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            # Group cells by row
            rows = {}
            for cell in cells:
                row_index = cell.get('RowIndex', 0)
                if row_index not in rows:
                    rows[row_index] = []
                rows[row_index].append(cell)
            
            # Extract table content
            for row_index in sorted(rows.keys()):
                row_cells = sorted(rows[row_index], key=lambda x: x.get('ColumnIndex', 0))
                row_text = []
                
                for cell in row_cells:
                    cell_text = self._extract_cell_text(cell, all_blocks)
                    row_text.append(cell_text)
                
                table_text.append(" | ".join(row_text))
            
            return '\n'.join(table_text)
            
        except Exception as e:
            logger.error(f"Error extracting table structure: {e}")
            return ""

    def _extract_cell_text(self, cell_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract text from a table cell.
        """
        try:
            cell_text = ""
            if 'Relationships' in cell_block:
                for relationship in cell_block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in all_blocks if b['Id'] == child_id), None)
                            if child_block and child_block['BlockType'] == 'WORD':
                                cell_text += child_block.get('Text', '') + ' '
            
            return cell_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting cell text: {e}")
            return ""

    def _extract_form_structure(self, key_value_blocks: List[Dict[str, Any]], all_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract form structure preserving key-value relationships.
        """
        try:
            form_data = []
            
            # Separate keys and values
            keys = [b for b in key_value_blocks if 'KEY' in b.get('EntityTypes', [])]
            values = [b for b in key_value_blocks if 'VALUE' in b.get('EntityTypes', [])]
            
            # Create key-value pairs
            for key_block in keys:
                key_text = self._extract_block_text(key_block, all_blocks)
                value_text = self._find_value_for_key(key_block, values, all_blocks)
                
                if key_text and value_text:
                    form_data.append(f"{key_text}: {value_text}")
                elif key_text:
                    form_data.append(f"{key_text}: [No value found]")
            
            return '\n'.join(form_data)
            
        except Exception as e:
            logger.error(f"Error extracting form structure: {e}")
            return ""

    def _extract_block_text(self, block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract text from a block by following relationships.
        """
        try:
            text = ""
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in all_blocks if b['Id'] == child_id), None)
                            if child_block and child_block['BlockType'] == 'WORD':
                                text += child_block.get('Text', '') + ' '
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting block text: {e}")
            return ""

    def _find_value_for_key(self, key_block: Dict[str, Any], value_blocks: List[Dict[str, Any]], all_blocks: List[Dict[str, Any]]) -> str:
        """
        Find the value associated with a key block.
        """
        try:
            for value_block in value_blocks:
                if 'Relationships' in value_block:
                    for relationship in value_block['Relationships']:
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                if value_id == key_block['Id']:
                                    return self._extract_block_text(value_block, all_blocks)
            return ""
            
        except Exception as e:
            logger.error(f"Error finding value for key: {e}")
            return ""

    def _extract_lines_with_positioning(self, line_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract lines with spatial positioning information.
        """
        try:
            # Sort lines by vertical position (top to bottom)
            sorted_lines = sorted(line_blocks, key=lambda x: x.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0))
            
            lines_text = []
            for line_block in sorted_lines:
                line_text = line_block.get('Text', '').strip()
                if line_text:
                    # Add positioning info
                    geometry = line_block.get('Geometry', {}).get('BoundingBox', {})
                    top = geometry.get('Top', 0)
                    left = geometry.get('Left', 0)
                    confidence = line_block.get('Confidence', 0)
                    
                    # Format: [Position: Top=Y%, Left=X%] Text (Confidence: Z%)
                    position_info = f"[Top={top:.2%}, Left={left:.2%}]"
                    confidence_info = f"(Confidence: {confidence:.1f}%)"
                    lines_text.append(f"{position_info} {line_text} {confidence_info}")
            
            return '\n'.join(lines_text)
            
        except Exception as e:
            logger.error(f"Error extracting lines with positioning: {e}")
            return ""

    def _extract_words_with_positioning(self, word_blocks: List[Dict[str, Any]]) -> str:
        """
        Extract words with spatial positioning and reconstruct text flow.
        """
        try:
            # Sort words by position (top to bottom, left to right)
            sorted_words = sorted(word_blocks, key=lambda w: (
                w.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0),
                w.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0)
            ))
            
            # Group words into lines based on Y position
            lines = []
            current_line = []
            current_y = None
            y_tolerance = 0.02  # Tighter tolerance for better line detection
            
            for word_block in sorted_words:
                word_text = word_block.get('Text', '').strip()
                if not word_text:
                    continue
                
                # Get Y position
                y_pos = word_block.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0)
                
                # Check if this word is on the same line
                if current_y is None or abs(y_pos - current_y) <= y_tolerance:
                    current_line.append(word_block)
                    current_y = y_pos
                else:
                    # New line
                    if current_line:
                        lines.append(current_line)
                    current_line = [word_block]
                    current_y = y_pos
            
            # Add the last line
            if current_line:
                lines.append(current_line)
            
            # Process each line
            lines_text = []
            for line_num, line_words in enumerate(lines):
                # Sort words in line by X position
                line_words.sort(key=lambda w: w.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0))
                
                line_text = " ".join(word.get('Text', '').strip() for word in line_words if word.get('Text', '').strip())
                
                if line_text:
                    # Add line positioning info
                    first_word = line_words[0]
                    geometry = first_word.get('Geometry', {}).get('BoundingBox', {})
                    top = geometry.get('Top', 0)
                    left = geometry.get('Left', 0)
                    
                    position_info = f"[Line {line_num+1}: Top={top:.2%}, Left={left:.2%}]"
                    lines_text.append(f"{position_info} {line_text}")
            
            return '\n'.join(lines_text)
            
        except Exception as e:
            logger.error(f"Error extracting words with positioning: {e}")
            return ""

    async def upload_to_s3_and_extract(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: DocumentType = DocumentType.GENERAL,
        user_id: str = "anonymous"
    ) -> Tuple[str, int]:
        """
        Upload file to S3 and extract text using AWS Textract.
        """
        try:
            # Ensure clients are initialized
            self._ensure_clients_initialized()
            
            if not self.s3_client:
                raise TextractError("AWS S3 client not available")
            
            bucket_name = aws_config.s3_bucket_name
            
            # Upload file to S3
            s3_key = f"temp-documents/{user_id}/{filename}"
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            logger.info(f"Uploaded {filename} to S3: s3://{bucket_name}/{s3_key}")
            
            # Extract text using Textract
            text_content, page_count = await self.extract_text_from_s3_pdf(bucket_name, s3_key, document_type)
            
            # Clean up S3 object
            await self._cleanup_s3_objects(bucket_name, [s3_key])
            
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Upload and extraction failed: {e}")
            raise TextractError(f"Upload and extraction failed: {e}")

    async def process_preprocessed_document(
        self, 
        bucket_name: str, 
        s3_key: str, 
        document_type: DocumentType = DocumentType.GENERAL
    ) -> Tuple[str, int]:
        """
        Process a preprocessed document that's already in S3.
        """
        try:
            return await self.extract_text_from_s3_pdf(bucket_name, s3_key, document_type)
        except Exception as e:
            logger.error(f"Error processing preprocessed document: {e}")
            raise TextractError(f"Preprocessed document processing failed: {e}")

    async def _try_pypdf2_extraction(self, file_content: bytes, filename: str) -> Tuple[str, int]:
        """
        Try PyPDF2 extraction as a fallback method.
        """
        try:
            import PyPDF2
            pdf = PyPDF2.PdfReader(BytesIO(file_content))
            text_content = []
            page_count = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(f"Page {i+1}: {page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i+1}: {e}")
            
            if text_content:
                result = '\n\n'.join(text_content)
                logger.info(f"PyPDF2 extraction successful: {filename} ({page_count} pages)")
                return result, page_count
            else:
                logger.warning(f"PyPDF2 extracted no text from {filename}")
                return "", page_count
                
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed for {filename}: {e}")
            return "", 0

    async def _try_raw_text_extraction(self, file_content: bytes, filename: str) -> str:
        """
        Try raw text extraction as a fallback method.
        """
        try:
            # Try to decode as text
            text_content = file_content.decode('utf-8', errors='ignore')
            if text_content.strip():
                logger.info(f"Raw text extraction successful for {filename}")
                return text_content
            else:
                logger.warning(f"Raw text extraction returned empty content for {filename}")
                return ""
        except Exception as e:
            logger.warning(f"Raw text extraction failed for {filename}: {e}")
            return ""

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
                "PDF-to-image conversion is available as fallback"
            ],
            "troubleshooting": [
                "If you get 'Unsupported document type', PDF will be converted to images",
                "Convert browser-generated PDFs to standard PDFs",
                "Use image files (PNG/JPEG) as an alternative",
                "Check if the PDF is encrypted or corrupted",
                "PDF-to-image conversion handles problematic PDFs automatically"
            ]
        }
    
    def estimate_cost(self, document_type: DocumentType, page_count: int = 1) -> Dict[str, Any]:
        """
        Estimate the cost of Textract processing.
        """
        # DetectDocumentText: $1.50 per 1,000 pages
        # AnalyzeDocument: $5.00 per 1,000 pages
        if document_type in [DocumentType.FORM, DocumentType.INVOICE, DocumentType.TABLE_HEAVY]:
            cost_per_1000_pages = 5.00
            api_type = "AnalyzeDocument"
        else:
            cost_per_1000_pages = 1.50
            api_type = "DetectDocumentText"
        
        estimated_cost = (page_count / 1000) * cost_per_1000_pages
        
        return {
            "api_type": api_type,
            "page_count": page_count,
            "cost_per_1000_pages": cost_per_1000_pages,
            "estimated_cost": estimated_cost,
            "currency": "USD"
        }

# Global instance
textract_service = AWSTextractService() 