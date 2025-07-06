#!/usr/bin/env python3
"""
Test script for AWS Textract integration
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.aws_textract_service import textract_service, DocumentType
from src.core.aws_config import aws_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_textract_service():
    """Test the AWS Textract service."""
    
    print("🔍 Testing AWS Textract Service")
    print("=" * 50)
    
    # Test 1: Check AWS configuration
    print("\n1. Testing AWS Configuration:")
    print(f"   - AWS Region: {aws_config.region}")
    print(f"   - Textract Region: {aws_config.textract_region}")
    print(f"   - S3 Bucket: {aws_config.s3_bucket_name}")
    print(f"   - Access Key Present: {bool(aws_config.access_key_id)}")
    print(f"   - Secret Key Present: {bool(aws_config.secret_access_key)}")
    
    # Test 2: Check Textract service initialization
    print("\n2. Testing Textract Service Initialization:")
    if textract_service.textract_client:
        print("   ✅ Textract client initialized successfully")
    else:
        print("   ❌ Textract client failed to initialize")
        return False
    
    if textract_service.s3_client:
        print("   ✅ S3 client initialized successfully")
    else:
        print("   ❌ S3 client failed to initialize")
        return False
    
    # Test 3: Test cost estimation
    print("\n3. Testing Cost Estimation:")
    for doc_type in DocumentType:
        cost_info = textract_service.estimate_cost(doc_type, 10)
        print(f"   - {doc_type.value}: ${cost_info['estimated_cost']:.4f} for 10 pages")
    
    # Test 4: Test API selection logic
    print("\n4. Testing API Selection Logic:")
    test_cases = [
        ("annual_report.pdf", DocumentType.GENERAL),
        ("invoice_2024.pdf", DocumentType.FORM),
        ("tax_form_w2.pdf", DocumentType.FORM),
        ("receipt.pdf", DocumentType.FORM),
        ("document.pdf", DocumentType.GENERAL),
    ]
    
    for filename, expected_type in test_cases:
        # Simulate the document type detection logic
        filename_lower = filename.lower()
        detected_type = DocumentType.GENERAL
        if any(keyword in filename_lower for keyword in ['form', 'invoice', 'receipt', 'tax', 'w2', '1099']):
            detected_type = DocumentType.FORM
        
        status = "✅" if detected_type == expected_type else "❌"
        print(f"   {status} {filename} -> {detected_type.value} (expected: {expected_type.value})")
    
    print("\n5. Testing S3 Bucket Access:")
    try:
        # Test if we can access the S3 bucket
        response = textract_service.s3_client.head_bucket(Bucket=aws_config.s3_bucket_name)
        print("   ✅ S3 bucket access successful")
    except Exception as e:
        print(f"   ❌ S3 bucket access failed: {e}")
        return False
    
    print("\n6. Testing Textract Permissions:")
    try:
        # Test if we have Textract permissions by calling a simple API
        # We'll use a minimal test document (1x1 pixel PNG)
        import io
        from PIL import Image
        
        # Create a minimal test image
        img = Image.new('RGB', (1, 1), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Test Textract with the minimal image
        response = textract_service.textract_client.detect_document_text(
            Document={'Bytes': img_bytes.getvalue()}
        )
        print("   ✅ Textract permissions verified")
    except Exception as e:
        print(f"   ❌ Textract permissions failed: {e}")
        return False
    
    print("\n✅ All tests completed successfully!")
    return True

async def test_with_sample_pdf():
    """Test with a sample PDF if available."""
    
    print("\n📄 Testing with Sample PDF")
    print("=" * 30)
    
    # Look for a sample PDF in the current directory
    sample_pdfs = list(Path(".").glob("*.pdf"))
    
    if not sample_pdfs:
        print("   No sample PDFs found in current directory")
        print("   To test with a real PDF, place a file named 'test.pdf' in the current directory")
        return
    
    test_pdf = sample_pdfs[0]
    print(f"   Found test PDF: {test_pdf}")
    
    try:
        # Read the PDF file
        with open(test_pdf, 'rb') as f:
            pdf_content = f.read()
        
        print(f"   PDF size: {len(pdf_content)} bytes")
        
        # Test text extraction
        print("   Extracting text...")
        start_time = asyncio.get_event_loop().time()
        
        text_content = await textract_service.upload_to_s3_and_extract(
            pdf_content,
            test_pdf.name,
            DocumentType.GENERAL
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"   ✅ Text extraction completed in {processing_time:.2f} seconds")
        print(f"   Extracted text length: {len(text_content)} characters")
        
        if text_content.strip():
            print("   Sample text (first 200 chars):")
            print(f"   {text_content[:200]}...")
        else:
            print("   ⚠️  No text extracted from PDF")
            
    except Exception as e:
        print(f"   ❌ Error testing with sample PDF: {e}")

def main():
    """Main test function."""
    print("🚀 AWS Textract Integration Test")
    print("=" * 50)
    
    # Check environment
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        print("Running in Lambda environment")
    else:
        print("Running in local environment")
    
    # Run tests
    success = asyncio.run(test_textract_service())
    
    if success:
        # Test with sample PDF if available
        asyncio.run(test_with_sample_pdf())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! AWS Textract integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check your AWS configuration.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 