#!/usr/bin/env python3
"""
Quick test to verify region configuration fix.
"""

import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.core.aws_config import aws_config
from common.src.services.aws_textract_service import textract_service

def test_region_configuration():
    """Test that regions are properly configured."""
    
    print("🔧 Testing Region Configuration Fix")
    print("=" * 40)
    
    # Test 1: Check main region
    print(f"\n1️⃣ Main AWS Region: {aws_config.region}")
    
    # Test 2: Check Textract region (should now match main region)
    print(f"2️⃣ Textract Region: {aws_config.textract_region}")
    
    # Test 3: Verify they match
    if aws_config.region == aws_config.textract_region:
        print("3️⃣ ✅ Regions match - S3 region mismatch should be fixed!")
    else:
        print(f"3️⃣ ❌ Regions don't match - {aws_config.region} vs {aws_config.textract_region}")
    
    # Test 4: Check S3 bucket
    print(f"4️⃣ S3 Bucket: {aws_config.s3_bucket}")
    
    # Test 5: Check if clients are initialized
    print(f"\n5️⃣ AWS Clients Status:")
    print(f"   Textract Client: {'✅ Initialized' if textract_service.textract_client else '❌ Not Initialized'}")
    print(f"   S3 Client: {'✅ Initialized' if textract_service.s3_client else '❌ Not Initialized'}")
    
    print("\n" + "=" * 40)
    print("🎯 Expected Result:")
    print("- Regions should match (both ap-south-1)")
    print("- This should fix the InvalidS3ObjectException")
    print("- Textract should now be able to access S3 objects")

if __name__ == "__main__":
    test_region_configuration() 