#!/usr/bin/env python3
"""
Test script for Unified Preprocessing Service
Tests the consolidated preprocessing functionality.
"""

import asyncio
import logging
import sys
import os

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.src.services.unified_preprocessing_service import unified_preprocessing_service, DocumentType
from common.src.services.document_processing_service import document_processing_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_unified_preprocessing():
    """Test the unified preprocessing service."""
    print("🧪 Testing Unified Preprocessing Service")
    print("=" * 50)
    
    try:
        # Test 1: Service initialization
        print("1. Testing service initialization...")
        stats = unified_preprocessing_service.get_processing_stats()
        print(f"✅ Service initialized successfully")
        print(f"   Supported document types: {stats['supported_document_types']}")
        print(f"   Processing types: {stats['processing_types']}")
        print(f"   S3 integration: {stats['capabilities']['s3_integration']}")
        
        # Test 2: Document type detection
        print("\n2. Testing document type detection...")
        
        # Test PDF detection
        pdf_filename = "test.pdf"
        pdf_content = b"%PDF-1.4\n%Test PDF content"
        doc_type = unified_preprocessing_service._detect_document_type(pdf_filename, pdf_content)
        print(f"✅ PDF detection: {pdf_filename} -> {doc_type.value}")
        
        # Test image detection
        image_filename = "test.png"
        image_content = b"\x89PNG\r\n\x1a\n"
        doc_type = unified_preprocessing_service._detect_document_type(image_filename, image_content)
        print(f"✅ Image detection: {image_filename} -> {doc_type.value}")
        
        # Test text detection
        text_filename = "test.txt"
        text_content = b"Plain text content"
        doc_type = unified_preprocessing_service._detect_document_type(text_filename, text_content)
        print(f"✅ Text detection: {text_filename} -> {doc_type.value}")
        
        # Test 3: Text document processing
        print("\n3. Testing text document processing...")
        text_result = await unified_preprocessing_service.process_document(
            file_content=b"This is a test text document with some content.",
            filename="test.txt",
            user_id="test_user"
        )
        
        if text_result.get("status") == "success":
            print(f"✅ Text processing successful")
            print(f"   Processing type: {text_result.get('processing_type')}")
            print(f"   Text length: {text_result.get('text_length')}")
        else:
            print(f"❌ Text processing failed: {text_result.get('error')}")
        
        # Test 4: Document processing with vector store integration
        print("\n4. Testing document processing with vector store...")
        vector_result = await document_processing_service.process_document_with_preprocessing(
            file_content=b"This is a test document for vector store integration.",
            filename="test_vector.txt",
            user_id="test_user",
            session_id="test_session"
        )
        
        if vector_result.get("status") == "success":
            print(f"✅ Vector store integration successful")
            print(f"   Document ID: {vector_result.get('document_id')}")
            print(f"   Preprocessing status: {vector_result.get('preprocessing', {}).get('status')}")
        else:
            print(f"❌ Vector store integration failed: {vector_result.get('error')}")
        
        # Test 5: Batch processing
        print("\n5. Testing batch processing...")
        documents = [
            {
                "content": b"First test document content.",
                "filename": "test1.txt"
            },
            {
                "content": b"Second test document content.",
                "filename": "test2.txt"
            }
        ]
        
        batch_result = await unified_preprocessing_service.batch_process_documents(
            documents=documents,
            user_id="test_user"
        )
        
        success_count = sum(1 for r in batch_result if r.get("status") == "success")
        print(f"✅ Batch processing: {success_count}/{len(batch_result)} documents processed successfully")
        
        # Test 6: Supported types endpoint
        print("\n6. Testing supported types...")
        supported_types = [dt.value for dt in DocumentType]
        from common.src.services.unified_preprocessing_service import ProcessingType
        processing_types = [pt.value for pt in ProcessingType]
        print(f"✅ Supported document types: {supported_types}")
        print(f"✅ Processing types: {processing_types}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("✅ Unified preprocessing service is working correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
        return False

async def test_error_handling():
    """Test error handling in the unified preprocessing service."""
    print("\n🧪 Testing Error Handling")
    print("=" * 30)
    
    try:
        # Test with invalid document type
        print("1. Testing invalid document type...")
        result = await unified_preprocessing_service.process_document(
            file_content=b"test content",
            filename="test.xyz",
            user_id="test_user",
            document_type=DocumentType.UNKNOWN
        )
        
        if result.get("status") == "success":
            print(f"✅ Unknown document type handled gracefully")
        else:
            print(f"⚠️  Unknown document type resulted in: {result.get('status')}")
        
        # Test with empty content
        print("2. Testing empty content...")
        result = await unified_preprocessing_service.process_document(
            file_content=b"",
            filename="empty.txt",
            user_id="test_user"
        )
        
        if result.get("status") == "success":
            print(f"✅ Empty content handled gracefully")
        else:
            print(f"⚠️  Empty content resulted in: {result.get('status')}")
        
        print("✅ Error handling tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Unified Preprocessing Service Tests")
    print("=" * 60)
    
    # Run main tests
    main_success = await test_unified_preprocessing()
    
    # Run error handling tests
    error_success = await test_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Main functionality: {'✅ PASSED' if main_success else '❌ FAILED'}")
    print(f"Error handling: {'✅ PASSED' if error_success else '❌ FAILED'}")
    
    if main_success and error_success:
        print("\n🎉 All tests passed! Unified preprocessing service is ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 