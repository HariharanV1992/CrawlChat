#!/usr/bin/env python3
"""
Test script for hybrid PDF extraction approach.
Tests the new strategy: local extraction first, then Textract as fallback.
"""

import asyncio
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.aws_textract_service import AWSTextractService
from src.core.logging import setup_logging

async def test_hybrid_extraction():
    """Test the hybrid PDF extraction approach."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Initialize the service
    textract_service = AWSTextractService()
    
    # Test with the problematic PDF
    pdf_path = "Namecheap.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file {pdf_path} not found")
        return
    
    logger.info(f"Testing hybrid extraction with {pdf_path}")
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        logger.info(f"PDF file size: {len(file_content)} bytes")
        
        # Test the hybrid extraction method
        logger.info("Testing hybrid PDF extraction...")
        start_time = asyncio.get_event_loop().time()
        
        from src.services.aws_textract_service import DocumentType
        
        text_content, page_count = await textract_service._hybrid_pdf_extraction(
            file_content, pdf_path, "test-bucket", "test-key", 
            DocumentType.GENERAL, "test_user"
        )
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        logger.info(f"Hybrid extraction completed in {duration:.2f} seconds")
        logger.info(f"Extracted {len(text_content)} characters, {page_count} pages")
        
        # Show first 500 characters of extracted text
        preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
        logger.info(f"Text preview: {preview}")
        
        # Check if extraction was successful
        if len(text_content.strip()) > 50:
            logger.info("✅ Hybrid extraction successful!")
            return True
        else:
            logger.warning("⚠️ Hybrid extraction returned minimal content")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def test_aggressive_extraction():
    """Test the aggressive text extraction method."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    textract_service = AWSTextractService()
    
    # Test with the problematic PDF
    pdf_path = "Namecheap.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file {pdf_path} not found")
        return
    
    try:
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        logger.info(f"Testing aggressive text extraction with {pdf_path}")
        
        # Test aggressive extraction directly
        aggressive_text = await textract_service._try_aggressive_text_extraction(file_content, pdf_path)
        
        if aggressive_text:
            logger.info(f"✅ Aggressive extraction successful: {len(aggressive_text)} characters")
            logger.info(f"Sample text: {aggressive_text[:200]}...")
            return True
        else:
            logger.warning("⚠️ Aggressive extraction found no text")
            return False
            
    except Exception as e:
        logger.error(f"Aggressive extraction test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("Testing hybrid extraction...")
        hybrid_result = await test_hybrid_extraction()
        
        print("\nTesting aggressive extraction...")
        aggressive_result = await test_aggressive_extraction()
        
        print(f"\nResults:")
        print(f"Hybrid extraction: {'✅ PASS' if hybrid_result else '❌ FAIL'}")
        print(f"Aggressive extraction: {'✅ PASS' if aggressive_result else '❌ FAIL'}")
    
    asyncio.run(main()) 