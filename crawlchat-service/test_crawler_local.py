#!/usr/bin/env python3
"""
Local test script to debug crawler functionality
"""

import sys
import os
import logging

# Add crawler path
sys.path.append('crawler-service/src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_crawler():
    """Test the crawler locally."""
    try:
        from crawler.enhanced_crawler_service import EnhancedCrawlerService
        
        # Get API key
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not api_key:
            logger.error("SCRAPINGBEE_API_KEY not set")
            return
        
        logger.info(f"Testing crawler with API key: {api_key[:10]}...")
        
        # Initialize crawler
        crawler = EnhancedCrawlerService(api_key=api_key)
        logger.info("EnhancedCrawlerService initialized")
        
        # Test URL
        test_url = "https://www.aboutamazon.com/about-us"
        logger.info(f"Testing with URL: {test_url}")
        
        # Call crawl_with_max_docs
        logger.info("Calling crawl_with_max_docs...")
        result = crawler.crawl_with_max_docs(test_url, max_doc_count=1)
        
        logger.info(f"Crawl result: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Documents found: {result.get('documents_found', 0)}")
        logger.info(f"Documents: {len(result.get('documents', []))}")
        
        if result.get('documents'):
            for i, doc in enumerate(result['documents']):
                logger.info(f"Document {i+1}: {doc.get('title', 'No title')} - {doc.get('url', 'No URL')}")
                logger.info(f"  Content length: {len(doc.get('content', ''))}")
        
    except Exception as e:
        logger.error(f"Error testing crawler: {e}", exc_info=True)

if __name__ == "__main__":
    test_crawler() 