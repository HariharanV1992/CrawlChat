#!/usr/bin/env python3
"""
Simple local test for fallback PDF extraction mechanism.
Tests the core functionality without external API calls.
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

async def test_fallback_extraction_logic():
    """Test the fallback PDF extraction logic without external dependencies."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Fallback PDF Extraction Logic")
        logger.info("=" * 50)
        
        # Create a simple PDF content for testing
        # This simulates a PDF that would fail Textract
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        # Test the fallback method directly
        textract_service = AWSTextractService()
        
        logger.info("📄 Testing fallback PDF extraction...")
        
        try:
            # Test the fallback method
            text_content, page_count = await textract_service._fallback_pdf_extraction(
                file_content=test_pdf_content,
                filename="test_fallback.pdf",
                user_id="test_user"
            )
            
            logger.info(f"✅ Fallback extraction successful!")
            logger.info(f"📊 Pages: {page_count}")
            logger.info(f"📝 Text length: {len(text_content)} characters")
            logger.info(f"📄 Extracted text: {text_content[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def test_textract_service_initialization():
    """Test Textract service initialization."""
    try:
        from src.services.aws_textract_service import AWSTextractService
        
        logger.info("🧪 Testing Textract Service Initialization")
        logger.info("=" * 50)
        
        # Test service initialization
        textract_service = AWSTextractService()
        
        logger.info("✅ Textract service initialized successfully")
        logger.info(f"📦 S3 client available: {textract_service.s3_client is not None}")
        logger.info(f"📦 Textract client available: {textract_service.textract_client is not None}")
        
        # Test configuration
        from src.core.aws_config import aws_config
        logger.info(f"📦 S3 bucket: {aws_config.s3_bucket}")
        logger.info(f"📦 Textract region: {aws_config.textract_region}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Textract service test failed: {e}")
        return False

async def test_document_processing_error():
    """Test custom exception handling."""
    try:
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Document Processing Error Handling")
        logger.info("=" * 50)
        
        # Test exception creation
        error = DocumentProcessingError("Test error message")
        logger.info(f"✅ Exception created: {error}")
        
        # Test exception with details
        detailed_error = DocumentProcessingError("Detailed error", details={"file": "test.pdf", "reason": "unsupported"})
        logger.info(f"✅ Detailed exception: {detailed_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Exception test failed: {e}")
        return False

async def test_pypdf2_availability():
    """Test PyPDF2 availability."""
    try:
        logger.info("🧪 Testing PyPDF2 Availability")
        logger.info("=" * 50)
        
        try:
            from PyPDF2 import PdfReader
            logger.info("✅ PyPDF2 is available")
            
            # Test basic functionality
            from io import BytesIO
            test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
            
            pdf_file = BytesIO(test_content)
            reader = PdfReader(pdf_file)
            
            logger.info(f"✅ PyPDF2 can read PDF: {len(reader.pages)} pages")
            
            # Try to extract text
            if len(reader.pages) > 0:
                page = reader.pages[0]
                text = page.extract_text()
                logger.info(f"✅ Text extraction works: {len(text)} characters")
            
            return True
            
        except ImportError:
            logger.error("❌ PyPDF2 is not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ PyPDF2 test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Simple Local Tests")
    logger.info("=" * 60)
    
    # Check environment
    logger.info("🔧 Environment Check:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")
    logger.info(f"   AWS credentials: {'Available' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}")
    
    results = {}
    
    # Test PyPDF2 availability
    results['pypdf2'] = await test_pypdf2_availability()
    
    # Test Textract service initialization
    results['textract_init'] = await test_textract_service_initialization()
    
    # Test document processing error handling
    results['error_handling'] = await test_document_processing_error()
    
    # Test fallback extraction logic
    results['fallback_logic'] = await test_fallback_extraction_logic()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Your local setup is working correctly.")
        logger.info("📋 Ready for deployment!")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 