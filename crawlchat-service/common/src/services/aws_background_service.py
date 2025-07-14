"""
AWS Background Service for handling asynchronous operations
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from ..core.aws_config import aws_config

logger = logging.getLogger(__name__)

class AWSBackgroundService:
    """Service for handling background AWS operations."""
    
    def __init__(self):
        """Initialize AWS background service."""
        self.region = aws_config.region
        self.lambda_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients."""
        try:
            # Use boto3's default credential chain
            session = boto3.Session()
            self.lambda_client = session.client('lambda', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.lambda_client = None
    
    def invoke_lambda_function(self, payload: Dict[str, Any], function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke AWS Lambda function synchronously.
        
        Args:
            payload: Data to send to Lambda function
            function_name: Lambda function name (optional, uses default if not provided)
            
        Returns:
            Response from Lambda function
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {"error": "Lambda client not initialized"}
        
        try:
            function_name = function_name or aws_config.lambda_function_name
            
            # Prepare the payload
            lambda_payload = {
                "body": json.dumps(payload),
                "headers": {
                    "Content-Type": "application/json"
                }
            }
            
            logger.info(f"Invoking Lambda function: {function_name}")
            logger.debug(f"Lambda payload: {lambda_payload}")
            
            # Invoke the Lambda function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',  # Synchronous invocation
                Payload=json.dumps(lambda_payload)
            )
            
            # Parse the response
            if response['StatusCode'] == 200:
                response_payload = json.loads(response['Payload'].read().decode('utf-8'))
                logger.info(f"Lambda function {function_name} invoked successfully")
                return response_payload
            else:
                logger.error(f"Lambda function {function_name} failed with status: {response['StatusCode']}")
                return {"error": f"Lambda invocation failed with status {response['StatusCode']}"}
                
        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_name}: {e}")
            return {"error": str(e)}
    
    def invoke_crawler_lambda(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke crawler Lambda function.
        
        Args:
            task_data: Crawler task data
            
        Returns:
            Response from crawler Lambda function
        """
        payload = {
            "action": "crawl",
            "data": task_data
        }
        return self.invoke_lambda_function(payload)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test AWS connection by listing Lambda functions.
        
        Returns:
            Connection test result
        """
        if not self.lambda_client:
            return {"status": "error", "message": "Lambda client not initialized"}
        
        try:
            # List Lambda functions to test connection
            response = self.lambda_client.list_functions(MaxItems=5)
            functions = [func['FunctionName'] for func in response.get('Functions', [])]
            
            return {
                "status": "success",
                "message": "AWS connection successful",
                "region": self.region,
                "available_functions": functions
            }
        except Exception as e:
            logger.error(f"AWS connection test failed: {e}")
            return {
                "status": "error",
                "message": f"AWS connection failed: {str(e)}",
                "region": self.region
            }

# Global instance
aws_background_service = AWSBackgroundService() 