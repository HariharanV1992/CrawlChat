#!/usr/bin/env python3
"""
Delete the ZIP-based worker Lambda and its SQS trigger.
"""

import boto3
import os

def delete_zip_worker():
    """Delete the ZIP-based worker Lambda."""
    
    print("🗑️  Deleting ZIP-based worker Lambda...")
    
    # Configuration
    function_name = "crawlchat-crawl-worker"
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    try:
        # Get clients
        lambda_client = boto3.client("lambda", region_name=region)
        sqs_client = boto3.client("sqs", region_name=region)
        
        # Get queue ARN
        queue_response = sqs_client.get_queue_url(QueueName="crawlchat-crawl-tasks")
        account_id = boto3.client('sts').get_caller_identity()['Account']
        queue_arn = f"arn:aws:sqs:{region}:{account_id}:crawlchat-crawl-tasks"
        
        print(f"📋 Queue ARN: {queue_arn}")
        
        # Delete event source mappings first
        print("🔗 Deleting SQS event source mappings...")
        response = lambda_client.list_event_source_mappings(
            FunctionName=function_name,
            EventSourceArn=queue_arn
        )
        
        for mapping in response['EventSourceMappings']:
            print(f"🗑️  Deleting mapping: {mapping['UUID']}")
            lambda_client.delete_event_source_mapping(UUID=mapping['UUID'])
        
        # Delete the Lambda function
        print(f"🗑️  Deleting Lambda function: {function_name}")
        lambda_client.delete_function(FunctionName=function_name)
        
        print("✅ ZIP-based worker Lambda deleted successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting worker: {e}")
        return False

if __name__ == "__main__":
    delete_zip_worker() 