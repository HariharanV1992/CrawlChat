#!/usr/bin/env python3
"""
Update the existing container-based crawler function to handle SQS messages.
"""

import boto3
import os

def update_crawler_function():
    """Update the crawler function to handle SQS."""
    
    print("🔧 Updating crawler function for SQS...")
    
    # Configuration
    function_name = "crawlchat-crawler-function"
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
        
        # Update function configuration
        print(f"⚙️  Updating function configuration...")
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=900,  # 15 minutes
            MemorySize=1024,
            Environment={
                'Variables': {
                    'CRAWLCHAT_SQS_QUEUE': queue_name
                }
            }
        )
        
        # Add SQS trigger
        print("🔗 Adding SQS trigger...")
        try:
            # Check if trigger already exists
            response = lambda_client.list_event_source_mappings(
                FunctionName=function_name,
                EventSourceArn=queue_arn
            )
            
            if response['EventSourceMappings']:
                print("✅ SQS trigger already exists!")
            else:
                # Create event source mapping
                response = lambda_client.create_event_source_mapping(
                    EventSourceArn=queue_arn,
                    FunctionName=function_name,
                    BatchSize=1,
                    Enabled=True
                )
                print(f"✅ SQS trigger added successfully!")
                print(f"📋 Event Source Mapping ID: {response['UUID']}")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not set up SQS trigger: {e}")
            print("   You may need to set it up manually in the AWS Console")
        
        print(f"✅ Crawler function updated successfully!")
        print(f"📋 Function name: {function_name}")
        print(f"📋 Region: {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating crawler function: {e}")
        return False

if __name__ == "__main__":
    update_crawler_function() 