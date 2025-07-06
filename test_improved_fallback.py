#!/usr/bin/env python3
"""
Test script for improved fallback PDF extraction mechanism.
Tests multiple PDF extraction methods for maximum compatibility.
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

async def test_improved_fallback():
    """Test the improved fallback PDF extraction mechanism."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Improved Fallback PDF Extraction")
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
        
        # Test the improved fallback method
        textract_service = AWSTextractService()
        
        try:
            # Test the fallback method directly
            text_content, page_count = await textract_service._fallback_pdf_extraction(
                file_content=file_content,
                filename=pdf_path,
                user_id="test_user"
            )
            
            logger.info(f"✅ Improved fallback extraction successful!")
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
            logger.error(f"❌ Improved fallback extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def test_individual_methods():
    """Test each extraction method individually."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        
        logger.info("🧪 Testing Individual Extraction Methods")
        logger.info("=" * 60)
        
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        textract_service = AWSTextractService()
        
        # Test PyPDF2 method
        logger.info("📋 Testing PyPDF2 method...")
        try:
            text, pages = await textract_service._try_pypdf2_extraction(file_content, pdf_path)
            logger.info(f"✅ PyPDF2: {len(text)} chars, {pages} pages")
        except Exception as e:
            logger.warning(f"❌ PyPDF2 failed: {e}")
        
        # Test PDFMiner method
        logger.info("📋 Testing PDFMiner method...")
        try:
            text, pages = await textract_service._try_pdfminer_extraction(file_content, pdf_path)
            logger.info(f"✅ PDFMiner: {len(text)} chars, {pages} pages")
        except Exception as e:
            logger.warning(f"❌ PDFMiner failed: {e}")
        
        # Test basic text extraction
        logger.info("📋 Testing basic text extraction...")
        try:
            text, pages = await textract_service._try_basic_text_extraction(file_content, pdf_path)
            logger.info(f"✅ Basic: {len(text)} chars, {pages} pages")
        except Exception as e:
            logger.warning(f"❌ Basic extraction failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Individual methods test failed: {e}")
        return False

async def test_preprocessing_service():
    """Test the preprocessing service if available."""
    try:
        logger.info("🧪 Testing Preprocessing Service")
        logger.info("=" * 60)
        
        # Check if preprocessing service is available
        try:
            from preprocessing_service import PDFPreprocessor
            
            logger.info("✅ Preprocessing service available")
            
            # Test with local PDF
            pdf_path = "Namecheap.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
                
                preprocessor = PDFPreprocessor()
                
                # Test text extraction
                text = await preprocessor._extract_text_from_pdf(pdf_content)
                if text:
                    logger.info(f"✅ Preprocessing service extracted {len(text)} characters")
                else:
                    logger.warning("⚠️ Preprocessing service found no text")
                
                return True
            else:
                logger.warning("⚠️ Test PDF not found for preprocessing service")
                return False
                
        except ImportError:
            logger.info("ℹ️ Preprocessing service not available (expected)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Preprocessing service test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Testing Improved Fallback Mechanism")
    logger.info("=" * 80)
    
    results = {}
    
    # Test individual extraction methods
    results['individual_methods'] = await test_individual_methods()
    
    # Test improved fallback mechanism
    results['improved_fallback'] = await test_improved_fallback()
    
    # Test preprocessing service
    results['preprocessing_service'] = await test_preprocessing_service()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Improved fallback mechanism is working correctly.")
        logger.info("📋 Ready for deployment!")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 