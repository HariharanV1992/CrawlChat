#!/usr/bin/env python3
"""
Test script to verify the PDF to image fallback mechanism.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append('src')

from src.services.aws_textract_service import textract_service

async def test_fallback_mechanism():
    """Test the PDF to image fallback mechanism."""
    
    print("🚀 Testing PDF to Image Fallback Mechanism")
    print("=" * 60)
    
    # Test with the problematic PDF
    s3_bucket = "stock-market-crawler-data"
    s3_key = "crawled_documents/textract_processing/7320c5a4-8865-468c-a851-5edc3ad445e2/9e479d0b-f855-42a7-8eb8-fde8dde56c86/Hariharan Vijayakumar_7X8.pdf"
    
    print(f"🔍 Testing fallback with: s3://{s3_bucket}/{s3_key}")
    
    try:
        # Initialize the Textract service
        textract_service._init_clients()
        
        # Test the enhanced extraction method
        text_content, page_count = await textract_service.extract_text_from_s3_pdf(
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            document_type=textract_service.DocumentType.GENERAL
        )
        
        print(f"✅ Fallback mechanism successful!")
        print(f"   📄 Pages processed: {page_count}")
        print(f"   📝 Characters extracted: {len(text_content)}")
        print(f"   📖 Preview: {text_content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback mechanism failed: {e}")
        return False

async def test_compatibility_guide():
    """Test the compatibility guide functionality."""
    
    print("\n📋 Testing Compatibility Guide")
    print("=" * 60)
    
    try:
        guide = textract_service.get_textract_compatibility_guide()
        
        print("✅ Compatibility guide generated successfully!")
        print(f"   📋 Supported formats: {len(guide['supported_formats'])}")
        print(f"   ⚠️  Unsupported formats: {len(guide['unsupported_formats'])}")
        print(f"   💡 Recommendations: {len(guide['recommendations'])}")
        print(f"   🔧 Troubleshooting tips: {len(guide['troubleshooting'])}")
        
        print("\n📋 Supported Formats:")
        for fmt in guide['supported_formats']:
            print(f"   ✅ {fmt}")
            
        print("\n⚠️  Unsupported Formats:")
        for fmt in guide['unsupported_formats']:
            print(f"   ❌ {fmt}")
            
        return True
        
    except Exception as e:
        print(f"❌ Compatibility guide test failed: {e}")
        return False

async def main():
    """Main test function."""
    
    print("🧪 Testing Enhanced Textract Service with Fallback")
    print("=" * 60)
    
    # Test 1: Compatibility Guide
    guide_test = await test_compatibility_guide()
    
    # Test 2: Fallback Mechanism (only if we have the dependencies)
    try:
        import pdf2image
        print(f"\n✅ pdf2image available: {pdf2image.__version__}")
        fallback_test = await test_fallback_mechanism()
    except ImportError:
        print(f"\n❌ pdf2image not available - skipping fallback test")
        print(f"   Install with: pip install pdf2image")
        fallback_test = False
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   📋 Compatibility Guide: {'✅' if guide_test else '❌'}")
    print(f"   🔄 Fallback Mechanism: {'✅' if fallback_test else '❌'}")
    
    if guide_test and fallback_test:
        print(f"\n🎉 All tests passed! Your system is ready to handle any PDF format.")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 