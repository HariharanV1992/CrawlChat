"""
Lambda handler for FastAPI application using Mangum.
"""

import logging
import os
import sys
import json
import asyncio
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
    
    # Create Mangum handler for API Gateway events
    mangum_handler = Mangum(app, lifespan="off")
    logger.info("Successfully created Mangum handler")
    
    # Import services for SQS processing
    from common.src.services.crawler_service import crawler_service
    from common.src.core.database import mongodb
    logger.info("Successfully imported crawler service and database")
    
except Exception as e:
    logger.error(f"Error during Lambda initialization: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Directory contents: {os.listdir('.')}")
    raise

def lambda_handler(event, context):
    """
    Lambda handler that can process both API Gateway and SQS events.
    """
    logger.info(f"Lambda handler called with event type: {type(event)}")
    logger.info(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'not a dict'}")
    
    # Check if this is an SQS event
    if isinstance(event, dict) and 'Records' in event:
        # This is an SQS event
        logger.info("Processing SQS event")
        return process_sqs_event(event, context)
    else:
        # This is an API Gateway event (or other HTTP event)
        logger.info("Processing API Gateway event")
        return process_api_gateway_event(event, context)

def process_sqs_event(event, context):
    """
    Process SQS events for background crawl tasks.
    """
    logger.info(f"[SQS] Received event with {len(event.get('Records', []))} records")
    
    if not event.get("Records"):
        logger.warning("[SQS] No records found in event")
        return {"statusCode": 200, "body": "No records to process"}
    
    processed_count = 0
    
    for i, record in enumerate(event.get("Records", [])):
        try:
            logger.info(f"[SQS] Processing record {i+1}/{len(event['Records'])}")
            logger.info(f"[SQS] Record body: {record.get('body', 'NO_BODY')}")
            
            body = json.loads(record["body"])
            task_id = body["task_id"]
            user_id = body.get("user_id")
            logger.info(f"[SQS] Processing crawl task: {task_id} for user: {user_id}")
            
            # Run the crawl synchronously
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_crawl(task_id))
            logger.info(f"[SQS] Finished crawl for task: {task_id}")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"[SQS] Error processing record {i+1}: {e}")
            import traceback
            logger.error(f"[SQS] Traceback: {traceback.format_exc()}")
    
    logger.info(f"[SQS] Processed {processed_count}/{len(event['Records'])} records successfully")
    return {"statusCode": 200, "body": f"Processed {processed_count} crawl tasks"}

async def run_crawl(task_id):
    """
    Run a crawl task.
    """
    try:
        # Ensure DB is connected
        if not mongodb.is_connected():
            await mongodb.connect()
            logger.info("[SQS] Connected to database")
        
        # Fetch the task and run the crawl
        task = await crawler_service.get_task_status(task_id)
        if not task:
            logger.error(f"[SQS] Task {task_id} not found in DB")
            return
        
        logger.info(f"[SQS] Starting crawl for task: {task_id}")
        # Actually run the crawl (synchronously)
        await crawler_service._run_crawl_task(task)
        logger.info(f"[SQS] Completed crawl for task: {task_id}")
        
    except Exception as e:
        logger.error(f"[SQS] Error running crawl for task {task_id}: {e}")
        import traceback
        logger.error(f"[SQS] Traceback: {traceback.format_exc()}")

def process_api_gateway_event(event, context):
    """
    Process API Gateway events using Mangum.
    """
    try:
        logger.info("Processing API Gateway event with Mangum")
        return mangum_handler(event, context)
    except Exception as e:
        logger.error(f"Error processing API Gateway event: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a proper error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": "2025-07-08T10:30:00Z"
            })
        } 