"""
S3 Cache Manager for storing site requirements and other cache data.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class S3CacheManager:
    """S3-based cache manager for storing site requirements and other data."""
    
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize S3 cache manager.
        
        Args:
            bucket_name: S3 bucket name (defaults to S3_BUCKET env var)
            region: AWS region (defaults to AWS_REGION env var)
        """
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET', 'crawlchat-data')
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client."""
        try:
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                logger.info("Initializing S3 client using IAM role")
                self.s3_client = boto3.client('s3', region_name=self.region)
            else:
                # Running locally - use default credential chain
                logger.info("Initializing S3 client using default credentials")
                self.s3_client = boto3.client('s3', region_name=self.region)
            
            logger.info(f"S3 cache manager initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def save_site_js_requirements(self, requirements: Dict[str, bool], key: str = "cache/site_js_requirements.json"):
        """
        Save site JS requirements to S3.
        
        Args:
            requirements: Dictionary of site requirements
            key: S3 object key
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping save")
            return False
        
        try:
            # Convert to JSON
            data = json.dumps(requirements, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType='application/json'
            )
            
            logger.info(f"Site JS requirements saved to S3: s3://{self.bucket_name}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save site JS requirements to S3: {e}")
            return False
    
    def load_site_js_requirements(self, key: str = "cache/site_js_requirements.json") -> Dict[str, bool]:
        """
        Load site JS requirements from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary of site requirements (empty if not found or error)
        """
        if not self.s3_client:
            logger.warning("S3 client not available, returning empty cache")
            return {}
        
        try:
            # Try to get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # Parse JSON data
            data = response['Body'].read().decode('utf-8')
            requirements = json.loads(data)
            
            logger.info(f"Site JS requirements loaded from S3: s3://{self.bucket_name}/{key}")
            return requirements
            
        except self.s3_client.exceptions.NoSuchKey:
            logger.info(f"Site JS requirements not found in S3: s3://{self.bucket_name}/{key}")
            return {}
        except Exception as e:
            logger.warning(f"Failed to load site JS requirements from S3: {e}")
            return {}
    
    def save_site_requirements(self, requirements: Dict[str, str], key: str = "cache/site_requirements.json"):
        """
        Save site requirements to S3.
        
        Args:
            requirements: Dictionary of site requirements (domain -> mode)
            key: S3 object key
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping save")
            return False
        
        try:
            # Convert to JSON
            data = json.dumps(requirements, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType='application/json'
            )
            
            logger.info(f"Site requirements saved to S3: s3://{self.bucket_name}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save site requirements to S3: {e}")
            return False
    
    def load_site_requirements(self, key: str = "cache/site_requirements.json") -> Dict[str, str]:
        """
        Load site requirements from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary of site requirements (empty if not found or error)
        """
        if not self.s3_client:
            logger.warning("S3 client not available, returning empty cache")
            return {}
        
        try:
            # Try to get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # Parse JSON data
            data = response['Body'].read().decode('utf-8')
            requirements = json.loads(data)
            
            logger.info(f"Site requirements loaded from S3: s3://{self.bucket_name}/{key}")
            return requirements
            
        except self.s3_client.exceptions.NoSuchKey:
            logger.info(f"Site requirements not found in S3: s3://{self.bucket_name}/{key}")
            return {}
        except Exception as e:
            logger.warning(f"Failed to load site requirements from S3: {e}")
            return {}
    
    def save_cache_data(self, data: Dict[str, Any], key: str):
        """
        Save generic cache data to S3.
        
        Args:
            data: Data to cache
            key: S3 object key
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping save")
            return False
        
        try:
            # Convert to JSON
            json_data = json.dumps(data, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            
            logger.info(f"Cache data saved to S3: s3://{self.bucket_name}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache data to S3: {e}")
            return False
    
    def load_cache_data(self, key: str) -> Dict[str, Any]:
        """
        Load generic cache data from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Cached data (empty dict if not found or error)
        """
        if not self.s3_client:
            logger.warning("S3 client not available, returning empty cache")
            return {}
        
        try:
            # Try to get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # Parse JSON data
            data = response['Body'].read().decode('utf-8')
            cache_data = json.loads(data)
            
            logger.info(f"Cache data loaded from S3: s3://{self.bucket_name}/{key}")
            return cache_data
            
        except self.s3_client.exceptions.NoSuchKey:
            logger.info(f"Cache data not found in S3: s3://{self.bucket_name}/{key}")
            return {}
        except Exception as e:
            logger.warning(f"Failed to load cache data from S3: {e}")
            return {}
    
    def delete_cache_data(self, key: str) -> bool:
        """
        Delete cache data from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping delete")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            logger.info(f"Cache data deleted from S3: s3://{self.bucket_name}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cache data from S3: {e}")
            return False 