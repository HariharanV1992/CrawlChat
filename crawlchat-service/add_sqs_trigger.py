#!/usr/bin/env python3
"""
Add SQS trigger to the worker Lambda.
"""

import boto3
import os

def add_sqs_trigger():
    """Add SQS trigger to the worker Lambda."""
    
    print("🔗 Adding SQS trigger to worker Lambda...")
    
    # Configuration
    function_name = "crawlchat-crawl-worker"
    queue_name = "crawlchat-crawl-tasks"
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    try:
        # Get clients
        lambda_client = boto3.client("lambda", region_name=region)
        sqs_client = boto3.client("sqs", region_name=region)
        
        # Get queue ARN
        queue_response = sqs_client.get_queue_url(QueueName=queue_name)
        account_id = boto3.client('sts').get_caller_identity()['Account']
        queue_arn = f"arn:aws:sqs:{region}:{account_id}:{queue_name}"
        
        print(f"📋 Queue ARN: {queue_arn}")
        
        # Check if trigger already exists
        try:
            response = lambda_client.list_event_source_mappings(
                FunctionName=function_name,
                EventSourceArn=queue_arn
            )
            
            if response['EventSourceMappings']:
                print("✅ SQS trigger already exists!")
                return True
                
        except Exception as e:
            print(f"⚠️  Warning checking existing triggers: {e}")
        
        # Create event source mapping
        response = lambda_client.create_event_source_mapping(
            EventSourceArn=queue_arn,
            FunctionName=function_name,
            BatchSize=1,
            Enabled=True
        )
        
        print(f"✅ SQS trigger added successfully!")
        print(f"📋 Event Source Mapping ID: {response['UUID']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding SQS trigger: {e}")
        return False

if __name__ == "__main__":
    add_sqs_trigger() 