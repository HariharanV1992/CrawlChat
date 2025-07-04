"""
Simple Lambda handler for AWS deployment.
This bypasses the problematic logging setup.
"""

import json
import logging
import os
from mangum import Mangum

# Configure basic logging for Lambda
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the FastAPI app
from main import app

# Create Mangum handler for AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda handler for FastAPI application."""
    try:
        logger.info(f"Received event: {json.dumps(event, indent=2)}")
        
        # Handle the request through Mangum
        response = handler(event, context)
        
        logger.info(f"Response status: {response.get('statusCode', 'unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            }
        } 