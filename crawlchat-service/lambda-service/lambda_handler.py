"""
Lambda handler for CrawlChat API and Crawler functions
"""

import json
import logging
import os
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Log initialization info
logger.info(f"Lambda handler initialized - Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"AWS_LAMBDA_FUNCTION_NAME: {os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'NOT_SET')}")

from common.src.services.crawler_service import crawler_service
from common.src.core.database import mongodb
import asyncio

def lambda_handler(event, context):
    """
    Routes API Gateway events to FastAPI (via Mangum), direct events to crawler logic, and SQS events to batch handler.
    """
    logger.info(f"Lambda handler started - Event type: {type(event)}")
    logger.info(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'not a dict'}")
    
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # API Gateway proxy event
        if 'httpMethod' in event or 'requestContext' in event:
            logger.info("Routing to FastAPI application")
            return handle_api_gateway_request(event, context)
        # SQS batch event
        elif 'Records' in event:
            logger.info("Routing to SQS batch handler")
            return process_sqs_message(event, context)
        # Direct Lambda invoke (crawler)
        else:
            logger.info("Routing to crawler handler")
            return handle_crawler_request(event, context)
    except Exception as e:
        error_msg = f"Error in lambda handler: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'traceback': traceback.format_exc()})
        }

def handle_api_gateway_request(event, context):
    """Handle API Gateway requests by routing to FastAPI application."""
    try:
        logger.info("Importing FastAPI app...")
        
        # Import FastAPI app
        from main import app
        logger.info("FastAPI app imported successfully")
        
        # Convert API Gateway event to ASGI scope
        scope = {
            'type': 'http',
            'http_version': '1.1',
            'method': event.get('httpMethod', 'GET'),
            'scheme': 'https',
            'server': ('api.crawlchat.site', 443),
            'path': event.get('path', '/'),
            'query_string': event.get('queryStringParameters', {}),
            'headers': [(k.lower().encode(), v.encode()) for k, v in event.get('headers', {}).items()],
            'body': event.get('body', '').encode() if event.get('body') else b'',
            'client': ('127.0.0.1', 0),
            'asgi': {'version': '3.0'}
        }
        
        logger.info("Creating Mangum handler...")
        
        # Create ASGI application
        from mangum import Mangum
        handler = Mangum(app, lifespan="off")
        
        logger.info("Handling the request...")
        
        # Handle the request
        response = handler(event, context)
        logger.info("Request handled successfully")
        return response
        
    except Exception as e:
        error_msg = f"Error handling API Gateway request: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'message': str(e), 'traceback': traceback.format_exc()})
        }

