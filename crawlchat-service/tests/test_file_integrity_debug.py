#!/usr/bin/env python3
"""
Test script to verify file integrity logging and debug upload issues.
This will help identify where file corruption occurs in the upload pipeline.
"""

import asyncio
import os
import sys
import logging
import hashlib

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see all the file integrity messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from common.src.services.aws_textract_service import textract_service

async def test_file_integrity_debug():
    """Test file integrity logging with a sample PDF."""
    
    # Test with a sample PDF file
    test_file_path = "Namecheap.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file {test_file_path} not found!")
        return
    
    print(f"🔍 Testing file integrity debugging with: {test_file_path}")
    print("=" * 80)
    
    # Read the file
    with open(test_file_path, 'rb') as f:
        file_content = f.read()
    
    # Log original file details
    print(f"📄 ORIGINAL FILE DETAILS:")
    print(f"   📏 Size: {len(file_content):,} bytes")
    print(f"   🔢 MD5: {hashlib.md5(file_content).hexdigest()}")
    print(f"   📄 First 20 bytes: {file_content[:20]}")
    print(f"   📄 Last 20 bytes: {file_content[-20:]}")
    
    if file_content.startswith(b'%PDF-'):
        print(f"   ✅ Valid PDF header")
    else:
        print(f"   ❌ Invalid PDF header: {file_content[:10]}")
    
    if b'%%EOF' in file_content[-1000:]:
        print(f"   ✅ PDF EOF marker found")
    else:
        print(f"   ❌ PDF EOF marker missing")
    
    print("\n" + "=" * 80)
    print("🚀 Testing upload and extraction with integrity logging...")
    print("=" * 80)
    
    try:
        # Test the improved extraction with detailed integrity logging
        text_content, page_count = await textract_service.upload_to_s3_and_extract(
            file_content,
            os.path.basename(test_file_path),
            user_id="test_integrity_debug"
        )
        
        print("\n" + "=" * 80)
        print(f"🏁 FINAL RESULT:")
        print(f"   Text length: {len(text_content)} characters")
        print(f"   Page count: {page_count}")
        print(f"   Success: {'✅' if len(text_content.strip()) > 50 else '❌'}")
        
        if len(text_content.strip()) > 50:
            print(f"   Preview: {text_content[:200]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_files():
    """Test multiple files to see if the issue is file-specific."""
    
    test_files = [
        "Namecheap.pdf",
        # Add other PDF files here if available
    ]
    
    print(f"🧪 Testing multiple files for integrity issues...")
    print("=" * 80)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📄 Testing: {test_file}")
            
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            print(f"   📏 Size: {len(file_content):,} bytes")
            print(f"   🔢 MD5: {hashlib.md5(file_content).hexdigest()}")
            
            if file_content.startswith(b'%PDF-'):
                print(f"   ✅ Valid PDF header")
            else:
                print(f"   ❌ Invalid PDF header")
            
            try:
                text_content, page_count = await textract_service.upload_to_s3_and_extract(
                    file_content,
                    os.path.basename(test_file),
                    user_id="test_multiple"
                )
                
                print(f"   ✅ Extraction successful: {len(text_content)} chars")
                
            except Exception as e:
                print(f"   ❌ Extraction failed: {e}")
        else:
            print(f"   ⚠ File not found: {test_file}")

if __name__ == "__main__":
    print("🔬 File Integrity Debug Test")
    print("This will show detailed file integrity logs to debug upload issues")
    print("=" * 80)
    
    asyncio.run(test_file_integrity_debug())
    print("\n" + "=" * 80)
    asyncio.run(test_multiple_files()) 