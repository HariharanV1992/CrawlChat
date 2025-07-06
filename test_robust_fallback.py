#!/usr/bin/env python3
"""
Test script for robust fallback PDF extraction mechanism.
Tests the improved fallback with raw text extraction for corrupted PDFs.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_robust_fallback():
    """Test the robust fallback PDF extraction mechanism."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Robust Fallback PDF Extraction")
        logger.info("=" * 60)
        
        # Use the actual Namecheap.pdf file
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        # Read the PDF file
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        logger.info(f"📄 Testing with file: {pdf_path} ({len(file_content)} bytes)")
        
        # Test the robust fallback method
        textract_service = AWSTextractService()
        
        try:
            # Test the fallback method directly
            text_content, page_count = await textract_service._fallback_pdf_extraction(
                file_content=file_content,
                filename=pdf_path,
                user_id="test_user"
            )
            
            logger.info(f"✅ Robust fallback extraction successful!")
            logger.info(f"📊 Pages: {page_count}")
            logger.info(f"📝 Text length: {len(text_content)} characters")
            logger.info(f"📄 First 300 chars: {text_content[:300]}...")
            
            # Check if we got meaningful content
            if len(text_content.strip()) > 10:
                logger.info("✅ Extracted meaningful content!")
                return True
            else:
                logger.warning("⚠️ Extracted content seems too short")
                return False
            
        except Exception as e:
            logger.error(f"❌ Robust fallback extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def test_raw_text_extraction():
    """Test the raw text extraction method specifically."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        
        logger.info("🧪 Testing Raw Text Extraction")
        logger.info("=" * 60)
        
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        textract_service = AWSTextractService()
        
        # Test raw text extraction directly
        try:
            raw_text = await textract_service._try_raw_text_extraction(file_content, pdf_path)
            logger.info(f"✅ Raw text extraction: {len(raw_text)} characters")
            if raw_text:
                logger.info(f"📄 Sample text: {raw_text[:200]}...")
                return True
            else:
                logger.warning("⚠️ No text extracted")
                return False
                
        except Exception as e:
            logger.error(f"❌ Raw text extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Raw text test failed: {e}")
        return False

async def test_method_order():
    """Test the extraction methods in the correct order."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        
        logger.info("🧪 Testing Method Order")
        logger.info("=" * 60)
        
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        textract_service = AWSTextractService()
        
        # Test PDFMiner first (most robust)
        logger.info("📋 Testing PDFMiner (most robust)...")
        try:
            text, pages = await textract_service._try_pdfminer_extraction(file_content, pdf_path)
            logger.info(f"✅ PDFMiner: {len(text)} chars, {pages} pages")
            if len(text.strip()) > 10:
                logger.info("✅ PDFMiner succeeded - this should be used!")
                return True
        except Exception as e:
            logger.warning(f"❌ PDFMiner failed: {e}")
        
        # Test PyPDF2 second
        logger.info("📋 Testing PyPDF2...")
        try:
            text, pages = await textract_service._try_pypdf2_extraction(file_content, pdf_path)
            logger.info(f"✅ PyPDF2: {len(text)} chars, {pages} pages")
            if len(text.strip()) > 10:
                logger.info("✅ PyPDF2 succeeded")
                return True
        except Exception as e:
            logger.warning(f"❌ PyPDF2 failed: {e}")
        
        # Test basic extraction
        logger.info("📋 Testing basic extraction...")
        try:
            text, pages = await textract_service._try_basic_text_extraction(file_content, pdf_path)
            logger.info(f"✅ Basic: {len(text)} chars, {pages} pages")
            if len(text.strip()) > 10:
                logger.info("✅ Basic extraction succeeded")
                return True
        except Exception as e:
            logger.warning(f"❌ Basic extraction failed: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Method order test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Testing Robust Fallback Mechanism")
    logger.info("=" * 80)
    
    results = {}
    
    # Test method order
    results['method_order'] = await test_method_order()
    
    # Test raw text extraction
    results['raw_text_extraction'] = await test_raw_text_extraction()
    
    # Test robust fallback mechanism
    results['robust_fallback'] = await test_robust_fallback()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Robust fallback mechanism is working correctly.")
        logger.info("📋 Ready for deployment!")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 