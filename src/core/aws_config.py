"""
AWS Configuration loader
"""

import json
import os
from typing import Dict, Any

class AWSConfig:
    """AWS configuration loader from JSON file."""
    
    def __init__(self, config_file: str = "aws_credentials.json"):
        """Initialize AWS configuration."""
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Fallback to environment variables
                return {
                    "aws": {
                        "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                        "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                        "region": os.getenv("AWS_REGION", "ap-south-1")
                    },
                    "sqs": {
                        "queue_name": "stock-market-crawler-tasks"
                    },
                    "lambda": {
                        "function_name": "stock-market-crawler-background-processor"
                    },
                    "s3": {
                        "bucket_name": os.getenv("S3_BUCKET_NAME", "stock-market-crawler-data"),
                        "documents_prefix": "documents/",
                        "crawled_data_prefix": "crawled_data/"
                    }
                }
        except Exception as e:
            print(f"Warning: Could not load AWS config file: {e}")
            return {}
    
    @property
    def access_key_id(self) -> str:
        """Get AWS access key ID."""
        return self.config.get("aws", {}).get("access_key_id")
    
    @property
    def secret_access_key(self) -> str:
        """Get AWS secret access key."""
        return self.config.get("aws", {}).get("secret_access_key")
    
    @property
    def region(self) -> str:
        """Get AWS region."""
        return self.config.get("aws", {}).get("region", "ap-south-1")
    
    @property
    def sqs_queue_name(self) -> str:
        """Get SQS queue name."""
        return self.config.get("sqs", {}).get("queue_name", "stock-market-crawler-tasks")
    
    @property
    def lambda_function_name(self) -> str:
        """Get Lambda function name."""
        return self.config.get("lambda", {}).get("function_name", "stock-market-crawler-background-processor")
    
    @property
    def s3_bucket_name(self) -> str:
        """Get S3 bucket name."""
        return self.config.get("s3", {}).get("bucket_name", "stock-market-crawler-data")
    
    @property
    def s3_documents_prefix(self) -> str:
        """Get S3 documents prefix."""
        return self.config.get("s3", {}).get("documents_prefix", "documents/")
    
    @property
    def s3_crawled_data_prefix(self) -> str:
        """Get S3 crawled data prefix."""
        return self.config.get("s3", {}).get("crawled_data_prefix", "crawled_data/")
    
    def get_sqs_queue_url(self) -> str:
        """Get SQS queue URL."""
        # For now, return None to disable SQS operations until queue is properly configured
        # This prevents the InvalidAddress error
        return None
    
    def get_lambda_function_arn(self) -> str:
        """Get Lambda function ARN."""
        return f"arn:aws:lambda:{self.region}:*:function:{self.lambda_function_name}"

# Global AWS config instance
aws_config = AWSConfig() 