import json
import logging
import os
from typing import Dict, Any, Optional
import sys
import uuid
from datetime import datetime

# Add the src directory to the Python path
sys.path.append('/var/task/src')

try:
    from services.sqs_helper import SQSHelper
    from core.database import mongodb
    from core.config import config
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    SQSHelper = None
    mongodb = None
    config = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
sqs_helper = None
if SQSHelper:
    try:
        sqs_helper = SQSHelper()
        logger.info("SQS helper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SQS helper: {e}")

def get_mongodb():
    """Get MongoDB connection."""
    if not mongodb:
        logger.error("MongoDB not available")
        return None
    return mongodb

async def store_crawl_task(task_id: str, url: str, max_doc_count: int, user_id: str = "default") -> bool:
    """Store crawl task in MongoDB."""
    try:
        db = get_mongodb()
        if not db:
            return False
            
        await db.connect()
        collection = db.get_collection("crawl_tasks")
        
        task_data = {
            "task_id": task_id,
            "url": url,
            "max_doc_count": max_doc_count,
            "user_id": user_id,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await collection.insert_one(task_data)
        logger.info(f"Stored crawl task {task_id} in MongoDB")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store crawl task: {e}")
        return False

async def update_task_status(task_id: str, status: str, result: Dict = None):
    """Update task status in MongoDB."""
    try:
        db = get_mongodb()
        if not db:
            return False
            
        await db.connect()
        collection = db.get_collection("crawl_tasks")
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result:
            update_data["result"] = result
            
        await collection.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        logger.info(f"Updated task {task_id} status to {status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        return False

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for crawler service.
    
    This handler creates crawl tasks and sends them to SQS queue for processing.
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str, ensure_ascii=False)}")
        
        # Check if this is a direct invocation or HTTP API Gateway event
        if 'httpMethod' in event:
            # HTTP API Gateway event
            return handle_http_event(event)
        else:
            # Direct invocation event
            return handle_direct_invocation(event)
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'}, ensure_ascii=False)
        }

def handle_direct_invocation(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct Lambda invocation (from AWS CLI)."""
    try:
        # Extract parameters from direct event
        url = event.get('url')
        max_doc_count = event.get('max_doc_count', 1)
        user_id = event.get('user_id', 'default')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'URL parameter is required'}, ensure_ascii=False)
            }
        
        # Ensure max_doc_count is an integer
        try:
            max_doc_count = int(max_doc_count)
        except (ValueError, TypeError):
            max_doc_count = 1
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"Creating crawl task {task_id} for URL: {url}, max_doc_count: {max_doc_count}")
        
        # Store task in MongoDB
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(store_crawl_task(task_id, url, max_doc_count, user_id))
            if not success:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Failed to store task in database'}, ensure_ascii=False)
                }
        finally:
            loop.close()
        
        # Send task to SQS queue
        if sqs_helper:
            try:
                sqs_helper.send_crawl_task(task_id, user_id)
                logger.info(f"Sent crawl task {task_id} to SQS queue")
            except Exception as e:
                logger.error(f"Failed to send task to SQS: {e}")
                # Update task status to failed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(update_task_status(task_id, "failed", {"error": str(e)}))
                finally:
                    loop.close()
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Failed to queue task: {str(e)}'}, ensure_ascii=False)
                }
        else:
            logger.warning("SQS helper not available, task not queued")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'task_id': task_id,
                'status': 'queued',
                'message': 'Crawl task created and queued for processing'
            }, ensure_ascii=False)
        }
    
    except Exception as e:
        logger.error(f"Error in handle_direct_invocation: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Task creation failed: {str(e)}'}, ensure_ascii=False)
        }

def handle_http_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP API Gateway events."""
    try:
        # Get HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Handle different endpoints
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'healthy', 'service': 'crawler_service'}, ensure_ascii=False)
            }
        
        elif path == '/tasks' and http_method == 'POST':
            return handle_http_task_creation(event)
        
        elif path.startswith('/tasks/') and path.endswith('/start') and http_method == 'POST':
            return handle_http_task_start(event)
        
        elif path.startswith('/tasks/') and http_method == 'GET':
            return handle_http_task_status(event)
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'}, ensure_ascii=False)
            }
    
    except Exception as e:
        logger.error(f"Error in handle_http_event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'HTTP handler error: {str(e)}'}, ensure_ascii=False)
        }

