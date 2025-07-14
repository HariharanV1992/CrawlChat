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
            
            logger.info(f"Starting document analysis job for s3://{s3_bucket}/{s3_key}")
            logger.info(f"Feature types: {feature_types}")
            
            response = self.textract_client.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
                FeatureTypes=feature_types
            )
            
            job_id = response['JobId']
            logger.info(f"Document analysis job started with ID: {job_id}")
            
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
            
            logger.info(f"Waiting for job completion: {job_id}")
            
            while True:
                result = self.textract_client.get_document_analysis(JobId=job_id)
                status = result['JobStatus']
                logger.info(f"Job Status: {status}")
                
                if status == 'SUCCEEDED':
                    logger.info(f"Job {job_id} completed successfully")
                    return
                elif status == 'FAILED':
                    error_message = result.get('StatusMessage', 'Unknown error')
                    logger.error(f"Job {job_id} failed: {error_message}")
                    raise TextractError(f"Textract job failed: {error_message}")
                elif status == 'IN_PROGRESS':
                    logger.info(f"Job {job_id} still in progress, waiting {poll_interval} seconds...")
                    await asyncio.sleep(poll_interval)
                else:
                    logger.warning(f"Unknown job status: {status}")
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
            
            logger.info(f"Retrieving all blocks from job: {job_id}")
            
            blocks = []
            next_token = None
            
            while True:
                if next_token:
                    response = self.textract_client.get_document_analysis(
                        JobId=job_id, 
                        NextToken=next_token
                    )
                else:
                    response = self.textract_client.get_document_analysis(JobId=job_id)
                
                blocks.extend(response['Blocks'])
                next_token = response.get("NextToken")
                
                if not next_token:
                    break
            
            logger.info(f"Retrieved {len(blocks)} blocks from job {job_id}")
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
            
            logger.info(f"Organized {len(blocks)} blocks into {len(organized)} types")
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
            logger.info(f"Starting comprehensive async document processing: s3://{s3_bucket}/{s3_key}")
            
            if feature_types is None:
                feature_types = ["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
            
            # Start the async job
            job_id = await self.start_document_analysis_job(s3_bucket, s3_key, feature_types)
            
            # Wait for completion
            await self.wait_for_job_completion(job_id)
            
            # Get all blocks
            all_blocks = await self.get_all_blocks_from_job(job_id)
            
            # Organize blocks by type
            organized_blocks = self.organize_blocks_by_type(all_blocks)
            
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
                    logger.info(f"✅ Organized blocks saved to {output_filename}")
                    results["output_file"] = output_filename
                except Exception as e:
                    logger.error(f"Failed to save organized blocks: {e}")
            
            logger.info(f"✅ Comprehensive async document processing completed successfully")
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
            
            logger.info(f"Extracted: {len(extracted_data['text_lines'])} text lines, "
                       f"{len(extracted_data['paragraphs'])} paragraphs, "
                       f"{len(extracted_data['form_data'])} form fields, "
                       f"{len(extracted_data['tables'])} tables, "
                       f"{extracted_data['page_count']} pages")
            
        except Exception as e:
            logger.error(f"Error extracting specific data types: {e}")
        
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
            logger.error(f"Error extracting form data: {e}")
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
            logger.error(f"Error finding value block: {e}")
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
            logger.error(f"Error getting text from block: {e}")
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
            logger.error(f"Error extracting tables: {e}")
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
                logger.warning("No LINE blocks found for paragraph extraction")
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
            
            logger.info(f"Extracted {len(paragraphs)} paragraphs from {len(lines_by_page)} pages")
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
            
            logger.info(f"Enhanced {len(enhanced_paragraphs)} paragraphs for vector storage")
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
            logger.info(f"Processing preprocessed document: s3://{s3_bucket}/{s3_key} (type: {document_type.value})")
            
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
            
            logger.info(f"Successfully processed preprocessed document: {len(text_content)} characters, {page_count} pages")
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
            logger.info(f"Uploading and extracting document: {filename} (type: {document_type.value})")
            
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
            logger.info(f"Document uploaded to S3: {s3_key}")
            
            # Process with Textract
            text_content, page_count = await self.process_preprocessed_document(
                s3_bucket=upload_result["bucket"],
                s3_key=s3_key,
                document_type=document_type
            )
            
            # Clean up temporary file
            try:
                await unified_storage_service.delete_file(s3_key)
                logger.info(f"Cleaned up temporary file: {s3_key}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file {s3_key}: {cleanup_error}")
            
            return text_content, page_count
            
        except Exception as e:
            logger.error(f"Error uploading and extracting document: {e}")
            raise TextractError(f"Failed to upload and extract document: {e}")

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
            logger.info(f"Extracting text from S3 PDF: s3://{s3_bucket}/{s3_key} (type: {document_type.value})")
            
            # Use the comprehensive async processing for PDF documents
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
            
            logger.info(f"Successfully extracted text from S3 PDF: {len(text_content)} characters, {page_count} pages")
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
            logger.info(f"Trying PyPDF2 extraction for: {filename}")
            
            # Import PyPDF2
            try:
                import PyPDF2
            except ImportError:
                logger.warning("PyPDF2 not available, skipping PyPDF2 extraction")
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
                    logger.warning(f"Error extracting text from page {page_num}: {page_error}")
                    continue
            
            logger.info(f"PyPDF2 extraction completed: {len(text_content)} characters, {page_count} pages")
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
            logger.info(f"Trying aggressive text extraction for: {filename}")
            
            # Try to decode as text first
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    logger.warning("Could not decode file content as text")
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
            
            logger.info(f"Aggressive text extraction completed: {len(text_content)} characters")
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
            logger.info(f"Trying raw text extraction for: {filename}")
            
            # For images, we can't extract text without OCR
            # This is a placeholder for future OCR implementation
            logger.warning("Raw text extraction not implemented for images (requires OCR)")
            return ""
            
        except Exception as e:
            logger.error(f"Raw text extraction failed: {e}")
            return ""

# Global instance
textract_service = AWSTextractService() 