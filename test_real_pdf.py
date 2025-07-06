#!/usr/bin/env python3
"""
Test script using the actual Namecheap.pdf file to test fallback mechanism.
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

async def test_real_pdf_fallback():
    """Test fallback extraction with the actual Namecheap.pdf file."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Real PDF Fallback Extraction")
        logger.info("=" * 50)
        
        # Use the actual Namecheap.pdf file
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        # Read the PDF file
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        logger.info(f"📄 Testing with file: {pdf_path} ({len(file_content)} bytes)")
        
        # Test the fallback method directly
        textract_service = AWSTextractService()
        
        try:
            # Test the fallback method
            text_content, page_count = await textract_service._fallback_pdf_extraction(
                file_content=file_content,
                filename=pdf_path,
                user_id="test_user"
            )
            
            logger.info(f"✅ Fallback extraction successful!")
            logger.info(f"📊 Pages: {page_count}")
            logger.info(f"📝 Text length: {len(text_content)} characters")
            logger.info(f"📄 First 300 chars: {text_content[:300]}...")
            
            # Check if we got meaningful content
            if len(text_content.strip()) > 50:
                logger.info("✅ Extracted meaningful content!")
                return True
            else:
                logger.warning("⚠️ Extracted content seems too short")
                return False
            
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def test_pypdf2_direct():
    """Test PyPDF2 directly with the Namecheap.pdf file."""
    try:
        logger.info("🧪 Testing PyPDF2 Direct Extraction")
        logger.info("=" * 50)
        
        pdf_path = "Namecheap.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return False
        
        # Test PyPDF2 directly
        from PyPDF2 import PdfReader
        
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            
        logger.info(f"📄 PDF loaded: {len(reader.pages)} pages")
        
        # Extract text from each page
        all_text = ""
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    logger.info(f"✅ Page {page_num + 1}: {len(page_text)} characters")
                else:
                    logger.warning(f"⚠️ Page {page_num + 1}: No text extracted")
            except Exception as e:
                logger.error(f"❌ Page {page_num + 1}: Error - {e}")
        
        logger.info(f"📝 Total extracted text: {len(all_text)} characters")
        if all_text.strip():
            logger.info(f"📄 Sample text: {all_text[:200]}...")
            return True
        else:
            logger.warning("⚠️ No text extracted from any page")
            return False
            
    except Exception as e:
        logger.error(f"❌ PyPDF2 direct test failed: {e}")
        return False

async def main():
    """Run the real PDF tests."""
    logger.info("🚀 Testing Real PDF Fallback Mechanism")
    logger.info("=" * 60)
    
    results = {}
    
    # Test PyPDF2 direct extraction
    results['pypdf2_direct'] = await test_pypdf2_direct()
    
    # Test fallback extraction
    results['fallback_extraction'] = await test_real_pdf_fallback()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Fallback mechanism is working correctly.")
        logger.info("📋 Ready for deployment!")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 