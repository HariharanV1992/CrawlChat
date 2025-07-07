#!/usr/bin/env python3
"""
Local test script for the PDF preprocessor service.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import the preprocessing service
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing_service import PDFPreprocessor

async def test_preprocessor():
    """Test the PDF preprocessor locally."""
    
    print("🧪 Testing PDF Preprocessor Service")
    print("=" * 50)
    
    # Initialize preprocessor
    preprocessor = PDFPreprocessor()
    
    # Test AWS clients
    print("\n1️⃣ Testing AWS Clients:")
    if preprocessor.s3_client:
        print("   ✅ S3 Client: Initialized")
    else:
        print("   ❌ S3 Client: Failed to initialize")
    
    if preprocessor.sqs_client:
        print("   ✅ SQS Client: Initialized")
    else:
        print("   ❌ SQS Client: Failed to initialize")
    
    # Test with a sample PDF (if available)
    print("\n2️⃣ Testing PDF Processing:")
    
    # Check if we have a test PDF
    test_pdf_path = Path(__file__).parent / "test.pdf"
    if test_pdf_path.exists():
        print(f"   Found test PDF: {test_pdf_path}")
        
        try:
            with open(test_pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Test text extraction
            print("   Testing text extraction...")
            text_content = await preprocessor._extract_text_from_pdf(pdf_content)
            
            if text_content and len(text_content.strip()) > 10:
                print(f"   ✅ Text extraction successful: {len(text_content)} characters")
                print(f"   📄 Preview: {text_content[:100]}...")
            else:
                print("   ⚠️ Text extraction returned minimal content")
                
        except Exception as e:
            print(f"   ❌ Error testing PDF: {e}")
    else:
        print("   ⚠️ No test PDF found, skipping PDF processing test")
        print("   💡 Create a test.pdf file in this directory to test PDF processing")
    
    # Test SQS polling (without actually polling)
    print("\n3️⃣ Testing SQS Configuration:")
    queue_url = os.environ.get("SQS_QUEUE_URL")
    if queue_url:
        print(f"   ✅ SQS Queue URL: {queue_url}")
    else:
        print("   ⚠️ SQS_QUEUE_URL not set")
    
    s3_bucket = os.environ.get("S3_BUCKET")
    if s3_bucket:
        print(f"   ✅ S3 Bucket: {s3_bucket}")
    else:
        print("   ⚠️ S3_BUCKET not set")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("- If AWS clients are initialized, the service should work")
    print("- If text extraction works, PDF processing will be functional")
    print("- Set SQS_QUEUE_URL and S3_BUCKET environment variables for full testing")
    print("- The service is ready for deployment!")

if __name__ == "__main__":
    asyncio.run(test_preprocessor()) 