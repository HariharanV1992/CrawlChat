#!/usr/bin/env python3
"""
Test script to verify file integrity before and after S3 upload.
This will help identify if files are getting corrupted during the upload process.
"""

import asyncio
import hashlib
import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.src.core.config import config
from common.src.services.aws_textract_service import textract_service

async def test_file_integrity():
    """Test file integrity before and after S3 upload."""
    
    # Test with a sample PDF file
    test_file_path = "Namecheap.pdf"  # Use the file that's causing issues
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file {test_file_path} not found!")
        return
    
    print(f"🔍 Testing file integrity for: {test_file_path}")
    
    # Read original file
    with open(test_file_path, 'rb') as f:
        original_content = f.read()
    
    original_hash = hashlib.md5(original_content).hexdigest()
    original_size = len(original_content)
    
    print(f"📄 Original file:")
    print(f"   Size: {original_size:,} bytes")
    print(f"   MD5: {original_hash}")
    
    # Check if it's a valid PDF
    if original_content.startswith(b'%PDF'):
        print("   ✅ Valid PDF header detected")
    else:
        print("   ❌ Invalid PDF header")
    
    # Upload to S3 and download back
    try:
        print(f"\n📤 Uploading to S3...")
        
        # Upload using our service
        text_content, page_count = await textract_service.upload_to_s3_and_extract(
            original_content,
            os.path.basename(test_file_path),
            user_id="test_user"
        )
        
        print(f"✅ Upload successful")
        print(f"   Extracted text length: {len(text_content)} characters")
        print(f"   Page count: {page_count}")
        
        # Download the file back from S3 to compare
        print(f"\n📥 Downloading from S3 for comparison...")
        
        # Get the S3 key that was used
        import uuid
        file_id = str(uuid.uuid4())  # This won't match exactly, but let's try to find the file
        s3_key = f"uploaded_documents/test_user/{file_id}/{os.path.basename(test_file_path)}"
        
        # List objects to find the actual key
        s3_client = textract_service.s3_client
        response = s3_client.list_objects_v2(
            Bucket=config.s3_bucket,
            Prefix="uploaded_documents/test_user/"
        )
        
        if 'Contents' in response:
            # Get the most recent file
            latest_key = max(response['Contents'], key=lambda x: x['LastModified'])['Key']
            print(f"   Found S3 key: {latest_key}")
            
            # Download the file
            download_response = s3_client.get_object(
                Bucket=config.s3_bucket,
                Key=latest_key
            )
            downloaded_content = download_response['Body'].read()
            
            downloaded_hash = hashlib.md5(downloaded_content).hexdigest()
            downloaded_size = len(downloaded_content)
            
            print(f"\n📄 Downloaded file:")
            print(f"   Size: {downloaded_size:,} bytes")
            print(f"   MD5: {downloaded_hash}")
            
            if downloaded_content.startswith(b'%PDF'):
                print("   ✅ Valid PDF header detected")
            else:
                print("   ❌ Invalid PDF header")
            
            # Compare
            if original_hash == downloaded_hash:
                print(f"\n✅ File integrity maintained!")
                print(f"   Original and downloaded files are identical")
            else:
                print(f"\n❌ File corruption detected!")
                print(f"   Original hash: {original_hash}")
                print(f"   Downloaded hash: {downloaded_hash}")
                print(f"   Size difference: {original_size - downloaded_size} bytes")
                
                # Show first few bytes for comparison
                print(f"\n🔍 First 50 bytes comparison:")
                print(f"   Original: {original_content[:50]}")
                print(f"   Downloaded: {downloaded_content[:50]}")
        else:
            print("❌ No files found in S3")
            
    except Exception as e:
        print(f"❌ Error during upload/download test: {e}")
        import traceback
        traceback.print_exc()

async def test_direct_s3_upload():
    """Test direct S3 upload without using our service."""
    
    test_file_path = "Namecheap.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file {test_file_path} not found!")
        return
    
    print(f"\n🔍 Testing direct S3 upload for: {test_file_path}")
    
    # Read original file
    with open(test_file_path, 'rb') as f:
        original_content = f.read()
    
    original_hash = hashlib.md5(original_content).hexdigest()
    
    try:
        import uuid
        s3_client = textract_service.s3_client
        bucket_name = config.s3_bucket
        test_key = f"test_integrity/{uuid.uuid4()}/{os.path.basename(test_file_path)}"
        
        print(f"📤 Direct upload to s3://{bucket_name}/{test_key}")
        
        # Upload with explicit content type
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=original_content,
            ContentType='application/pdf'
        )
        
        print(f"✅ Direct upload successful")
        
        # Download immediately
        download_response = s3_client.get_object(
            Bucket=bucket_name,
            Key=test_key
        )
        downloaded_content = download_response['Body'].read()
        
        downloaded_hash = hashlib.md5(downloaded_content).hexdigest()
        
        if original_hash == downloaded_hash:
            print(f"✅ Direct upload integrity maintained!")
        else:
            print(f"❌ Direct upload corruption detected!")
            print(f"   Original hash: {original_hash}")
            print(f"   Downloaded hash: {downloaded_hash}")
        
        # Clean up
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"🧹 Cleaned up test file")
        
    except Exception as e:
        print(f"❌ Error during direct upload test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 File Integrity Test")
    print("=" * 50)
    
    asyncio.run(test_file_integrity())
    asyncio.run(test_direct_s3_upload())
    
    print("\n" + "=" * 50)
    print("�� Test completed") 