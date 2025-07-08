#!/usr/bin/env python3
"""
Test script to trigger Lambda function and test document processing.
"""

import boto3
import json
import uuid
import time

def test_lambda_trigger():
    """Test Lambda function by sending a test SQS message."""
    
    print("🚀 Testing Lambda function trigger...")
    
    # Configuration
    sqs_queue_name = "crawlchat-crawl-tasks"
    region = "ap-south-1"
    
    try:
        # Create SQS client
        sqs = boto3.client('sqs', region_name=region)
        
        # Get queue URL
        try:
            response = sqs.get_queue_url(QueueName=sqs_queue_name)
            queue_url = response['QueueUrl']
            print(f"✅ Found SQS queue: {queue_url}")
        except Exception as e:
            print(f"❌ Error getting SQS queue: {e}")
            return False
        
        # Create test message
        test_task_id = str(uuid.uuid4())
        test_message = {
            "task_id": test_task_id,
            "user_id": "test-user",
            "url": "https://www.business-standard.com",
            "max_pages": 2,
            "max_documents": 5
        }
        
        print(f"📤 Sending test message with task_id: {test_task_id}")
        
        # Send message to SQS
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(test_message)
        )
        
        print(f"✅ Message sent successfully: {response['MessageId']}")
        
        # Wait a bit for processing
        print("⏳ Waiting 30 seconds for Lambda processing...")
        time.sleep(30)
        
        # Check if message was processed
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        messages_in_queue = int(response['Attributes']['ApproximateNumberOfMessages'])
        messages_in_flight = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
        
        print(f"📊 Queue status:")
        print(f"   Messages in queue: {messages_in_queue}")
        print(f"   Messages in flight: {messages_in_flight}")
        
        if messages_in_queue == 0 and messages_in_flight == 0:
            print("✅ All messages processed successfully!")
        else:
            print("⚠️  Some messages still in queue or processing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda trigger: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_lambda_logs():
    """Check recent Lambda logs for any errors."""
    
    print("\n🔍 Checking recent Lambda logs...")
    
    try:
        # Create CloudWatch Logs client
        logs = boto3.client('logs', region_name='ap-south-1')
        
        # Get recent log streams
        response = logs.describe_log_streams(
            logGroupName='/aws/lambda/crawlchat-crawler-function',
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not response['logStreams']:
            print("❌ No log streams found")
            return
        
        latest_stream = response['logStreams'][0]['logStreamName']
        print(f"📋 Latest log stream: {latest_stream}")
        
        # Get recent events
        response = logs.get_log_events(
            logGroupName='/aws/lambda/crawlchat-crawler-function',
            logStreamName=latest_stream,
            startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
            limit=50
        )
        
        if not response['events']:
            print("📭 No recent log events found")
            return
        
        print("📝 Recent log events:")
        for event in response['events'][-10:]:  # Last 10 events
            timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
            message = event['message'].strip()
            if message:
                print(f"   [{timestamp}] {message}")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    # Test Lambda trigger
    success = test_lambda_trigger()
    
    # Check logs
    check_lambda_logs()
    
    if success:
        print("\n🎉 Lambda test completed successfully!")
    else:
        print("\n❌ Lambda test failed!") 