"""
AWS Background Service for handling background tasks using AWS SQS and Lambda
"""

import json
import logging
import boto3
import os
from typing import Dict, Any, Optional
from ..core.aws_config import aws_config
from ..core.exceptions import BackgroundServiceError
from ..services.storage_service import get_storage_service
import time

logger = logging.getLogger(__name__)

class AWSBackgroundService:
    """AWS-based background task processing service."""
    
    def __init__(self):
        """Initialize AWS background service."""
        self.sqs_client = None
        self.lambda_client = None
        self.enabled = self._initialize_aws_clients()
    
    def _initialize_aws_clients(self) -> bool:
        """Initialize AWS clients."""
        try:
            # Check if running in Lambda environment
            is_lambda = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
            
            if is_lambda:
                # In Lambda, use IAM role (no credentials needed)
                logger.info("Running in Lambda environment, using IAM role for AWS access")
                self.sqs_client = boto3.client('sqs', region_name=aws_config.region)
                self.lambda_client = boto3.client('lambda', region_name=aws_config.region)
            else:
                # In local environment, check for credentials
                if not aws_config.access_key_id or not aws_config.secret_access_key:
                    logger.warning("AWS credentials not configured, disabling background service")
                    return False
                    
                # Use credentials from config file
                self.sqs_client = boto3.client(
                    'sqs',
                    aws_access_key_id=aws_config.access_key_id,
                    aws_secret_access_key=aws_config.secret_access_key,
                    region_name=aws_config.region
                )
                
                self.lambda_client = boto3.client(
                    'lambda',
                    aws_access_key_id=aws_config.access_key_id,
                    aws_secret_access_key=aws_config.secret_access_key,
                    region_name=aws_config.region
                )
            
            # Test SQS connection only if queue URL is available
            queue_url = aws_config.get_sqs_queue_url()
            if queue_url:
                self.sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['QueueArn']
                )
            else:
                logger.info("SQS queue URL not configured, background service will be limited")
            
            logger.info("AWS background service initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize AWS background service: {e}")
            return False
    
    def submit_task(self, task_type: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Submit a task to AWS SQS."""
        if not self.enabled:
            logger.warning("AWS background service disabled, task will not be processed")
            return None
        
        try:
            message_body = {
                "task_type": task_type,
                "task_data": task_data,
                "timestamp": str(int(time.time()))
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=aws_config.get_sqs_queue_url(),
                MessageBody=json.dumps(message_body)
            )
            
            task_id = response['MessageId']
            logger.info(f"Task submitted to SQS: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting task to SQS: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status from Lambda."""
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            # For now, return a basic status
            # In a real implementation, you'd query Lambda or DynamoDB for task status
            return {
                "task_id": task_id,
                "status": "submitted",
                "message": "Task submitted to AWS SQS"
            }
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if not self.enabled:
            return False
        
        try:
            # In a real implementation, you'd send a cancellation message
            logger.info(f"Task cancellation requested for: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get AWS service statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            # Get SQS queue attributes
            queue_attrs = self.sqs_client.get_queue_attributes(
                QueueUrl=aws_config.get_sqs_queue_url(),
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            return {
                "enabled": True,
                "sqs": {
                    "queue_url": aws_config.get_sqs_queue_url(),
                    "messages_available": queue_attrs['Attributes'].get('ApproximateNumberOfMessages', '0'),
                    "messages_in_flight": queue_attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', '0')
                },
                "lambda": {
                    "function_name": aws_config.lambda_function_name,
                    "function_arn": aws_config.get_lambda_function_arn()
                }
            }
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {"enabled": False, "error": str(e)}

# Global AWS background service instance
aws_background_service = AWSBackgroundService() 