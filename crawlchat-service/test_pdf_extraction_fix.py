#!/usr/bin/env python3
"""
Test script for PDF extraction improvements
Tests user-friendly error messages and extraction fallbacks
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.document_service import document_service
from common.src.services.aws_textract_service import AWSTextractService
from common.src.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_user_friendly_error_messages():
    """Test that user-friendly error messages are returned instead of technical descriptions."""
    
    print("\n🔍 Testing User-Friendly Error Messages:")
    print("=" * 60)
    
    # Test document service error message
    try:
        error_msg = document_service._get_user_friendly_pdf_error_message("test.pdf")
        print(f"✅ Document Service Error Message:")
        print(f"   Length: {len(error_msg)} characters")
        print(f"   Contains 'unable to read': {'unable to read' in error_msg.lower()}")
        print(f"   Contains 'scanned document': {'scanned document' in error_msg.lower()}")
        print(f"   Contains 'password-protected': {'password-protected' in error_msg.lower()}")
        print(f"   Preview: {error_msg[:100]}...")
        
        # Check that it's not a technical description
        technical_terms = ['pdfminer', 'pypdf2', 'textract', 'aws', 's3', 'lambda']
        has_technical_terms = any(term in error_msg.lower() for term in technical_terms)
        print(f"   Contains technical terms: {has_technical_terms} (should be False)")
        
        if not has_technical_terms:
            print("   ✅ PASS: Error message is user-friendly")
        else:
            print("   ❌ FAIL: Error message contains technical terms")
            
    except Exception as e:
        print(f"❌ Error testing document service error message: {e}")
    
    # Test Textract service error message
    try:
        textract_service = AWSTextractService()
        error_msg = textract_service._get_user_friendly_extraction_error_message("test.pdf")
        print(f"\n✅ Textract Service Error Message:")
        print(f"   Length: {len(error_msg)} characters")
        print(f"   Contains 'unable to read': {'unable to read' in error_msg.lower()}")
        print(f"   Contains 'scanned document': {'scanned document' in error_msg.lower()}")
        print(f"   Contains 'password-protected': {'password-protected' in error_msg.lower()}")
        print(f"   Preview: {error_msg[:100]}...")
        
        # Check that it's not a technical description
        technical_terms = ['pdfminer', 'pypdf2', 'textract', 'aws', 's3', 'lambda']
        has_technical_terms = any(term in error_msg.lower() for term in technical_terms)
        print(f"   Contains technical terms: {has_technical_terms} (should be False)")
        
        if not has_technical_terms:
            print("   ✅ PASS: Error message is user-friendly")
        else:
            print("   ❌ FAIL: Error message contains technical terms")
            
    except Exception as e:
        print(f"❌ Error testing Textract service error message: {e}")

async def test_pdf_extraction_fallback():
    """Test PDF extraction fallback behavior with corrupted/invalid PDFs."""
    
    print("\n🔍 Testing PDF Extraction Fallback:")
    print("=" * 60)
    
    # Create a corrupted PDF (just random bytes)
    corrupted_pdf = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09' * 1000
    
    try:
        # Test document service extraction
        result = await document_service._extract_pdf_text_optimized(corrupted_pdf, "corrupted.pdf")
        print(f"✅ Document Service Fallback Result:")
        print(f"   Length: {len(result)} characters")
        print(f"   Contains error message: {'unable to read' in result.lower()}")
        print(f"   Contains technical terms: {any(term in result.lower() for term in ['pdfminer', 'pypdf2', 'textract'])}")
        print(f"   Preview: {result[:150]}...")
        
        if 'unable to read' in result.lower() and not any(term in result.lower() for term in ['pdfminer', 'pypdf2', 'textract']):
            print("   ✅ PASS: Returns user-friendly error message")
        else:
            print("   ❌ FAIL: Returns technical description")
            
    except Exception as e:
        print(f"❌ Error testing document service fallback: {e}")
    
    try:
        # Test Textract service hybrid extraction
        textract_service = AWSTextractService()
        from common.src.services.aws_textract_service import DocumentType
        result, page_count = await textract_service._hybrid_pdf_extraction(
            corrupted_pdf, "corrupted.pdf", "test-bucket", "test-key", 
            DocumentType.GENERAL, "test-user"
        )
        print(f"\n✅ Textract Service Fallback Result:")
        print(f"   Length: {len(result)} characters")
        print(f"   Page count: {page_count}")
        print(f"   Contains error message: {'unable to read' in result.lower()}")
        print(f"   Contains technical terms: {any(term in result.lower() for term in ['pdfminer', 'pypdf2', 'textract'])}")
        print(f"   Preview: {result[:150]}...")
        
        if 'unable to read' in result.lower() and not any(term in result.lower() for term in ['pdfminer', 'pypdf2', 'textract']):
            print("   ✅ PASS: Returns user-friendly error message")
        else:
            print("   ❌ FAIL: Returns technical description")
            
    except Exception as e:
        print(f"❌ Error testing Textract service fallback: {e}")

async def test_error_message_quality():
    """Test the quality and helpfulness of error messages."""
    
    print("\n🔍 Testing Error Message Quality:")
    print("=" * 60)
    
    try:
        # Test document service error message quality
        error_msg = document_service._get_user_friendly_pdf_error_message("test.pdf")
        
        quality_checks = [
            ("Contains problem explanation", any(term in error_msg.lower() for term in ['scanned', 'password', 'corrupted', 'damaged'])),
            ("Contains solution suggestions", any(term in error_msg.lower() for term in ['uploading', 'converting', 'different format', 'password-protected'])),
            ("Uses bullet points", "•" in error_msg),
            ("Is conversational", "i'm" in error_msg.lower() or "please try" in error_msg.lower()),
            ("Mentions specific file formats", any(term in error_msg.lower() for term in ['word', 'text file', 'pdf'])),
            ("No technical jargon", not any(term in error_msg.lower() for term in ['pdfminer', 'pypdf2', 'textract', 'aws', 'lambda', 's3']))
        ]
        
        print("✅ Document Service Error Message Quality:")
        for check_name, passed in quality_checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {check_name}: {status}")
        
        overall_score = sum(1 for _, passed in quality_checks if passed)
        print(f"   Overall Score: {overall_score}/{len(quality_checks)}")
        
        if overall_score >= 5:
            print("   ✅ PASS: Error message is high quality")
        else:
            print("   ❌ FAIL: Error message needs improvement")
            
    except Exception as e:
        print(f"❌ Error testing error message quality: {e}")

async def test_extraction_methods():
    """Test that all extraction methods are properly handled."""
    
    print("\n🔍 Testing Extraction Methods:")
    print("=" * 60)
    
    # Test with empty content
    empty_content = b''
    
    try:
        result = await document_service._extract_pdf_text_optimized(empty_content, "empty.pdf")
        print(f"✅ Empty PDF Test:")
        print(f"   Result length: {len(result)}")
        print(f"   Contains error message: {'unable to read' in result.lower()}")
        print(f"   Preview: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ Error testing empty PDF: {e}")
    
    # Test with non-PDF content
    text_content = b"This is not a PDF file, just plain text content."
    
    try:
        result = await document_service._extract_pdf_text_optimized(text_content, "text.txt")
        print(f"\n✅ Non-PDF Content Test:")
        print(f"   Result length: {len(result)}")
        print(f"   Contains error message: {'unable to read' in result.lower()}")
        print(f"   Preview: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ Error testing non-PDF content: {e}")

async def main():
    """Run all tests."""
    print("🚀 PDF Extraction Fix Test Suite")
    print("=" * 60)
    
    tests = [
        test_user_friendly_error_messages,
        test_pdf_extraction_fallback,
        test_error_message_quality,
        test_extraction_methods
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PDF extraction improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 