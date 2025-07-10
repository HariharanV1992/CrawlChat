#!/usr/bin/env python3
"""
Local test script for the crawler functionality
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_crawler_imports():
    """Test if all crawler modules can be imported."""
    try:
        from config.crawler_config import CrawlerConfig
        logger.info("✓ CrawlerConfig imported successfully")
        
        from crawler.advanced_crawler import AdvancedCrawler
        logger.info("✓ AdvancedCrawler imported successfully")
        
        from crawler.enhanced_scrapingbee_manager import EnhancedScrapingBeeManager
        logger.info("✓ EnhancedScrapingBeeManager imported successfully")
        
        from crawler.file_downloader import FileDownloader
        logger.info("✓ FileDownloader imported successfully")
        
        from crawler.link_extractor import LinkExtractor
        logger.info("✓ LinkExtractor imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_crawler_config():
    """Test crawler configuration."""
    try:
        from config.crawler_config import CrawlerConfig
        
        # Test configuration methods
        config = CrawlerConfig.get_crawl_config()
        logger.info(f"✓ Crawl config: {config}")
        
        params = CrawlerConfig.get_scrapingbee_params()
        logger.info(f"✓ ScrapingBee params: {params}")
        
        # Check API key
        api_key = CrawlerConfig.SCRAPINGBEE_API_KEY
        if api_key:
            logger.info("✓ ScrapingBee API key is configured")
        else:
            logger.warning("⚠ ScrapingBee API key is NOT configured")
        
        return True
    except Exception as e:
        logger.error(f"✗ Config test failed: {e}")
        return False

def test_crawler_initialization():
    """Test crawler initialization."""
    try:
        from config.crawler_config import CrawlerConfig
        from crawler.advanced_crawler import AdvancedCrawler
        
        api_key = CrawlerConfig.SCRAPINGBEE_API_KEY
        if not api_key:
            logger.warning("⚠ Skipping crawler initialization test - no API key")
            return True
        
        # Test crawler initialization
        crawler = AdvancedCrawler(api_key=api_key)
        logger.info("✓ Crawler initialized successfully")
        
        # Test crawler close
        crawler.close()
        logger.info("✓ Crawler closed successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Crawler initialization failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🧪 Starting crawler tests...")
    
    tests = [
        ("Import Test", test_crawler_imports),
        ("Config Test", test_crawler_config),
        ("Initialization Test", test_crawler_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Crawler is ready to use.")
    else:
        logger.warning("⚠ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 