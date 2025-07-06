#!/usr/bin/env python3
"""
Test script for fallback PDF extraction and vector store functionality.
Tests both AWS Textract and PyPDF2 fallback mechanisms.
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

async def test_fallback_pdf_extraction():
    """Test the fallback PDF extraction mechanism."""
    try:
        from src.services.aws_textract_service import textract_service, DocumentType
        from src.core.exceptions import DocumentProcessingError
        
        logger.info("🧪 Testing Fallback PDF Extraction")
        logger.info("=" * 50)
        
        # Test with a sample PDF (you can replace this with your actual PDF)
        test_pdf_path = "data/uploads/Namecheap.pdf"  # Adjust path as needed
        
        if not os.path.exists(test_pdf_path):
            logger.warning(f"Test PDF not found: {test_pdf_path}")
            logger.info("Creating a simple test PDF for demonstration...")
            
            # Create a simple test PDF for demonstration
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(100, 750, "Test PDF Document")
            p.drawString(100, 700, "This is a test document for fallback extraction.")
            p.drawString(100, 650, "It should be processed by PyPDF2 if Textract fails.")
            p.save()
            
            file_content = buffer.getvalue()
            filename = "test_document.pdf"
        else:
            # Read existing PDF
            with open(test_pdf_path, "rb") as f:
                file_content = f.read()
            filename = os.path.basename(test_pdf_path)
        
        logger.info(f"📄 Testing with file: {filename} ({len(file_content)} bytes)")
        
        # Test the upload_to_s3_and_extract method
        try:
            text_content, page_count = await textract_service.upload_to_s3_and_extract(
                file_content=file_content,
                filename=filename,
                document_type=DocumentType.GENERAL,
                user_id="test_user"
            )
            
            logger.info(f"✅ Extraction successful!")
            logger.info(f"📊 Pages: {page_count}")
            logger.info(f"📝 Text length: {len(text_content)} characters")
            logger.info(f"📄 First 200 chars: {text_content[:200]}...")
            
            return True
            
        except DocumentProcessingError as e:
            logger.error(f"❌ Extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def test_vector_store_functionality():
    """Test the vector store functionality."""
    try:
        from src.services.vector_store_service import VectorStoreService
        
        logger.info("\n🧪 Testing Vector Store Functionality")
        logger.info("=" * 50)
        
        # Initialize vector store service
        vector_store_service = VectorStoreService()
        
        # Test creating/getting vector store
        logger.info("📦 Testing vector store creation...")
        vector_store_id = await vector_store_service.get_or_create_vector_store("Test Store")
        logger.info(f"✅ Vector store ID: {vector_store_id}")
        
        # Test uploading text content
        logger.info("📤 Testing text upload...")
        test_text = """
        This is a test document about artificial intelligence and machine learning.
        AI has become increasingly important in modern technology.
        Machine learning algorithms can process large amounts of data efficiently.
        """
        
        file_id = await vector_store_service.upload_text_to_vector_store(
            text=test_text,
            filename="test_ai_document.txt",
            vector_store_id=vector_store_id
        )
        logger.info(f"✅ File uploaded with ID: {file_id}")
        
        # Test searching
        logger.info("🔍 Testing search functionality...")
        search_results = await vector_store_service.search_vector_store(
            query="artificial intelligence",
            vector_store_id=vector_store_id,
            max_results=5
        )
        
        logger.info(f"✅ Search completed!")
        logger.info(f"📊 Found {len(search_results.get('results', []))} results")
        
        if search_results.get('results'):
            first_result = search_results['results'][0]
            logger.info(f"📄 First result: {first_result.get('content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector store test failed: {e}")
        return False

async def test_openai_version():
    """Test OpenAI version compatibility."""
    try:
        logger.info("\n🧪 Testing OpenAI Version Compatibility")
        logger.info("=" * 50)
        
        import openai
        logger.info(f"📦 OpenAI version: {openai.__version__}")
        
        # Test if vector_stores attribute exists
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'test'))
        
        if hasattr(client, 'vector_stores'):
            logger.info("✅ OpenAI client has vector_stores attribute")
            return True
        else:
            logger.warning("⚠️ OpenAI client does not have vector_stores attribute")
            return False
            
    except Exception as e:
        logger.error(f"❌ OpenAI version test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Local Tests")
    logger.info("=" * 60)
    
    # Check environment
    logger.info("🔧 Environment Check:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")
    logger.info(f"   OPENAI_API_KEY set: {'Yes' if os.environ.get('OPENAI_API_KEY') else 'No'}")
    logger.info(f"   AWS credentials: {'Available' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}")
    
    results = {}
    
    # Test OpenAI version
    results['openai_version'] = await test_openai_version()
    
    # Test vector store functionality
    results['vector_store'] = await test_vector_store_functionality()
    
    # Test fallback PDF extraction
    results['fallback_extraction'] = await test_fallback_pdf_extraction()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Your local setup is working correctly.")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 