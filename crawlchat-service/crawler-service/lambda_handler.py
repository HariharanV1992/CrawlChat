"""
Lambda handler for FastAPI application using Mangum.
"""

import logging
import os
import sys
from pathlib import Path
from mangum import Mangum

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup basic logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Check if templates directory exists (for reference only)
    if not os.path.exists("templates"):
        logger.info("Templates directory not found (expected in Lambda)")
    
    # Import the FastAPI app
    from main import app
    logger.info("Successfully imported FastAPI app")
    
    # Create Mangum handler
    handler = Mangum(app, lifespan="off")
    logger.info("Successfully created Mangum handler")
    
except Exception as e:
    logger.error(f"Error during Lambda initialization: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Directory contents: {os.listdir('.')}")
    raise 