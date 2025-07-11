import json
import logging
import os
from typing import Dict, Any, Optional
import sys
import uuid
from datetime import datetime
import boto3
import motor.motor_asyncio
import asyncio

# Add the crawler path to sys.path
current_dir = os.path.dirname(__file__)
crawler_path = os.path.join(current_dir, 'src', 'crawler')
sys.path.insert(0, crawler_path)
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_QUEUE_NAME = os.getenv("CRAWLCHAT_SQS_QUEUE", "crawlchat-crawl-tasks")
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("DB_NAME", "stock_market_crawler")
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY", "")

# Initialize AWS clients
sqs_client = boto3.client("sqs", region_name=AWS_REGION)

# Import enhanced crawler service
try:
    from src.crawler.enhanced_crawler_service import EnhancedCrawlerService
    logger.info("Successfully imported EnhancedCrawlerService")
except ImportError as e:
    logger.error(f"Failed to import EnhancedCrawlerService: {e}")
    # Try alternative import path
    try:
        from crawler.enhanced_crawler_service import EnhancedCrawlerService
        logger.info("Successfully imported EnhancedCrawlerService with alternative path")
    except ImportError as e2:
        logger.error(f"Failed to import EnhancedCrawlerService with alternative path: {e2}")
        EnhancedCrawlerService = None

