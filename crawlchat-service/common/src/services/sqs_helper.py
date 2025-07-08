import boto3
import os
import json

SQS_QUEUE_NAME = os.getenv("CRAWLCHAT_SQS_QUEUE", "crawlchat-crawl-tasks")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

sqs_client = boto3.client("sqs", region_name=AWS_REGION)

class SQSHelper:
    def __init__(self, queue_name=SQS_QUEUE_NAME):
        self.queue_name = queue_name
        self.queue_url = self.get_or_create_queue()

    def get_or_create_queue(self):
        try:
            response = sqs_client.get_queue_url(QueueName=self.queue_name)
            return response["QueueUrl"]
        except sqs_client.exceptions.QueueDoesNotExist:
            response = sqs_client.create_queue(QueueName=self.queue_name)
            return response["QueueUrl"]

    def send_crawl_task(self, task_id, user_id):
        message = {"task_id": task_id, "user_id": user_id}
        sqs_client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message)
        )

    def receive_messages(self, max_messages=1):
        response = sqs_client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=10
        )
        return response.get("Messages", [])

    def delete_message(self, receipt_handle):
        sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

sqs_helper = SQSHelper() 