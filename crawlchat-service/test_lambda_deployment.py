#!/usr/bin/env python3
"""
Lambda Deployment Testing Script
Helps test and compare Lambda vs local PDF extraction
"""

import json
import boto3
import time
import sys
from pathlib import Path

def test_lambda_function(function_name: str, region: str = "us-east-1"):
    """Test the Lambda function and return results."""
    
    print(f"🚀 Testing Lambda Function: {function_name}")
    print(f"🌍 Region: {region}")
    print("=" * 60)
    
    try:
        # Initialize Lambda client
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Test event (empty for our debug handler)
        test_event = {}
        
        print("📤 Invoking Lambda function...")
        start_time = time.time()
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Lambda invocation completed in {duration:.2f} seconds")
        
        # Parse response
        payload = response['Payload'].read()
        result = json.loads(payload.decode('utf-8'))
        
        print(f"\n📊 LAMBDA RESPONSE:")
        print(f"Status Code: {result.get('statusCode', 'N/A')}")
        
        if 'body' in result:
            body = json.loads(result['body'])
            print(f"\n📋 DEBUG INFO:")
            print(json.dumps(body, indent=2, default=str))
            
            # Extract key information for comparison
            if 'debug_info' in body:
                debug = body['debug_info']
                
                print(f"\n🔍 KEY COMPARISON DATA:")
                print(f"File Size: {debug['file_info']['size_bytes']} bytes")
                print(f"MD5 Hash: {debug['file_info']['md5_hash']}")
                print(f"PDF Header: {'✅' if debug['file_info']['is_pdf_header'] else '❌'}")
                print(f"EOF Marker: {'✅' if debug['file_info']['has_eof_marker'] else '❌'}")
                print(f"Python Version: {debug['environment']['python_version']}")
                print(f"Is Lambda: {debug['environment']['is_lambda']}")
                print(f"Lambda Memory: {debug['environment']['lambda_memory']}")
                
                # Check libraries
                print(f"\n📚 LIBRARIES:")
                for lib_name, lib_info in debug['libraries'].items():
                    if lib_info.get('available'):
                        print(f"   ✅ {lib_name}: {lib_info.get('version', 'unknown')}")
                    else:
                        print(f"   ❌ {lib_name}: {lib_info.get('error', 'unknown error')}")
                
                # Check extraction
                if 'extraction' in body:
                    extraction = body['extraction']
                    if extraction.get('success'):
                        print(f"\n✅ EXTRACTION: Success")
                        print(f"   Pages with text: {extraction.get('pages_with_text', 'unknown')}")
                        if 'preview' in extraction:
                            print(f"   Preview: {extraction['preview']}")
                    else:
                        print(f"\n❌ EXTRACTION: Failed")
                        print(f"   Error: {extraction.get('error', 'unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return None

def compare_with_local():
    """Compare Lambda results with local results."""
    
    print(f"\n🔄 COMPARISON WITH LOCAL RESULTS:")
    print("=" * 60)
    
    # Local results (from our previous test)
    local_results = {
        "file_size": 361791,
        "md5_hash": "a474e61ccfd35d416d76ddc5345e9e0f",
        "pdf_header": True,
        "eof_marker": True,
        "python_version": "3.10.12",
        "libraries": {
            "PyPDF2": "3.0.1",
            "pdfminer.six": "20250506",
            "boto3": "1.39.2"
        },
        "extraction_success": True,
        "extraction_length": 2329
    }
    
    print("📊 LOCAL RESULTS:")
    print(f"   File Size: {local_results['file_size']} bytes")
    print(f"   MD5 Hash: {local_results['md5_hash']}")
    print(f"   PDF Header: {'✅' if local_results['pdf_header'] else '❌'}")
    print(f"   EOF Marker: {'✅' if local_results['eof_marker'] else '❌'}")
    print(f"   Python: {local_results['python_version']}")
    print(f"   Extraction: {'✅' if local_results['extraction_success'] else '❌'}")
    
    print(f"\n💡 COMPARISON INSTRUCTIONS:")
    print("1. Run this script with your Lambda function name")
    print("2. Compare the Lambda output with the local results above")
    print("3. Look for differences in:")
    print("   - File size and MD5 hash (file corruption)")
    print("   - Library versions (deployment issues)")
    print("   - Extraction success (environment differences)")
    print("   - Python version (runtime differences)")

def main():
    """Main function."""
    
    if len(sys.argv) < 2:
        print("❌ Usage: python test_lambda_deployment.py <lambda_function_name> [region]")
        print("\nExample: python test_lambda_deployment.py my-pdf-debug-function us-east-1")
        compare_with_local()
        return
    
    function_name = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-1"
    
    # Test the Lambda function
    result = test_lambda_function(function_name, region)
    
    if result:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Compare the Lambda output with local results above")
        print("2. Check CloudWatch logs for additional details")
        print("3. If there are differences, they indicate the root cause")
        print("4. Common issues:")
        print("   - Different library versions → Update Lambda layer/package")
        print("   - File corruption → Check S3 upload/read logic")
        print("   - Memory issues → Increase Lambda memory")
        print("   - Missing dependencies → Fix deployment package")
    
    compare_with_local()

if __name__ == "__main__":
    main() 