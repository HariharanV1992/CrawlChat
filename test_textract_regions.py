#!/usr/bin/env python3
"""
Test script to check Textract availability in different regions.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, EndpointConnectionError

def test_textract_region(region_name):
    """Test if Textract is available in a specific region."""
    print(f"\n🔍 Testing Textract in region: {region_name}")
    print("-" * 50)
    
    try:
        # Create Textract client
        textract_client = boto3.client('textract', region_name=region_name)
        print(f"✅ Textract client created successfully in {region_name}")
        
        # Test with a simple document (we'll use a small test)
        try:
            # Create a simple test document (1x1 pixel PNG)
            import base64
            # This is a minimal 1x1 pixel PNG file
            test_png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
            
            response = textract_client.detect_document_text(
                Document={
                    'Bytes': test_png
                }
            )
            print(f"✅ Textract API is working in {region_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnsupportedDocumentException':
                print(f"✅ Textract API is available in {region_name} (UnsupportedDocumentException is expected for 1x1 pixel)")
                return True
            else:
                print(f"❌ Textract API error in {region_name}: {error_code}")
                return False
                
    except EndpointConnectionError:
        print(f"❌ Textract endpoint not available in {region_name}")
        return False
    except Exception as e:
        print(f"❌ Error testing Textract in {region_name}: {e}")
        return False

def test_detect_document_text(region_name, s3_bucket, s3_key):
    """Test DetectDocumentText API with a simple document."""
    print(f"\n🔍 Testing DetectDocumentText in {region_name}")
    print("-" * 50)
    
    try:
        textract_client = boto3.client('textract', region_name=region_name)
        
        # Try to call DetectDocumentText
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            }
        )
        
        print(f"✅ DetectDocumentText successful in {region_name}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', '')
        print(f"❌ DetectDocumentText failed in {region_name}: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in {region_name}: {e}")
        return False

def main():
    """Main test function."""
    
    print("🚀 Testing Textract Availability in Different Regions")
    print("=" * 60)
    
    # Test regions
    regions_to_test = [
        'us-east-1',      # US East (N. Virginia) - Primary region
        'us-west-2',      # US West (Oregon)
        'eu-west-1',      # Europe (Ireland)
        'ap-south-1',     # Asia Pacific (Mumbai) - Your current region
        'ap-southeast-1', # Asia Pacific (Singapore)
        'ap-northeast-1'  # Asia Pacific (Tokyo)
    ]
    
    # Test basic availability
    available_regions = []
    for region in regions_to_test:
        if test_textract_region(region):
            available_regions.append(region)
    
    print(f"\n📊 Summary:")
    print(f"✅ Available regions: {', '.join(available_regions)}")
    
    # Test with your S3 object if available regions found
    if available_regions:
        print(f"\n🔍 Testing DetectDocumentText with your S3 object...")
        s3_bucket = "stock-market-crawler-data"
        s3_key = "crawled_documents/textract_processing/7320c5a4-8865-468c-a851-5edc3ad445e2/9e479d0b-f855-42a7-8eb8-fde8dde56c86/Hariharan Vijayakumar_7X8.pdf"
        
        for region in available_regions[:3]:  # Test first 3 available regions
            test_detect_document_text(region, s3_bucket, s3_key)

if __name__ == "__main__":
    main() 