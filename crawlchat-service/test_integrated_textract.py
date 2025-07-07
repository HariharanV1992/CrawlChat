#!/usr/bin/env python3
"""
Test script for integrated Textract service with PDF-to-image conversion.
"""

import asyncio
import os
import sys
import logging

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.src.services.aws_textract_service import textract_service, DocumentType
from common.src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pdf_extraction():
    """Test PDF extraction with integrated image conversion."""
    try:
        # Test with a sample PDF file
        test_pdf_path = "Namecheap.pdf"  # Use the existing test PDF
        
        if not os.path.exists(test_pdf_path):
            logger.error(f"Test PDF file not found: {test_pdf_path}")
            return
        
        logger.info(f"Testing PDF extraction with: {test_pdf_path}")
        
        # Read the PDF file
        with open(test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        logger.info(f"PDF file size: {len(pdf_content)} bytes")
        
        # Test the integrated extraction
        text_content, page_count = await textract_service.upload_to_s3_and_extract(
            file_content=pdf_content,
            filename=os.path.basename(test_pdf_path),
            document_type=DocumentType.GENERAL,
            user_id="test_user"
        )
        
        logger.info(f"✅ Extraction successful!")
        logger.info(f"📄 Pages extracted: {page_count}")
        logger.info(f"📝 Text length: {len(text_content)} characters")
        logger.info(f"📄 First 200 characters: {text_content[:200]}...")
        
        return text_content, page_count
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return None, None

async def test_image_extraction():
    """Test direct image extraction."""
    try:
        # This would test with a direct image file
        logger.info("Image extraction test would go here")
        logger.info("(No test image provided)")
        
    except Exception as e:
        logger.error(f"❌ Image test failed: {e}")

async def main():
    """Run all tests."""
    logger.info("🧪 Starting integrated Textract service tests...")
    
    # Test PDF extraction
    await test_pdf_extraction()
    
    # Test image extraction
    await test_image_extraction()
    
    logger.info("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 