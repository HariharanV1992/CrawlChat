#!/usr/bin/env python3
"""
Deploy the SQS worker Lambda for processing crawl tasks.
"""

import boto3
import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path

def create_worker_package():
    """Create a deployment package for the worker Lambda."""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the worker file
        worker_file = Path("lambda_crawl_worker.py")
        if not worker_file.exists():
            print("❌ lambda_crawl_worker.py not found!")
            return None
            
        shutil.copy2(worker_file, temp_path / "lambda_handler.py")
        
        # Copy the common package
        common_dir = Path("common")
        if common_dir.exists():
            shutil.copytree(common_dir, temp_path / "common")
        
        # Copy requirements
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            shutil.copy2(requirements_file, temp_path / "requirements.txt")
        
        # Create zip file
        zip_path = Path("worker_deployment.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(temp_path)
                    zipf.write(file_path, arc_name)
        
        return zip_path

def deploy_worker():
    """Deploy the worker Lambda function."""
    
    print("🚀 Deploying SQS Worker Lambda...")
    
    # Configuration
    function_name = "crawlchat-crawl-worker"
    region = os.getenv("AWS_REGION", "ap-south-1")
    role_name = "lambda-execution-role"  # Use existing role
    
    try:
        # Create deployment package
        print("📦 Creating deployment package...")
        zip_path = create_worker_package()
        if not zip_path:
            return False
        
        # Get Lambda client
        lambda_client = boto3.client("lambda", region_name=region)
        iam_client = boto3.client("iam")
        
        # Get role ARN
        try:
            role_response = iam_client.get_role(RoleName=role_name)
            role_arn = role_response["Role"]["Arn"]
        except Exception as e:
            print(f"❌ Error getting role {role_name}: {e}")
            return False
        
        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=function_name)
            function_exists = True
            print(f"✅ Function {function_name} exists, updating...")
        except lambda_client.exceptions.ResourceNotFoundException:
            function_exists = False
            print(f"📝 Creating new function {function_name}...")
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        if function_exists:
            # Update function code
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=900,  # 15 minutes
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'CRAWLCHAT_SQS_QUEUE': 'crawlchat-crawl-tasks'
                    }
                }
            )
        else:
            # Create new function
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.10',
                Role=role_arn,
                Handler='lambda_handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Timeout=900,  # 15 minutes
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'CRAWLCHAT_SQS_QUEUE': 'crawlchat-crawl-tasks'
                    }
                }
            )
        
        # Add SQS trigger
        print("🔗 Setting up SQS trigger...")
        try:
            # Get queue URL
            sqs_client = boto3.client("sqs", region_name=region)
            queue_response = sqs_client.get_queue_url(QueueName="crawlchat-crawl-tasks")
            queue_arn = f"arn:aws:sqs:{region}:{boto3.client('sts').get_caller_identity()['Account']}:crawlchat-crawl-tasks"
            
            # Create event source mapping
            lambda_client.create_event_source_mapping(
                EventSourceArn=queue_arn,
                FunctionName=function_name,
                BatchSize=1,
                Enabled=True
            )
            print("✅ SQS trigger configured successfully!")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not set up SQS trigger: {e}")
            print("   You may need to set it up manually in the AWS Console")
        
        # Clean up
        zip_path.unlink()
        
        print(f"✅ Worker Lambda deployed successfully!")
        print(f"📋 Function name: {function_name}")
        print(f"📋 Region: {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying worker: {e}")
        return False

if __name__ == "__main__":
    success = deploy_worker()
    sys.exit(0 if success else 1) 