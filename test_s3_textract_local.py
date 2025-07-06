#!/usr/bin/env python3
"""
Local test script to verify S3 object availability and Textract access.
Run this locally to debug the S3 object availability issue.
"""

import asyncio
import boto3
import os
import sys
import time
from botocore.exceptions import ClientError

# Add the src directory to the path
sys.path.append('src')

from src.core.aws_config import aws_config
from src.services.aws_textract_service import textract_service

async def test_s3_object_availability():
    """Test S3 object availability and Textract access."""
    
    print("🔍 Testing S3 Object Availability and Textract Access")
    print("=" * 60)
    
    # Test S3 bucket access
    print("\n1. Testing S3 Bucket Access:")
    print("-" * 30)
    
    try:
        s3_client = boto3.client('s3', 
                                region_name=aws_config.region,
                                aws_access_key_id=aws_config.access_key_id,
                                aws_secret_access_key=aws_config.secret_access_key)
        
        bucket_name = aws_config.s3_bucket_name
        print(f"✅ S3 Client created successfully")
        print(f"📦 Bucket: {bucket_name}")
        print(f"🌍 Region: {aws_config.region}")
        
        # Test bucket access
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket {bucket_name} is accessible")
        
        # List objects in bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        print(f"✅ S3 bucket listing successful, found {len(response.get('Contents', []))} objects")
        
    except Exception as e:
        print(f"❌ S3 bucket access failed: {e}")
        return False
    
    # Test specific S3 object
    print("\n2. Testing Specific S3 Object:")
    print("-" * 30)
    
    # Use the same path structure as the failing request
    test_s3_key = "crawled_documents/textract_processing/7320c5a4-8865-468c-a851-5edc3ad445e2/f303a23b-5a68-4af2-ab1b-fb9213b0147c/Namecheap.pdf"
    
    print(f"🔍 Testing S3 object: s3://{bucket_name}/{test_s3_key}")
    
    try:
        # Check if object exists
        head_response = s3_client.head_object(Bucket=bucket_name, Key=test_s3_key)
        print(f"✅ S3 object exists!")
        print(f"   📏 Size: {head_response.get('ContentLength', 'unknown')} bytes")
        print(f"   🏷️  ETag: {head_response.get('ETag', 'unknown')}")
        print(f"   📅 LastModified: {head_response.get('LastModified', 'unknown')}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchKey':
            print(f"❌ S3 object not found (404/NoSuchKey)")
        else:
            print(f"❌ S3 error: {error_code} - {e.response['Error'].get('Message', '')}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking S3 object: {e}")
        return False
    
    # Test Textract client
    print("\n3. Testing Textract Client:")
    print("-" * 30)
    
    try:
        textract_client = boto3.client('textract', 
                                      region_name=aws_config.textract_region,
                                      aws_access_key_id=aws_config.access_key_id,
                                      aws_secret_access_key=aws_config.secret_access_key)
        
        print(f"✅ Textract Client created successfully")
        print(f"🌍 Textract Region: {aws_config.textract_region}")
        
        # Test Textract access by calling a simple API
        # We'll just test the client creation, not actually call Textract
        print(f"✅ Textract client is ready")
        
    except Exception as e:
        print(f"❌ Textract client creation failed: {e}")
        return False
    
    # Test the actual Textract service
    print("\n4. Testing Textract Service:")
    print("-" * 30)
    
    try:
        # Initialize the Textract service
        textract_service._init_clients()
        print(f"✅ Textract service initialized successfully")
        
        # Test S3 object availability check
        print(f"🔍 Testing S3 object availability check...")
        is_available = await textract_service._wait_for_s3_object(bucket_name, test_s3_key, max_wait=10)
        
        if is_available:
            print(f"✅ S3 object availability check passed")
        else:
            print(f"❌ S3 object availability check failed")
            return False
            
    except Exception as e:
        print(f"❌ Textract service test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! S3 object is available and Textract is ready.")
    print("=" * 60)
    
    return True

async def test_textract_extraction():
    """Test actual Textract extraction."""
    
    print("\n🔍 Testing Textract Extraction:")
    print("=" * 60)
    
    try:
        # Initialize the Textract service
        textract_service._init_clients()
        
        bucket_name = aws_config.s3_bucket_name
        test_s3_key = "crawled_documents/textract_processing/7320c5a4-8865-468c-a851-5edc3ad445e2/f303a23b-5a68-4af2-ab1b-fb9213b0147c/Namecheap.pdf"
        
        print(f"🔍 Testing Textract extraction for: s3://{bucket_name}/{test_s3_key}")
        
        # Test DetectDocumentText
        text_content, page_count = await textract_service._detect_document_text(bucket_name, test_s3_key)
        
        print(f"✅ Textract extraction successful!")
        print(f"   📄 Pages: {page_count}")
        print(f"   📝 Characters: {len(text_content)}")
        print(f"   📖 Preview: {text_content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Textract extraction failed: {e}")
        return False

async def test_with_local_pdf():
    """Test Textract with a local PDF file."""
    
    print("\n🔍 Testing Textract with Local PDF:")
    print("=" * 60)
    
    try:
        # Initialize the Textract service
        textract_service._init_clients()
        
        # Check if Namecheap.pdf exists locally
        local_pdf_path = "Namecheap.pdf"
        if not os.path.exists(local_pdf_path):
            print(f"❌ Local PDF file not found: {local_pdf_path}")
            return False
        
        print(f"📄 Found local PDF: {local_pdf_path}")
        
        # Read the local PDF file
        with open(local_pdf_path, 'rb') as f:
            file_content = f.read()
        
        print(f"📏 File size: {len(file_content)} bytes")
        
        # Test upload and extraction
        text_content, page_count = await textract_service.upload_to_s3_and_extract(
            file_content=file_content,
            filename="test_local.pdf",
            user_id="test_user"
        )
        
        print(f"✅ Textract extraction successful!")
        print(f"   📄 Pages: {page_count}")
        print(f"   📝 Characters: {len(text_content)}")
        print(f"   📖 Preview: {text_content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Textract extraction failed: {e}")
        return False

async def main():
    """Main test function."""
    
    print("🚀 Starting Local S3 and Textract Tests")
    print("=" * 60)
    
    # Test 1: S3 Object Availability
    s3_test_passed = await test_s3_object_availability()
    
    if not s3_test_passed:
        print("\n❌ S3 Object Availability Test Failed")
        return
    
    # Test 2: Textract Extraction (only if S3 test passed)
    print("\n" + "=" * 60)
    textract_test_passed = await test_textract_extraction()
    
    if textract_test_passed:
        print("\n🎉 All Tests Passed! The issue might be in the Lambda environment.")
    else:
        print("\n❌ Textract Extraction Test Failed")
        print("Testing with local PDF file...")
        
        # Test 3: Try with local PDF
        print("\n" + "=" * 60)
        local_test_passed = await test_with_local_pdf()
        
        if local_test_passed:
            print("\n🎉 Local PDF Test Passed! The S3 object might be corrupted.")
        else:
            print("\n❌ Local PDF Test Also Failed")
            print("This suggests the PDF file itself might be corrupted or encrypted.")

if __name__ == "__main__":
    asyncio.run(main()) 