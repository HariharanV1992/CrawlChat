#!/usr/bin/env python3
"""
Test script to demonstrate PDF preprocessing capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.pdf_preprocessing_service import pdf_preprocessing_service
from common.src.services.aws_textract_service import textract_service, DocumentType

async def test_pdf_preprocessing():
    """Test PDF preprocessing capabilities."""
    
    print("🔧 Testing PDF Preprocessing for Textract")
    print("=" * 50)
    
    # Test with the problematic PDF from your logs
    s3_key = "uploaded_documents/7320c5a4-8865-468c-a851-5edc3ad445e2/9e8935da-c2ce-48ad-b3c8-d10d5054df6e/58ae9f1389dc203189f5bd56ba030d16.pdf"
    filename = "58ae9f1389dc203189f5bd56ba030d16.pdf"
    
    try:
        # Get the file content from S3
        from common.src.services.storage_service import get_storage_service
        storage_service = get_storage_service()
        file_content = await storage_service.get_file_content(s3_key)
        
        if not file_content:
            print("❌ Could not retrieve file content from S3")
            return
        
        print(f"✅ Retrieved file: {len(file_content):,} bytes")
        
        # Test 1: Preprocess the PDF
        print(f"\n🔄 Step 1: Preprocessing PDF...")
        original_size = len(file_content)
        
        try:
            processed_content = await pdf_preprocessing_service.preprocess_pdf_for_textract(file_content, filename)
            processed_size = len(processed_content)
            
            stats = pdf_preprocessing_service.get_preprocessing_stats(original_size, processed_size)
            print(f"✅ Preprocessing completed:")
            print(f"   Original size: {stats['original_size_bytes']:,} bytes")
            print(f"   Processed size: {stats['processed_size_bytes']:,} bytes")
            print(f"   Size reduction: {stats['size_reduction_percent']:.1f}%")
            print(f"   Method: {stats['preprocessing_method']}")
            
        except Exception as e:
            print(f"❌ Preprocessing failed: {e}")
            processed_content = file_content
        
        # Test 2: Compare Textract performance
        print(f"\n🔄 Step 2: Testing Textract with original PDF...")
        try:
            original_text, original_pages = await textract_service.upload_to_s3_and_extract(
                file_content,
                f"original_{filename}",
                DocumentType.GENERAL,
                "test_user"
            )
            print(f"   Original PDF - Text length: {len(original_text.strip())} chars")
            print(f"   Original PDF - Pages: {original_pages}")
            
        except Exception as e:
            print(f"   ❌ Original PDF Textract failed: {e}")
            original_text = ""
        
        print(f"\n🔄 Step 3: Testing Textract with preprocessed PDF...")
        try:
            processed_text, processed_pages = await textract_service.upload_to_s3_and_extract(
                processed_content,
                f"preprocessed_{filename}",
                DocumentType.GENERAL,
                "test_user"
            )
            print(f"   Preprocessed PDF - Text length: {len(processed_text.strip())} chars")
            print(f"   Preprocessed PDF - Pages: {processed_pages}")
            
        except Exception as e:
            print(f"   ❌ Preprocessed PDF Textract failed: {e}")
            processed_text = ""
        
        # Test 4: Compare results
        print(f"\n📊 Results Comparison:")
        original_length = len(original_text.strip())
        processed_length = len(processed_text.strip())
        
        if original_length > 0 and processed_length > 0:
            improvement = ((processed_length - original_length) / original_length) * 100
            print(f"   Text extraction improvement: {improvement:+.1f}%")
            
            if improvement > 0:
                print(f"   ✅ Preprocessing improved text extraction!")
            elif improvement < 0:
                print(f"   ⚠️ Preprocessing reduced text extraction")
            else:
                print(f"   ➖ No change in text extraction")
        else:
            print(f"   ⚠️ Could not compare results (one or both extractions failed)")
        
        # Test 5: Show text previews
        if original_text.strip():
            print(f"\n📄 Original PDF Text Preview:")
            print(f"   {original_text[:200]}...")
        
        if processed_text.strip():
            print(f"\n📄 Preprocessed PDF Text Preview:")
            print(f"   {processed_text[:200]}...")
        
        print(f"\n" + "=" * 50)
        print("🎯 Summary:")
        print("- PDF preprocessing removes visuals that interfere with text extraction")
        print("- This should improve Textract's ability to extract text from complex PDFs")
        print("- The preprocessing uses both OpenCV edge detection and pixel analysis")
        print("- If preprocessing improves results, it will be automatically applied to all PDFs")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_pdf_preprocessing()) 