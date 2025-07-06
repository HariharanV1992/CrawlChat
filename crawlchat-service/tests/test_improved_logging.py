#!/usr/bin/env python3
"""
Test script to verify improved logging in the Textract service.
"""

import asyncio
import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see all the improved messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from common.src.services.aws_textract_service import textract_service

async def test_improved_logging():
    """Test the improved logging with a sample PDF."""
    
    # Test with a sample PDF file
    test_file_path = "Namecheap.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file {test_file_path} not found!")
        return
    
    print(f"🔍 Testing improved logging with: {test_file_path}")
    print("=" * 60)
    
    # Read the file
    with open(test_file_path, 'rb') as f:
        file_content = f.read()
    
    try:
        # Test the improved extraction with detailed logging
        text_content, page_count = await textract_service.upload_to_s3_and_extract(
            file_content,
            os.path.basename(test_file_path),
            user_id="test_logging"
        )
        
        print("\n" + "=" * 60)
        print(f"🏁 Final Result:")
        print(f"   Text length: {len(text_content)} characters")
        print(f"   Page count: {page_count}")
        print(f"   Success: {'✅' if len(text_content.strip()) > 50 else '❌'}")
        
        if len(text_content.strip()) > 50:
            print(f"   Preview: {text_content[:200]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Improved Logging")
    print("This will show detailed logs for each extraction step")
    print("=" * 60)
    
    asyncio.run(test_improved_logging()) 