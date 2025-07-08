#!/usr/bin/env python3
"""
Debug the SQS worker Lambda and trigger configuration.
"""

import boto3
import os
import json

def debug_worker():
    """Debug the worker Lambda and SQS trigger."""
    
    print("🔍 Debugging SQS Worker Lambda...")
    
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
        
        # Check queue messages
        queue_attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_response['QueueUrl'],
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        available = queue_attributes['Attributes']['ApproximateNumberOfMessages']
        in_flight = queue_attributes['Attributes']['ApproximateNumberOfMessagesNotVisible']
        
        print(f"📨 Messages available: {available}")
        print(f"📨 Messages in flight: {in_flight}")
        
        # Check Lambda function
        try:
            function_response = lambda_client.get_function(FunctionName=function_name)
            print(f"✅ Lambda function exists: {function_name}")
            print(f"📋 Runtime: {function_response['Configuration']['Runtime']}")
            print(f"📋 Handler: {function_response['Configuration']['Handler']}")
            print(f"📋 Timeout: {function_response['Configuration']['Timeout']}")
        except Exception as e:
            print(f"❌ Error getting Lambda function: {e}")
            return
        
        # Check event source mappings
        response = lambda_client.list_event_source_mappings(
            FunctionName=function_name,
            EventSourceArn=queue_arn
        )
        
        if response['EventSourceMappings']:
            mapping = response['EventSourceMappings'][0]
            print(f"✅ Event source mapping found:")
            print(f"📋 UUID: {mapping['UUID']}")
            print(f"📋 State: {mapping['State']}")
            print(f"📋 Batch Size: {mapping['BatchSize']}")
            print(f"📋 Enabled: {mapping['Enabled']}")
            
            if mapping['State'] != 'Enabled':
                print(f"⚠️  WARNING: Event source mapping is not enabled!")
                print(f"   Current state: {mapping['State']}")
                
        else:
            print(f"❌ No event source mappings found!")
            
        # Test manual invocation
        print("\n🧪 Testing manual invocation...")
        test_event = {
            "Records": [
                {
                    "body": json.dumps({"task_id": "test-task-123", "user_id": "test-user"})
                }
            ]
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            payload = json.loads(response['Payload'].read())
            print(f"✅ Manual invocation successful")
            print(f"📋 Status Code: {response['StatusCode']}")
            print(f"📋 Response: {payload}")
            
        except Exception as e:
            print(f"❌ Manual invocation failed: {e}")
            
    except Exception as e:
        print(f"❌ Error debugging worker: {e}")

if __name__ == "__main__":
    debug_worker() 