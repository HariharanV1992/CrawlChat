#!/usr/bin/env python3
"""
Debug script to test AWS Textract integration and identify issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.aws_textract_service import textract_service, DocumentType
from common.src.core.aws_config import aws_config

async def debug_textract_integration():
    """Debug AWS Textract integration."""
    
    print("🔍 Debugging AWS Textract Integration")
    print("=" * 50)
    
    # Test 1: Check AWS Configuration
    print("\n1️⃣ Checking AWS Configuration...")
    print(f"   AWS Region: {aws_config.region}")
    print(f"   Textract Region: {aws_config.textract_region}")
    print(f"   S3 Bucket: {aws_config.s3_bucket}")
    print(f"   Access Key ID: {'✅ Set' if aws_config.access_key_id else '❌ Not Set'}")
    print(f"   Secret Access Key: {'✅ Set' if aws_config.secret_access_key else '❌ Not Set'}")
    
    # Test 2: Check Environment Variables
    print("\n2️⃣ Checking Environment Variables...")
    env_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_DEFAULT_REGION',
        'AWS_REGION',
        'TEXTRACT_REGION',
        'S3_BUCKET'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"   {var}: ✅ {masked_value}")
            else:
                print(f"   {var}: ✅ {value}")
        else:
            print(f"   {var}: ❌ Not Set")
    
    # Test 3: Check AWS Clients
    print("\n3️⃣ Checking AWS Clients...")
    try:
        if textract_service.textract_client:
            print("   Textract Client: ✅ Initialized")
            # Test Textract client
            try:
                # Simple test call
                response = textract_service.textract_client.list_document_analysis_jobs(MaxResults=1)
                print("   Textract API: ✅ Accessible")
            except Exception as e:
                print(f"   Textract API: ❌ Error - {e}")
        else:
            print("   Textract Client: ❌ Not Initialized")
    except Exception as e:
        print(f"   Textract Client: ❌ Error - {e}")
    
    try:
        if textract_service.s3_client:
            print("   S3 Client: ✅ Initialized")
            # Test S3 client
            try:
                # Simple test call
                response = textract_service.s3_client.list_buckets()
                print("   S3 API: ✅ Accessible")
            except Exception as e:
                print(f"   S3 API: ❌ Error - {e}")
        else:
            print("   S3 Client: ❌ Not Initialized")
    except Exception as e:
        print(f"   S3 Client: ❌ Error - {e}")
    
    # Test 4: Check Lambda Environment
    print("\n4️⃣ Checking Lambda Environment...")
    lambda_env = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    if lambda_env:
        print(f"   Lambda Function: ✅ {lambda_env}")
        print("   Using IAM Role for AWS credentials")
    else:
        print("   Lambda Function: ❌ Not in Lambda environment")
        print("   Using local AWS credentials")
    
    # Test 5: Test with Sample PDF (if available)
    print("\n5️⃣ Testing with Sample PDF...")
    sample_pdf = Path(__file__).parent / "Namecheap.pdf"
    if sample_pdf.exists():
        print(f"   Sample PDF: ✅ Found ({sample_pdf.stat().st_size:,} bytes)")
        
        try:
            with open(sample_pdf, 'rb') as f:
                pdf_content = f.read()
            
            print("   Testing Textract extraction...")
            text_content, page_count = await textract_service.upload_to_s3_and_extract(
                pdf_content,
                "test_debug.pdf",
                DocumentType.GENERAL,
                "debug_user"
            )
            
            if text_content and len(text_content.strip()) > 10:
                print(f"   ✅ Textract Success: {len(text_content)} characters, {page_count} pages")
                print(f"   📄 Preview: {text_content[:200]}...")
            else:
                print(f"   ⚠ Textract returned minimal content: {len(text_content.strip())} chars")
                
        except Exception as e:
            print(f"   ❌ Textract Test Failed: {e}")
    else:
        print("   Sample PDF: ❌ Not found (Namecheap.pdf)")
    
    # Test 6: Check Boto3 Installation
    print("\n6️⃣ Checking Boto3 Installation...")
    try:
        import boto3
        print(f"   Boto3: ✅ Installed (version: {boto3.__version__})")
        
        # Test basic boto3 functionality
        try:
            session = boto3.Session()
            print("   Boto3 Session: ✅ Created successfully")
        except Exception as e:
            print(f"   Boto3 Session: ❌ Error - {e}")
            
    except ImportError:
        print("   Boto3: ❌ Not installed")
    
    print("\n" + "=" * 50)
    print("🔍 Debug Summary:")
    print("If you see '❌' for AWS clients or credentials, Textract won't work.")
    print("If you see '✅' for AWS clients but Textract test fails, check IAM permissions.")
    print("If Textract test succeeds, the issue is in your application code.")

if __name__ == "__main__":
    asyncio.run(debug_textract_integration()) 