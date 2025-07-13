"""
AWS Textract Service for document text extraction
Clean version with all syntax errors fixed
"""

import logging
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import asyncio
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter

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
                access_key = os.getenv('AWS_ACCESS_KEY_ID')
                secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                
                if access_key and secret_key:
                    logger.info("Running locally, using provided AWS credentials")
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

    async def detect_document_text_lambda_style(self, s3_bucket: str, s3_key: str) -> Tuple[List[str], int]:
        """
        Extract text from document using Lambda-style DetectDocumentText approach.
        Returns list of text lines and page count.
        """
        try:
            self._ensure_clients_initialized()
            
            if not self.textract_client:
                raise TextractError("AWS Textract client not available")
            
            logger.info(f"Calling DetectDocumentText Lambda-style for s3://{s3_bucket}/{s3_key}")
            
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
            
            logger.info(f"Lambda-style DetectDocumentText completed: {len(line_text)} lines, {page_count} pages")
            
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
            logger.error(f"Error extracting text Lambda-style: {e}")
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
            
            logger.info(f"Calling AnalyzeDocument Lambda-style for forms: s3://{s3_bucket}/{s3_key}")
            
            # Get key-value maps using Lambda-style approach
            key_map, value_map, block_map = await self._get_kv_map_lambda_style(s3_bucket, s3_key)
            
            # Get key-value relationships
            kvs = self._get_kv_relationship_lambda_style(key_map, value_map, block_map)
            
            logger.info(f"Lambda-style form analysis completed: {len(kvs)} key-value pairs found")
            
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
            logger.info(f'Lambda-style form analysis returned {len(blocks)} blocks')

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
            logger.error(f"Error getting KV relationships Lambda-style: {e}")
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
            logger.error(f"Error finding value block Lambda-style: {e}")
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
            logger.error(f"Error getting text Lambda-style: {e}")
            return ""

    async def process_document_lambda_style(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        """
        Process document using Lambda-style approach combining text detection and form analysis.
        """
        try:
            logger.info(f"Processing document Lambda-style: s3://{s3_bucket}/{s3_key}")
            
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
                logger.info(f"Lambda-style text detection successful: {len(text_lines)} lines")
            except Exception as e:
                logger.warning(f"Lambda-style text detection failed: {e}")
            
            # Try form analysis
            try:
                form_data = await self.analyze_document_forms_lambda_style(s3_bucket, s3_key)
                results["form_data"] = form_data
                logger.info(f"Lambda-style form analysis successful: {len(form_data)} key-value pairs")
            except Exception as e:
                logger.warning(f"Lambda-style form analysis failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Lambda-style document processing failed: {e}")
            raise TextractError(f"Lambda-style processing failed: {e}")

# Global instance
textract_service = AWSTextractService() 