import boto3
import os
import json
import logging
import traceback

logger = logging.getLogger(__name__)

SQS_QUEUE_NAME = os.getenv("CRAWLCHAT_SQS_QUEUE", "crawlchat-crawl-tasks")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

print(f"=== SQS HELPER INITIALIZATION ===")
print(f"SQS Queue Name: {SQS_QUEUE_NAME}")
print(f"AWS Region: {AWS_REGION}")

sqs_client = boto3.client("sqs", region_name=AWS_REGION)

class SQSHelper:
    def __init__(self, queue_name=SQS_QUEUE_NAME):
        self.queue_name = queue_name
        print(f"Initializing SQSHelper with queue: {queue_name}")
        self.queue_url = self.get_queue_url()

    def get_queue_url(self):
        """Get the queue URL. Assumes the queue already exists."""
        print(f"Getting queue URL for: {self.queue_name}")
        try:
            response = sqs_client.get_queue_url(QueueName=self.queue_name)
            queue_url = response["QueueUrl"]
            logger.info(f"Successfully got queue URL for {self.queue_name}")
            print(f"Successfully got queue URL: {queue_url}")
            return queue_url
        except sqs_client.exceptions.QueueDoesNotExist:
            error_msg = f"SQS queue '{self.queue_name}' does not exist. Please create it first."
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(f"SQS queue '{self.queue_name}' does not exist. Please create the queue before deploying the Lambda function.")
        except Exception as e:
            error_msg = f"Error getting queue URL for {self.queue_name}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def send_crawl_task(self, task_id, user_id):
        """Send a crawl task message to SQS."""
        print(f"=== SENDING CRAWL TASK TO SQS ===")
        print(f"Task ID: {task_id}")
        print(f"User ID: {user_id}")
        print(f"Queue URL: {self.queue_url}")
        
        try:
            message = {"task_id": task_id, "user_id": user_id}
            message_body = json.dumps(message)
            print(f"Message body: {message_body}")
            
            print("Sending message to SQS...")
            response = sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body
            )
            
            logger.info(f"Sent crawl task {task_id} to SQS queue")
            print(f"Successfully sent crawl task {task_id} to SQS queue")
            print(f"SQS Response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error sending crawl task to SQS: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def receive_messages(self, max_messages=1):
        """Receive messages from SQS queue."""
        try:
            response = sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=10
            )
            return response.get("Messages", [])
        except Exception as e:
            logger.error(f"Error receiving messages from SQS: {e}")
            raise

    def delete_message(self, receipt_handle):
        """Delete a message from SQS queue."""
        try:
            sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info("Successfully deleted message from SQS queue")
        except Exception as e:
            logger.error(f"Error deleting message from SQS: {e}")
            raise

# Initialize the SQS helper
sqs_helper = SQSHelper() 