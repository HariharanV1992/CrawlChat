#!/usr/bin/env python3
"""
Script to create the SQS queue needed by the Lambda function.
Run this script before deploying the Lambda function.
"""

import boto3
import os
import sys

def create_sqs_queue():
    """Create the SQS queue for crawl tasks."""
    
    # Configuration
    queue_name = os.getenv("CRAWLCHAT_SQS_QUEUE", "crawlchat-crawl-tasks")
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    print(f"Creating SQS queue: {queue_name}")
    print(f"Region: {region}")
    
    try:
        # Create SQS client
        sqs_client = boto3.client("sqs", region_name=region)
        
        # Check if queue already exists
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            print(f"✅ Queue '{queue_name}' already exists: {response['QueueUrl']}")
            return response['QueueUrl']
        except sqs_client.exceptions.QueueDoesNotExist:
            pass
        
        # Create the queue
        response = sqs_client.create_queue(
            QueueName=queue_name,
            Attributes={
                'VisibilityTimeout': '300',  # 5 minutes
                'MessageRetentionPeriod': '1209600',  # 14 days
                'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
            }
        )
        
        queue_url = response['QueueUrl']
        print(f"✅ Successfully created SQS queue: {queue_url}")
        
        # Get queue ARN for IAM policy
        queue_attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attributes['Attributes']['QueueArn']
        print(f"📋 Queue ARN: {queue_arn}")
        
        print("\n🔧 Next steps:")
        print("1. Update your Lambda execution role to include these SQS permissions:")
        print("   - sqs:SendMessage")
        print("   - sqs:ReceiveMessage") 
        print("   - sqs:DeleteMessage")
        print("   - sqs:GetQueueUrl")
        print("   - sqs:GetQueueAttributes")
        print(f"2. Resource: {queue_arn}")
        print("3. Deploy your Lambda function")
        
        return queue_url
        
    except Exception as e:
        print(f"❌ Error creating SQS queue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_sqs_queue() 