import os
import sys
import json
from pathlib import Path
import logging
import asyncio

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.services.crawler_service import crawler_service
from common.src.core.database import mongodb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Lambda handler for processing crawl jobs from SQS.
    """
    logger.info(f"[SQS Worker] Received event: {json.dumps(event)[:500]}")
    logger.info(f"[SQS Worker] Number of records: {len(event.get('Records', []))}")
    
    if not event.get("Records"):
        logger.warning("[SQS Worker] No records found in event")
        return {"statusCode": 200, "body": "No records to process"}
    
    loop = asyncio.get_event_loop()
    processed_count = 0
    
    for i, record in enumerate(event.get("Records", [])):
        try:
            logger.info(f"[SQS Worker] Processing record {i+1}/{len(event['Records'])}")
            logger.info(f"[SQS Worker] Record body: {record.get('body', 'NO_BODY')}")
            
            body = json.loads(record["body"])
            task_id = body["task_id"]
            user_id = body.get("user_id")
            logger.info(f"[SQS Worker] Processing crawl task: {task_id} for user: {user_id}")
            
            # Run the crawl synchronously
            loop.run_until_complete(run_crawl(task_id))
            logger.info(f"[SQS Worker] Finished crawl for task: {task_id}")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"[SQS Worker] Error processing record {i+1}: {e}")
            import traceback
            logger.error(f"[SQS Worker] Traceback: {traceback.format_exc()}")
    
    logger.info(f"[SQS Worker] Processed {processed_count}/{len(event['Records'])} records successfully")
    return {"statusCode": 200, "body": f"Processed {processed_count} crawl tasks"}

async def run_crawl(task_id):
    # Ensure DB is connected
    if not mongodb.is_connected():
        await mongodb.connect()
    # Fetch the task and run the crawl
    task = await crawler_service.get_task_status(task_id)
    if not task:
        logger.error(f"[SQS Worker] Task {task_id} not found in DB")
        return
    # Actually run the crawl (synchronously)
    await crawler_service._run_crawl_task(task) 