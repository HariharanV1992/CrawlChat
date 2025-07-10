import json
import logging
import os
from typing import Dict, Any, Optional
import sys

# Add the src directory to the Python path
sys.path.append('/var/task/src')

try:
    from crawler.enhanced_crawler_service import EnhancedCrawlerService
except ImportError as e:
    logging.error(f"Failed to import EnhancedCrawlerService: {e}")
    EnhancedCrawlerService = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the enhanced crawler service
crawler_service = None

def get_crawler_service() -> Optional[EnhancedCrawlerService]:
    """Get or create the enhanced crawler service instance."""
    global crawler_service
    if crawler_service is None and EnhancedCrawlerService:
        try:
            # Get API key from environment variable
            api_key = os.environ.get('SCRAPINGBEE_API_KEY')
            if not api_key:
                logger.warning("SCRAPINGBEE_API_KEY not found in environment variables")
                api_key = "demo_key"  # Fallback for testing
            
            crawler_service = EnhancedCrawlerService(api_key)
            logger.info("Enhanced crawler service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize crawler service: {e}")
            return None
    return crawler_service

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for enhanced crawler service.
    
    Supports both direct invocation and HTTP API Gateway events.
    
    Direct invocation format:
    {
        "url": "https://example.com",
        "max_doc_count": 3
    }
    
    HTTP API Gateway format:
    {
        "httpMethod": "POST",
        "path": "/crawl",
        "queryStringParameters": {
            "url": "https://example.com",
            "max_doc_count": "3"
        },
        "body": "{}"
    }
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
        
        logger.info(f"Starting direct crawl for URL: {url}, max_doc_count: {max_doc_count}")
        
        # Get crawler service and perform crawl
        service = get_crawler_service()
        if not service:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Crawler service not available'}, ensure_ascii=False)
            }
        
        result = service.crawl_with_max_docs(url, max_doc_count)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, default=str, ensure_ascii=False)
        }
    
    except Exception as e:
        logger.error(f"Error in handle_direct_invocation: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Crawl failed: {str(e)}'}, ensure_ascii=False)
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
                'body': json.dumps({'status': 'healthy', 'service': 'enhanced_crawler'}, ensure_ascii=False)
            }
        
        elif path == '/crawl' and http_method == 'POST':
            return handle_http_crawl_request(event)
        
        elif path.startswith('/tasks/') and path.endswith('/start') and http_method == 'POST':
            return handle_http_task_start(event)
        
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

def handle_http_crawl_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP crawl requests."""
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        url = query_params.get('url')
        max_doc_count = query_params.get('max_doc_count', '1')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'URL parameter is required'}, ensure_ascii=False)
            }
        
        # Parse max_doc_count
        try:
            max_doc_count = int(max_doc_count)
        except ValueError:
            max_doc_count = 1
        
        logger.info(f"Starting HTTP crawl for URL: {url}, max_doc_count: {max_doc_count}")
        
        # Get crawler service and perform crawl
        service = get_crawler_service()
        if not service:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Crawler service not available'}, ensure_ascii=False)
            }
        
        result = service.crawl_with_max_docs(url, max_doc_count)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, default=str, ensure_ascii=False)
        }
    
    except Exception as e:
        logger.error(f"Error in handle_http_crawl_request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'HTTP crawl failed: {str(e)}'}, ensure_ascii=False)
        }

def handle_http_task_start(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HTTP task start requests."""
    try:
        # Extract task ID from path
        path = event.get('path', '')
        task_id = path.split('/tasks/')[1].split('/start')[0]
        
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        max_doc_count = query_params.get('max_doc_count', '1')
        
        # Parse max_doc_count
        try:
            max_doc_count = int(max_doc_count)
        except ValueError:
            max_doc_count = 1
        
        # For now, we'll use a mock URL - in a real implementation, 
        # you'd get the task details from a database
        url = "https://example.com"  # This should come from task storage
        
        logger.info(f"Starting HTTP task {task_id} for URL: {url}, max_doc_count: {max_doc_count}")
        
        # Get crawler service and perform crawl
        service = get_crawler_service()
        if not service:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Crawler service not available'}, ensure_ascii=False)
            }
        
        result = service.crawl_with_max_docs(url, max_doc_count)
        
        # Add task information to result
        result['task_id'] = task_id
        result['status'] = 'completed'
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, default=str, ensure_ascii=False)
        }
    
    except Exception as e:
        logger.error(f"Error in handle_http_task_start: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'HTTP task start failed: {str(e)}'}, ensure_ascii=False)
        } 