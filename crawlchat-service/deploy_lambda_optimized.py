#!/usr/bin/env python3
"""
Deploy optimized Lambda function to fix cold start timeout issues.
"""

import boto3
import json
import os
import zipfile
import tempfile
import shutil
from pathlib import Path

def create_deployment_package():
    """Create a deployment package with the optimized Lambda handler."""
    
    print("📦 Creating deployment package...")
    
    # Create a temporary directory for the package
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the optimized lambda handler
        shutil.copy2("lambda_handler.py", temp_path / "lambda_handler.py")
        
        # Copy the common package
        common_src = Path("common/src")
        if common_src.exists():
            shutil.copytree(common_src, temp_path / "common" / "src")
            print("✅ Copied common package")
        
        # Copy lambda-service src if it exists
        lambda_src = Path("lambda-service/src")
        if lambda_src.exists():
            shutil.copytree(lambda_src, temp_path / "src")
            print("✅ Copied lambda-service src")
        
        # Copy requirements
        if Path("requirements.txt").exists():
            shutil.copy2("requirements.txt", temp_path / "requirements.txt")
            print("✅ Copied requirements.txt")
        
        # Create the zip file
        zip_path = Path("lambda-deployment-optimized.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created deployment package: {zip_path}")
        return zip_path

def update_lambda_function(function_name: str, zip_path: Path, region: str = "ap-south-1"):
    """Update the Lambda function with the new deployment package."""
    
    print(f"🚀 Updating Lambda function: {function_name}")
    print(f"📍 Region: {region}")
    
    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Read the deployment package
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        print(f"📦 Package size: {len(zip_content) / (1024*1024):.2f} MB")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print("✅ Lambda function code updated successfully!")
        print(f"📊 Function ARN: {response['FunctionArn']}")
        print(f"📊 Runtime: {response['Runtime']}")
        print(f"📊 Handler: {response['Handler']}")
        
        # Update function configuration for better performance
        config_response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=30,  # Increase timeout to 30 seconds
            MemorySize=1024,  # Keep 1024 MB memory
            Environment={
                'Variables': {
                    'ENVIRONMENT': 'production',
                    'PYTHONPATH': '/var/task:/var/task/common/src',
                    'LAMBDA_OPTIMIZED': 'true'
                }
            }
        )
        
        print("✅ Lambda function configuration updated!")
        print(f"📊 Timeout: {config_response['Timeout']} seconds")
        print(f"📊 Memory: {config_response['MemorySize']} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Lambda function: {e}")
        return False

def test_lambda_function(function_name: str, region: str = "ap-south-1"):
    """Test the Lambda function with a simple health check."""
    
    print(f"🧪 Testing Lambda function: {function_name}")
    
    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Test event for health check
        test_event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {
                "Content-Type": "application/json"
            },
            "queryStringParameters": None,
            "body": None,
            "isBase64Encoded": False
        }
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"📊 Status Code: {response['StatusCode']}")
        print(f"📊 Response: {json.dumps(payload, indent=2)}")
        
        if response['StatusCode'] == 200:
            print("✅ Lambda function test successful!")
            return True
        else:
            print("❌ Lambda function test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test Lambda function: {e}")
        return False

def main():
    """Main deployment function."""
    
    print("🚀 Lambda Optimization Deployment")
    print("=" * 50)
    
    # Configuration
    FUNCTION_NAME = "crawlchat-api-function"
    REGION = "ap-south-1"
    
    # Create deployment package
    zip_path = create_deployment_package()
    
    # Update Lambda function
    success = update_lambda_function(FUNCTION_NAME, zip_path, REGION)
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Deployment completed successfully!")
        
        # Test the function
        print("\n🧪 Testing deployed function...")
        test_success = test_lambda_function(FUNCTION_NAME, REGION)
        
        if test_success:
            print("\n🎉 SUCCESS: Lambda function is now optimized and working!")
            print("📋 Summary of optimizations:")
            print("   - Lazy loading of heavy dependencies")
            print("   - Deferred crawler imports")
            print("   - Optimized cold start time")
            print("   - Increased timeout to 30 seconds")
        else:
            print("\n⚠️  WARNING: Function deployed but test failed")
    else:
        print("\n❌ Deployment failed!")

if __name__ == "__main__":
    main() 