def handle_crawler_request(event, context):
    """Handle direct crawler requests."""
    try:
        logger.info("Importing crawler modules...")
        
        from crawler.advanced_crawler import AdvancedCrawler, CrawlScenarios
        from crawler.enhanced_scrapingbee_manager import ProxyMode, JavaScriptScenarios
        
        logger.info("Crawler modules imported successfully")
        
        # Extract parameters
        url = event.get('url')
        if not url:
            logger.error("URL is required but not provided")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'URL is required'})
            }
        
        logger.info(f"Processing URL: {url}")
        
        content_type = event.get('content_type', 'generic')
        use_js_scenario = event.get('use_js_scenario', False)
        js_scenario = event.get('js_scenario')
        take_screenshot = event.get('take_screenshot', False)
        download_file = event.get('download_file', False)
        country_code = event.get('country_code', 'in')  # Default to India for ap-south-1 region
        force_mode = event.get('force_mode')
        
        # Initialize enhanced crawler
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            logger.error("SCRAPINGBEE_API_KEY not configured")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SCRAPINGBEE_API_KEY not configured'})
            }
        
        logger.info("Initializing AdvancedCrawler...")
        
        crawler = AdvancedCrawler(api_key)
        
        # Set country code if specified
        if country_code:
            crawler.set_country_code(country_code)
        
        # Determine operation based on parameters
        if download_file:
            logger.info(f"Downloading file from {url}")
            result = crawler.download_file(url)
            
        elif take_screenshot:
            logger.info(f"Taking screenshot of {url}")
            full_page = event.get('full_page', True)
            selector = event.get('selector')
            result = crawler.take_screenshot(url, full_page, selector)
            
        elif use_js_scenario or js_scenario:
            logger.info(f"Crawling {url} with JavaScript scenario")
            if not js_scenario:
                # Use pre-built scenario based on content type
                if content_type == 'news':
                    js_scenario = CrawlScenarios.news_site_scenario()
                elif content_type == 'ecommerce':
                    js_scenario = CrawlScenarios.ecommerce_scenario()
                elif content_type == 'financial':
                    js_scenario = CrawlScenarios.financial_site_scenario()
                else:
                    js_scenario = CrawlScenarios.blog_scenario()
            
            result = crawler.crawl_with_js_scenario(url, js_scenario, content_type)
            
        else:
            logger.info(f"Crawling {url} with progressive proxy strategy")
            result = crawler.crawl_url(url, content_type)
        
        # Get usage statistics
        stats = crawler.get_usage_stats()
        
        # Prepare response
        response_body = {
            'success': result.get('success', False),
            'url': url,
            'result': result,
            'usage_stats': stats,
            'progressive_strategy_used': not force_mode,
        }
        
        # Add cost analysis
        if 'cost_estimate' in stats:
            response_body['cost_analysis'] = {
                'total_cost': stats['cost_estimate']['total_cost'],
                'credits_used': stats['cost_estimate']['credits_used'],
                'mode_costs': stats['cost_estimate']['mode_costs'],
            }
        
        # Clean up
        crawler.close()
        
        logger.info(f"Crawl completed successfully for {url}")
        return {
            'statusCode': 200,
            'body': json.dumps(response_body, default=str)
        }
        
    except Exception as e:
        error_msg = f"Error in crawler handler: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Try to get partial stats if crawler was initialized
        partial_stats = {}
        try:
            if 'crawler' in locals():
                partial_stats = crawler.get_usage_stats()
                crawler.close()
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'partial_stats': partial_stats
            })
        }

def process_sqs_message(event, context):
    try:
        logger.info(f"Processing SQS event with {len(event.get('Records', []))} records")

        # Initialize MongoDB connection
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mongodb.connect())
        logger.info("MongoDB connected successfully")

        for record in event.get('Records', []):
            try:
                logger.info(f"Processing SQS record")

                # Parse SQS message
                message_body = json.loads(record['body'])
                task_id = message_body.get('task_id')
                user_id = message_body.get('user_id')

                # Fetch the full task from DB
                task = loop.run_until_complete(crawler_service.get_task_status(task_id))
                if not task or not getattr(task, 'url', None):
                    logger.error(f"Task {task_id} not found or URL missing!")
                    continue

                # Actually run the crawl
                loop.run_until_complete(crawler_service._run_crawl_task(task))

            except Exception as e:
                error_msg = f"Error processing SQS record: {e}"
                logger.error(error_msg, exc_info=True)

        logger.info("Processed all records")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processed all records'})
        }

    except Exception as e:
        error_msg = f"Error in SQS handler: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'traceback': traceback.format_exc()})
        }

# Example functions for testing
def example_news_site_crawl():
    """Example: Crawl a news site with JavaScript scenario."""
    event = {
        'url': 'https://example-news.com',
        'content_type': 'news',
        'use_js_scenario': True,
        'take_screenshot': False
    }
    return lambda_handler(event, None)

def example_ecommerce_crawl():
    """Example: Crawl an e-commerce site with JavaScript scenario."""
    event = {
        'url': 'https://example-store.com',
        'content_type': 'ecommerce',
        'use_js_scenario': True,
        'take_screenshot': False
    }
    return lambda_handler(event, None)

def example_financial_crawl():
    """Example: Crawl a financial site with JavaScript scenario."""
    event = {
        'url': 'https://example-financial.com',
        'content_type': 'financial',
        'use_js_scenario': True,
        'take_screenshot': False
    }
    return lambda_handler(event, None)

def example_screenshot():
    """Example: Take a screenshot of a webpage."""
    event = {
        'url': 'https://example.com',
        'take_screenshot': True,
        'full_page': True
    }
    return lambda_handler(event, None)

def example_file_download():
    """Example: Download a file from a URL."""
    event = {
        'url': 'https://example.com/document.pdf',
        'download_file': True
    }
    return lambda_handler(event, None)

# Export the handler function for Lambda
handler = lambda_handler 