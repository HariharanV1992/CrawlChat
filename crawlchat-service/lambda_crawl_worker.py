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
    loop = asyncio.get_event_loop()
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            task_id = body["task_id"]
            user_id = body.get("user_id")
            logger.info(f"[SQS Worker] Processing crawl task: {task_id} for user: {user_id}")
            # Run the crawl synchronously
            loop.run_until_complete(run_crawl(task_id))
            logger.info(f"[SQS Worker] Finished crawl for task: {task_id}")
        except Exception as e:
            logger.error(f"[SQS Worker] Error processing record: {e}")
    return {"statusCode": 200, "body": "Processed crawl tasks"}

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