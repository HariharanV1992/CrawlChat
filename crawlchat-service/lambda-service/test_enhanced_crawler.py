#!/usr/bin/env python3
"""
Test script for enhanced crawler in Lambda environment
"""

import os
import sys
import json
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_crawler():
    """Test the enhanced crawler functionality."""
    
    # Set API key for testing
    os.environ['SCRAPINGBEE_API_KEY'] = 'NV9KS7HERG9249QDV83S4FXJS8732HVO79JM6Y3O9X4W4OBNMQKHI3F8VP7HBGF0JGSS4PT47QLRFUX6'
    
    try:
        # Import the enhanced crawler service
        from crawler.enhanced_crawler_service import EnhancedCrawlerService
        
        logger.info("Enhanced crawler service imported successfully")
        
        # Test single page crawl
        logger.info("Testing single page crawl...")
        enhanced_service = EnhancedCrawlerService(os.environ['SCRAPINGBEE_API_KEY'])
        
        # Test with max_doc_count=1
        result = enhanced_service.crawl_with_max_docs(
            url="https://example.com",
            max_doc_count=1
        )
        
        logger.info(f"Single page crawl result: {result.get('success')}")
        logger.info(f"Documents found: {result.get('documents_found')}")
        
        # Test with max_doc_count=3
        logger.info("Testing multi-page crawl...")
        result2 = enhanced_service.crawl_with_max_docs(
            url="https://www.irs.gov/forms-pubs",
            max_doc_count=3
        )
        
        logger.info(f"Multi-page crawl result: {result2.get('success')}")
        logger.info(f"Documents found: {result2.get('documents_found')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_lambda_handler():
    """Test the Lambda handler with enhanced crawler."""
    
    try:
        from lambda_handler import handle_enhanced_crawl_request
        
        # Test event
        event = {
            'url': 'https://example.com',
            'max_doc_count': 1
        }
        
        logger.info("Testing Lambda handler...")
        result = handle_enhanced_crawl_request(event, None)
        
        logger.info(f"Lambda handler result status: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            logger.info(f"Documents found: {body.get('documents_found')}")
        
        return result.get('statusCode') == 200
        
    except Exception as e:
        logger.error(f"Lambda handler test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting enhanced crawler tests...")
    
    # Test 1: Enhanced crawler service
    test1_result = test_enhanced_crawler()
    logger.info(f"Enhanced crawler test: {'PASSED' if test1_result else 'FAILED'}")
    
    # Test 2: Lambda handler
    test2_result = test_lambda_handler()
    logger.info(f"Lambda handler test: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        logger.info("All tests PASSED - Lambda deployment should work!")
    else:
        logger.error("Some tests FAILED - check the implementation") 