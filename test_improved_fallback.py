#!/usr/bin/env python3
"""
Test script for improved fallback mechanism with corruption detection and timeouts.
"""

import asyncio
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.aws_textract_service import AWSTextractService
from src.core.logging import setup_logging

async def test_improved_fallback():
    """Test the improved fallback mechanism."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Initialize the service
    textract_service = AWSTextractService()
    
    # Test with the problematic PDF
    pdf_path = "Namecheap.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file {pdf_path} not found")
        return
    
    logger.info(f"Testing improved fallback with {pdf_path}")
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        logger.info(f"PDF file size: {len(file_content)} bytes")
        
        # Test corruption detection
        is_corrupted = textract_service._is_pdf_severely_corrupted(file_content)
        logger.info(f"PDF corruption check result: {is_corrupted}")
        
        if is_corrupted:
            logger.info("PDF detected as corrupted, should skip extraction attempts")
            return
        
        # Test fallback extraction
        logger.info("Testing fallback extraction...")
        start_time = asyncio.get_event_loop().time()
        
        text_content, page_count = await textract_service._fallback_pdf_extraction(
            file_content, pdf_path, "test_user"
        )
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        logger.info(f"Fallback extraction completed in {duration:.2f} seconds")
        logger.info(f"Extracted {len(text_content)} characters, {page_count} pages")
        
        # Show first 500 characters of extracted text
        preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
        logger.info(f"Text preview: {preview}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

async def test_corruption_detection():
    """Test the corruption detection with various file types."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    textract_service = AWSTextractService()
    
    # Test cases
    test_cases = [
        ("valid_pdf_header", b"%PDF-1.4\n%%EOF"),
        ("missing_pdf_header", b"Not a PDF file"),
        ("missing_eof", b"%PDF-1.4\nSome content"),
        ("too_small", b"%PDF-1.4\n%%EOF"),
        ("many_nulls", b"%PDF-1.4" + b"\x00" * 1000 + b"\n%%EOF"),
        ("normal_pdf", b"%PDF-1.4\n" + b"Normal content " * 100 + b"\n%%EOF"),
    ]
    
    for test_name, content in test_cases:
        # Make the "too_small" test actually small
        if test_name == "too_small":
            content = content[:100]  # Make it less than 1KB
        
        is_corrupted = textract_service._is_pdf_severely_corrupted(content)
        logger.info(f"{test_name}: {is_corrupted} (size: {len(content)} bytes)")

if __name__ == "__main__":
    async def main():
        print("Testing corruption detection...")
        await test_corruption_detection()
        
        print("\nTesting improved fallback...")
        await test_improved_fallback()
    
    asyncio.run(main()) 