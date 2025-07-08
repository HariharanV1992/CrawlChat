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

def create_default_settings_files():
    """Create default settings files in /tmp directory."""
    try:
        # Create /tmp directory if it doesn't exist
        os.makedirs("/tmp", exist_ok=True)
        
        # Default stock market settings
        stock_market_settings = {
            "crawler_settings": {
                "max_pages": 5,
                "delay": 2,
                "min_year": 2015,
                "max_year": 2025,
                "max_workers": 3,
                "use_selenium": False,  # Disable in Lambda
                "max_documents": 10,
                "min_file_size_bytes": 1000,
                "selenium_timeout": 30,
                "selenium_wait_time": 3,
                "max_retries": 3,
                "retry_delay": 5
            },
            "proxy_settings": {
                "use_proxy": True,
                "timeout": 30,
                "proxy_api_key": "",
                "proxy_method": "api_endpoint",
                "min_file_size": 1024,
                "output_dir": "/tmp/crawled_data",  # Use /tmp in Lambda
                "single_page_mode": False,
                "connection_limit": 100,
                "tcp_connector_limit": 50,
                "keepalive_timeout": 30,
                "enable_compression": True,
                "total_timeout": 1800,
                "page_timeout": 60,
                "request_timeout": 30,
                "max_pages_without_documents": 20,
                "relevant_keywords": [
                    "stock", "market", "financial", "investor", "earnings", "revenue",
                    "profit", "dividend", "share", "equity", "trading", "quote",
                    "annual", "quarterly", "report", "statement", "filing", "sec",
                    "board", "governance", "corporate", "news", "announcement"
                ],
                "exclude_patterns": [
                    "login", "admin", "private", "internal", "test", "dev",
                    "temp", "cache", "session", "cookie", "tracking", "advertisement",
                    "ad", "banner", "social", "facebook", "twitter", "linkedin",
                    "youtube", "instagram", "subscribe", "newsletter", "contact",
                    "about", "careers", "jobs", "support", "help", "faq"
                ],
                "document_extensions": [".pdf", ".doc", ".docx", ".xlsx", ".xls", ".ppt", ".pptx", ".txt", ".csv"],
                "scrapingbee_api_key": "",
                "scrapingbee_options": {
                    "premium_proxy": True,
                    "country_code": "us",
                    "block_ads": True,
                    "block_resources": False
                }
            },
            "keyword_settings": {
                "url_keywords": [],
                "content_keywords": [],
                "snippet_keywords": []
            }
        }
        
        # Default site JS requirements
        site_js_requirements = {
            "www.aboutamazon.com": True,
            "www.business-standard.com": False,
            "www.moneycontrol.com": False,
            "www.ndtv.com": False,
            "www.livemint.com": False,
            "www.financialexpress.com": False,
            "www.economictimes.indiatimes.com": False,
            "www.screener.in": False
        }
        
        # Save stock market settings
        with open("/tmp/stock_market_settings.json", "w") as f:
            json.dump(stock_market_settings, f, indent=2)
        logger.info("✅ Created /tmp/stock_market_settings.json")
        
        # Save site JS requirements
        with open("/tmp/site_js_requirements.json", "w") as f:
            json.dump(site_js_requirements, f, indent=2)
        logger.info("✅ Created /tmp/site_js_requirements.json")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating settings files: {e}")
        return False

try:
    # Create default settings files on Lambda initialization
    create_default_settings_files()
    
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