def handle_http_task_creation(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP task creation requests."""
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        url = body.get('url')
        max_doc_count = body.get('max_doc_count', 1)
        user_id = body.get('user_id', 'default')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'URL parameter is required'}, ensure_ascii=False)
            }
        
        # Ensure max_doc_count is an integer
        try:
            max_doc_count = int(max_doc_count)
        except (ValueError, TypeError):
            max_doc_count = 1
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"Creating HTTP crawl task {task_id} for URL: {url}, max_doc_count: {max_doc_count}")
        
        # Store task in MongoDB
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(store_crawl_task(task_id, url, max_doc_count, user_id))
            if not success:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Failed to store task in database'}, ensure_ascii=False)
                }
        finally:
            loop.close()
        
        # Send task to SQS queue
        if sqs_helper:
            try:
                sqs_helper.send_crawl_task(task_id, user_id)
                logger.info(f"Sent crawl task {task_id} to SQS queue")
            except Exception as e:
                logger.error(f"Failed to send task to SQS: {e}")
                # Update task status to failed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(update_task_status(task_id, "failed", {"error": str(e)}))
                finally:
                    loop.close()
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Failed to queue task: {str(e)}'}, ensure_ascii=False)
                }
        else:
            logger.warning("SQS helper not available, task not queued")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'task_id': task_id,
                'status': 'queued',
                'message': 'Crawl task created and queued for processing'
            }, ensure_ascii=False)
        }
    
    except Exception as e:
        logger.error(f"Error in handle_http_task_creation: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Task creation failed: {str(e)}'}, ensure_ascii=False)
        }

def handle_http_task_start(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP task start requests."""
    try:
        # Extract task ID from path
        path = event.get('path', '')
        task_id = path.split('/tasks/')[1].split('/start')[0]
        
        logger.info(f"Starting HTTP task {task_id}")
        
        # Send task to SQS queue for processing
        if sqs_helper:
            try:
                sqs_helper.send_crawl_task(task_id, "default")
                logger.info(f"Sent crawl task {task_id} to SQS queue")
                
                # Update task status to queued
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(update_task_status(task_id, "queued"))
                finally:
                    loop.close()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'task_id': task_id,
                        'status': 'queued',
                        'message': 'Task queued for processing'
                    }, ensure_ascii=False)
                }
            except Exception as e:
                logger.error(f"Failed to send task to SQS: {e}")
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Failed to queue task: {str(e)}'}, ensure_ascii=False)
                }
        else:
            logger.warning("SQS helper not available")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'SQS service not available'}, ensure_ascii=False)
            }
    
    except Exception as e:
        logger.error(f"Error in handle_http_task_start: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Task start failed: {str(e)}'}, ensure_ascii=False)
        }

def handle_http_task_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP task status requests."""
    try:
        # Extract task ID from path
        path = event.get('path', '')
        task_id = path.split('/tasks/')[1]
        
        logger.info(f"Getting status for task {task_id}")
        
        # Get task status from MongoDB
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db = get_mongodb()
            if not db:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Database not available'}, ensure_ascii=False)
                }
            
            loop.run_until_complete(db.connect())
            collection = db.get_collection("crawl_tasks")
            
            task = loop.run_until_complete(collection.find_one({"task_id": task_id}))
            if not task:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Task not found'}, ensure_ascii=False)
                }
            
            # Convert ObjectId to string for JSON serialization
            task['_id'] = str(task['_id'])
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(task, default=str, ensure_ascii=False)
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Failed to get task status: {str(e)}'}, ensure_ascii=False)
            }
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error in handle_http_task_status: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Task status check failed: {str(e)}'}, ensure_ascii=False)
        } 