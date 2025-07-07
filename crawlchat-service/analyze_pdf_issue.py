#!/usr/bin/env python3
"""
Analyze the specific PDF that's causing Textract issues.
"""

import asyncio
import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.aws_textract_service import textract_service
from common.src.services.storage_service import get_storage_service

async def analyze_problematic_pdf():
    """Analyze the PDF that's causing Textract issues."""
    
    print("🔍 Analyzing Problematic PDF")
    print("=" * 50)
    
    # The problematic PDF from your logs
    s3_key = "uploaded_documents/7320c5a4-8865-468c-a851-5edc3ad445e2/9e8935da-c2ce-48ad-b3c8-d10d5054df6e/58ae9f1389dc203189f5bd56ba030d16.pdf"
    filename = "58ae9f1389dc203189f5bd56ba030d16.pdf"
    
    try:
        # Get the file content from S3
        storage_service = get_storage_service()
        file_content = await storage_service.get_file_content(s3_key)
        
        if not file_content:
            print("❌ Could not retrieve file content from S3")
            return
        
        print(f"✅ Retrieved file: {len(file_content):,} bytes")
        
        # Analyze the PDF content
        print("\n📊 PDF Analysis:")
        analysis = textract_service.analyze_pdf_content(file_content, filename)
        
        for key, value in analysis.items():
            print(f"   {key}: {value}")
        
        # Test Textract extraction
        print(f"\n🔄 Testing Textract Extraction:")
        try:
            text_content, page_count = await textract_service.upload_to_s3_and_extract(
                file_content,
                filename,
                textract_service.DocumentType.GENERAL,
                "test_user"
            )
            
            print(f"   Textract Result: {len(text_content.strip())} characters")
            print(f"   Page Count: {page_count}")
            
            if text_content.strip():
                print(f"   Preview: {text_content[:200]}...")
            else:
                print("   ⚠️ No text content extracted")
                
        except Exception as e:
            print(f"   ❌ Textract Error: {e}")
        
        # Provide recommendations
        print(f"\n💡 Recommendations:")
        if analysis.get("pdf_type") == "image_based":
            print("   • This appears to be an image-based PDF (scanned document)")
            print("   • Textract may not work well with this type of PDF")
            print("   • Consider uploading the original source file")
        elif analysis.get("pdf_type") == "text_based":
            print("   • This appears to be a text-based PDF")
            print("   • Textract should work, but there may be an issue")
            print("   • Check if the PDF is corrupted or has unusual formatting")
        else:
            print("   • PDF type unclear, try uploading a different document")
        
    except Exception as e:
        print(f"❌ Error analyzing PDF: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_problematic_pdf()) 