class SQSHelper:
    def __init__(self, queue_name=SQS_QUEUE_NAME):
        self.queue_name = queue_name
        self.queue_url = self.get_queue_url()

    def get_queue_url(self):
        """Get the queue URL. Assumes the queue already exists."""
        try:
            response = sqs_client.get_queue_url(QueueName=self.queue_name)
            queue_url = response["QueueUrl"]
            logger.info(f"Successfully got queue URL for {self.queue_name}")
            return queue_url
        except sqs_client.exceptions.QueueDoesNotExist:
            error_msg = f"SQS queue '{self.queue_name}' does not exist."
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error getting queue URL for {self.queue_name}: {e}"
            logger.error(error_msg)
            raise

    def send_crawl_task(self, task_id, user_id):
        """Send a crawl task message to SQS."""
        try:
            message = {"task_id": task_id, "user_id": user_id}
            message_body = json.dumps(message)
            
            response = sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body
            )
            
            logger.info(f"Sent crawl task {task_id} to SQS queue")
            return response
            
        except Exception as e:
            error_msg = f"Error sending crawl task to SQS: {e}"
            logger.error(error_msg)
            raise

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB."""
        if self.is_connected():
            logger.info("MongoDB already connected")
            return
            
        try:
            logger.info("Connecting to MongoDB...")
            
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=1,
                minPoolSize=0,
                maxIdleTimeMS=30000,
                retryWrites=True,
                retryReads=True
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            self.db = self.client[MONGODB_DB]
            logger.info(f"MongoDB connected successfully to database: {MONGODB_DB}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        return self.client is not None and self.db is not None

    def get_collection(self, name: str):
        """Get a collection with lazy connection."""
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db[name]

# Initialize services
sqs_helper = None
mongodb = None

try:
    sqs_helper = SQSHelper()
    logger.info("SQS helper initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize SQS helper: {e}")

try:
    mongodb = MongoDB()
    logger.info("MongoDB helper initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB helper: {e}")

async def store_crawl_task(task_id: str, url: str, max_doc_count: int, user_id: str = "default") -> bool:
    """Store crawl task in MongoDB."""
    try:
        if not mongodb:
            logger.error("MongoDB not available")
            return False
            
        await mongodb.connect()
        collection = mongodb.get_collection("crawl_tasks")
        
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
        if not mongodb:
            logger.error("MongoDB not available")
            return False
            
        await mongodb.connect()
        collection = mongodb.get_collection("crawl_tasks")
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result:
            update_data["result"] = result
            
            # Extract progress information from result
            if isinstance(result, dict):
                documents_found = result.get('documents_found', 0)
                total_documents = result.get('total_documents', 0)
                total_pages = result.get('total_pages', 0)
                
                # Update progress fields for UI compatibility
                update_data["progress"] = {
                    "documents_downloaded": documents_found,
                    "pages_crawled": total_pages,
                    "total_documents": total_documents,
                    "total_pages": total_pages,
                    "current_document": documents_found,
                    "current_page": total_pages
                }
                
                # Also update the legacy fields for compatibility
                update_data["documents_downloaded"] = documents_found
                update_data["pages_crawled"] = total_pages
            
        await collection.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        logger.info(f"Updated task {task_id} status to {status} with {result.get('documents_found', 0) if result else 0} documents")
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
        
        # Get task details from MongoDB
        try:
            if not mongodb:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Database not available'}, ensure_ascii=False)
                }
            
            # Use a single event loop for all async operations
            async def get_task_and_crawl():
                await mongodb.connect()
                collection = mongodb.get_collection("crawl_tasks")
                
                task = await collection.find_one({"task_id": task_id})
                if not task:
                    return None, None, None, None
                
                url = task['url']
                max_doc_count = task['max_doc_count']
                user_id = task['user_id']
                
                return task, url, max_doc_count, user_id
            
            # Run the async function
            task, url, max_doc_count, user_id = asyncio.run(get_task_and_crawl())
            
            if not task:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Task not found'}, ensure_ascii=False)
                }
            
            # Initialize EnhancedCrawlerService
            if EnhancedCrawlerService and SCRAPINGBEE_API_KEY:
                crawler = EnhancedCrawlerService(api_key=SCRAPINGBEE_API_KEY)
                
                # Start crawling
                logger.info(f"Starting enhanced crawling for task {task_id} with URL: {url}, max_doc_count: {max_doc_count}")
                try:
                    result = crawler.crawl_with_max_docs(url, max_doc_count=max_doc_count)
                    logger.info(f"Enhanced crawling for task {task_id} completed: {len(result.get('documents', []))} documents found")
                    
                    # Update task status to completed
                    asyncio.run(update_task_status(task_id, "completed", result))
                    
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'task_id': task_id,
                            'status': 'completed',
                            'message': f'Crawl completed successfully! {len(result.get("documents", []))} document(s) downloaded and ready for analysis.',
                            'result': result
                        }, ensure_ascii=False)
                    }
                except Exception as e:
                    logger.error(f"Enhanced crawling for task {task_id} failed: {e}")
                    # Update task status to failed
                    asyncio.run(update_task_status(task_id, "failed", {"error": str(e)}))
                    return {
                        'statusCode': 500,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': f'Enhanced crawling failed: {str(e)}'}, ensure_ascii=False)
                    }
            else:
                logger.error("EnhancedCrawlerService or SCRAPINGBEE_API_KEY not available, cannot start crawling.")
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Enhanced crawling service not available'}, ensure_ascii=False)
                }
        except Exception as e:
            logger.error(f"Error in handle_http_task_start: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Task start failed: {str(e)}'}, ensure_ascii=False)
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
        async def get_task_status():
            if not mongodb:
                return None
            
            await mongodb.connect()
            collection = mongodb.get_collection("crawl_tasks")
            return await collection.find_one({"task_id": task_id})
        
        try:
            task = asyncio.run(get_task_status())
            
            if not task:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Task not found'}, ensure_ascii=False)
                }
            if not task:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Task not found'}, ensure_ascii=False)
                }
            
            # Convert ObjectId to string for JSON serialization
            task['_id'] = str(task['_id'])
            
            # Ensure progress field exists with proper structure
            if 'progress' not in task:
                task['progress'] = {
                    "documents_downloaded": 0,
                    "pages_crawled": 0,
                    "total_documents": 0,
                    "total_pages": 0,
                    "current_document": 0,
                    "current_page": 0
                }
            
            # Update progress from result if available
            if 'result' in task and isinstance(task['result'], dict):
                result = task['result']
                documents_found = result.get('documents_found', 0)
                total_documents = result.get('total_documents', 0)
                total_pages = result.get('total_pages', 0)
                
                task['progress'].update({
                    "documents_downloaded": documents_found,
                    "pages_crawled": total_pages,
                    "total_documents": total_documents,
                    "total_pages": total_pages,
                    "current_document": documents_found,
                    "current_page": total_pages
                })
            
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
    
    except Exception as e:
        logger.error(f"Error in handle_http_task_status: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Task status check failed: {str(e)}'}, ensure_ascii=False)
        } 