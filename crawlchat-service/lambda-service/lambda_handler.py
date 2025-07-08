"""
Lambda handler for enhanced crawler with progressive proxy strategy
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crawler.advanced_crawler import AdvancedCrawler, CrawlScenarios
from crawler.enhanced_scrapingbee_manager import ProxyMode, JavaScriptScenarios

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Lambda handler for enhanced crawler with progressive proxy strategy.
    
    Expected event format:
    {
        "url": "https://example.com",
        "content_type": "generic",  // optional: "news", "ecommerce", "financial", "generic"
        "use_js_scenario": false,   // optional: whether to use JS scenario
        "js_scenario": {},          // optional: custom JS scenario
        "take_screenshot": false,   // optional: take screenshot
        "download_file": false,     // optional: download as file
        "country_code": "us",       // optional: proxy geolocation
        "force_mode": null          // optional: "standard", "premium", "stealth"
    }
    """
    
    try:
        # Parse event
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract parameters
        url = event.get('url')
        if not url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'URL is required'})
            }
        
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
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SCRAPINGBEE_API_KEY not configured'})
            }
        
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
                'mode_breakdown': stats['cost_estimate']['mode_costs'],
            }
        
        # Clean up
        crawler.close()
        
        logger.info(f"Crawl completed successfully for {url}")
        return {
            'statusCode': 200,
            'body': json.dumps(response_body, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda handler: {e}", exc_info=True)
        
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
                'partial_stats': partial_stats
            })
        }


def process_sqs_message(event, context):
    """
    Process SQS messages for batch crawling.
    
    Expected SQS message format:
    {
        "urls": ["https://example1.com", "https://example2.com"],
        "content_type": "generic",
        "batch_id": "unique-batch-id"
    }
    """
    
    try:
        logger.info(f"Processing SQS event: {json.dumps(event, default=str)}")
        
        results = []
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        
        if not api_key:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SCRAPINGBEE_API_KEY not configured'})
            }
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse SQS message
                message_body = json.loads(record['body'])
                urls = message_body.get('urls', [])
                content_type = message_body.get('content_type', 'generic')
                batch_id = message_body.get('batch_id', 'unknown')
                
                logger.info(f"Processing batch {batch_id} with {len(urls)} URLs")
                
                # Initialize crawler
                crawler = AdvancedCrawler(api_key)
                
                # Crawl all URLs
                batch_results = crawler.crawl_multiple_urls(urls, content_type)
                
                # Get batch statistics
                batch_stats = crawler.get_usage_stats()
                
                # Prepare batch result
                batch_result = {
                    'batch_id': batch_id,
                    'urls_processed': len(urls),
                    'successful_crawls': sum(1 for r in batch_results if r.get('success')),
                    'failed_crawls': sum(1 for r in batch_results if not r.get('success')),
                    'results': batch_results,
                    'usage_stats': batch_stats,
                }
                
                results.append(batch_result)
                crawler.close()
                
            except Exception as e:
                logger.error(f"Error processing SQS record: {e}")
                results.append({
                    'error': str(e),
                    'record': record
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed_batches': len(results),
                'results': results
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error processing SQS event: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Example usage functions for different scenarios
def example_news_site_crawl():
    """Example: Crawl news site with progressive strategy."""
    event = {
        'url': 'https://news.ycombinator.com',
        'content_type': 'news',
        'use_js_scenario': True,
        'country_code': 'us'
    }
    return lambda_handler(event, None)

def example_ecommerce_crawl():
    """Example: Crawl ecommerce site with JS scenario."""
    event = {
        'url': 'https://example-store.com',
        'content_type': 'ecommerce',
        'use_js_scenario': True,
        'js_scenario': CrawlScenarios.ecommerce_scenario(),
        'country_code': 'us'
    }
    return lambda_handler(event, None)

def example_financial_crawl():
    """Example: Crawl financial site with stealth mode."""
    event = {
        'url': 'https://financial-reports.com',
        'content_type': 'financial',
        'force_mode': 'stealth',
        'country_code': 'us'
    }
    return lambda_handler(event, None)

def example_screenshot():
    """Example: Take screenshot of webpage."""
    event = {
        'url': 'https://example.com',
        'take_screenshot': True,
        'full_page': True,
        'country_code': 'us'
    }
    return lambda_handler(event, None)

def example_file_download():
    """Example: Download file from URL."""
    event = {
        'url': 'https://example.com/document.pdf',
        'download_file': True,
        'country_code': 'us'
    }
    return lambda_handler(event, None) 