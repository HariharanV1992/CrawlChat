"""
Lambda handler for FastAPI application using Mangum.
"""

import logging
import os
import sys
from mangum import Mangum

# Setup basic logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Check if static directory exists
    if not os.path.exists("static"):
        logger.warning("Static directory does not exist, creating it")
        os.makedirs("static", exist_ok=True)
    
    # Check if templates directory exists
    if not os.path.exists("templates"):
        logger.warning("Templates directory does not exist")
    
    # Import the FastAPI app from the local main.py
    from main import app
    logger.info("Successfully imported FastAPI app")
    
    # Create Mangum handler
    handler = Mangum(app, lifespan="off")
    logger.info("Successfully created Mangum handler")
    
    # Export the handler for Lambda
    lambda_handler = handler
    
except Exception as e:
    logger.error(f"Error during Lambda initialization: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Directory contents: {os.listdir('.')}")
    raise 