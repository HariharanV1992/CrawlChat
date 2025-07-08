import boto3
import os
import json
import logging

logger = logging.getLogger(__name__)

SQS_QUEUE_NAME = os.getenv("CRAWLCHAT_SQS_QUEUE", "crawlchat-crawl-tasks")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

sqs_client = boto3.client("sqs", region_name=AWS_REGION)

class SQSHelper:
    def __init__(self, queue_name=SQS_QUEUE_NAME):
        self.queue_name = queue_name
        self.queue_url = self.get_queue_url()

    def get_queue_url(self):
        """Get the queue URL. Assumes the queue already exists."""
        try:
            response = sqs_client.get_queue_url(QueueName=self.queue_name)
            logger.info(f"Successfully got queue URL for {self.queue_name}")
            return response["QueueUrl"]
        except sqs_client.exceptions.QueueDoesNotExist:
            logger.error(f"SQS queue '{self.queue_name}' does not exist. Please create it first.")
            raise Exception(f"SQS queue '{self.queue_name}' does not exist. Please create the queue before deploying the Lambda function.")
        except Exception as e:
            logger.error(f"Error getting queue URL for {self.queue_name}: {e}")
            raise

    def send_crawl_task(self, task_id, user_id):
        """Send a crawl task message to SQS."""
        try:
            message = {"task_id": task_id, "user_id": user_id}
            response = sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info(f"Sent crawl task {task_id} to SQS queue")
            return response
        except Exception as e:
            logger.error(f"Error sending crawl task to SQS: {e}")
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