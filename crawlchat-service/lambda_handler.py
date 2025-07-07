#!/usr/bin/env python3
"""
Test debug script to run locally and compare with Lambda
"""

import asyncio
import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.document_service import document_service

async def test_local_debug():
    """Test the debug functionality locally."""
    
    print("🔍 Testing Local PDF Debug Information")
    print("=" * 50)
    
    # Test with the existing PDF file
    test_file = "../Namecheap.pdf"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    try:
        # Read the file
        with open(test_file, "rb") as f:
            content = f.read()
        
        print(f"📄 Testing with: {test_file}")
        print(f"   Size: {len(content)} bytes ({len(content) / (1024*1024):.2f} MB)")
        
        # Get debug info
        debug_info = document_service._get_pdf_debug_info(content, test_file)
        
        print("\n📊 DEBUG INFORMATION:")
        print(f"   File Size: {debug_info['file_info']['size_bytes']} bytes")
        print(f"   MD5 Hash: {debug_info['file_info']['md5_hash']}")
        print(f"   PDF Header: {'✅' if debug_info['file_info']['is_pdf_header'] else '❌'}")
        print(f"   EOF Marker: {'✅' if debug_info['file_info']['has_eof_marker'] else '❌'}")
        print(f"   Null Byte Ratio: {debug_info['file_info']['null_byte_ratio']:.2%}")
        
        print(f"\n🌍 ENVIRONMENT:")
        print(f"   Python: {debug_info['environment']['python_version']}")
        print(f"   Platform: {debug_info['environment']['platform']}")
        print(f"   Is Lambda: {debug_info['environment']['is_lambda']}")
        
        print(f"\n📚 LIBRARIES:")
        for lib_name, lib_info in debug_info['libraries'].items():
            if lib_info['available']:
                print(f"   ✅ {lib_name}: {lib_info['version']}")
            else:
                print(f"   ❌ {lib_name}: {lib_info['error']}")
        
        # Test extraction
        print(f"\n🔄 TESTING EXTRACTION:")
        result = await document_service._extract_pdf_text_optimized(content, test_file)
        
        if "unable to read" in result.lower():
            print("   ❌ Extraction failed - got error message")
            print(f"   Error: {result[:200]}...")
        else:
            print("   ✅ Extraction successful")
            print(f"   Result length: {len(result)} characters")
            print(f"   Preview: {result[:200]}...")
        
        print(f"\n📋 COMPLETE DEBUG INFO (for comparison with Lambda):")
        import json
        print(json.dumps(debug_info, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_debug()) 