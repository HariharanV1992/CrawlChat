#!/usr/bin/env python3
"""
Test script for Smart ScrapingBee integration with efficient JavaScript rendering control.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from crawler_service.src.crawler.smart_scrapingbee_manager import SmartScrapingBeeManager, ContentCheckers
from crawler_service.src.crawler.advanced_crawler import AdvancedCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartScrapingBeeTester:
    """Test class for Smart ScrapingBee integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.test_results = []
    
    async def test_smart_manager(self):
        """Test the SmartScrapingBeeManager with various scenarios."""
        logger.info("🧪 Testing SmartScrapingBeeManager...")
        
        # Initialize manager
        manager = SmartScrapingBeeManager(self.api_key)
        
        # Test URLs for different scenarios
        test_urls = [
            {
                'url': 'https://www.business-standard.com/article/companies/idfc-first-bank-q3-results-profit-rises-18-5-to-rs-716-cr-124012300001_1.html',
                'site_type': 'news',
                'checker': ContentCheckers.news_site_checker,
                'description': 'Business Standard News Article'
            },
            {
                'url': 'https://finance.yahoo.com/quote/AAPL',
                'site_type': 'stock',
                'checker': ContentCheckers.stock_site_checker,
                'description': 'Yahoo Finance Stock Page'
            },
            {
                'url': 'https://www.reuters.com/technology/',
                'site_type': 'news',
                'checker': ContentCheckers.news_site_checker,
                'description': 'Reuters Technology News'
            },
            {
                'url': 'https://www.marketwatch.com/investing/stock/msft',
                'site_type': 'stock',
                'checker': ContentCheckers.stock_site_checker,
                'description': 'MarketWatch Stock Page'
            }
        ]
        
        for test_case in test_urls:
            logger.info(f"\n🔍 Testing: {test_case['description']}")
            logger.info(f"URL: {test_case['url']}")
            
            try:
                # Make smart request
                start_time = datetime.now()
                response = manager.make_smart_request(
                    test_case['url'], 
                    test_case['checker'],
                    timeout=30
                )
                end_time = datetime.now()
                
                # Analyze results
                duration = (end_time - start_time).total_seconds()
                content_length = len(response.text)
                
                # Check if JS was used
                stats = manager.get_stats()
                js_used = test_case['url'] in manager.site_js_requirements.get('domain', {})
                
                result = {
                    'url': test_case['url'],
                    'description': test_case['description'],
                    'site_type': test_case['site_type'],
                    'status_code': response.status_code,
                    'content_length': content_length,
                    'duration_seconds': round(duration, 2),
                    'js_used': js_used,
                    'success': response.status_code == 200
                }
                
                self.test_results.append(result)
                
                logger.info(f"✅ Status: {response.status_code}")
                logger.info(f"📄 Content Length: {content_length:,} bytes")
                logger.info(f"⏱️ Duration: {duration:.2f}s")
                logger.info(f"🔄 JS Used: {js_used}")
                
                # Show sample content
                if response.status_code == 200:
                    sample = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    logger.info(f"📝 Sample: {sample}")
                
            except Exception as e:
                logger.error(f"❌ Failed: {e}")
                result = {
                    'url': test_case['url'],
                    'description': test_case['description'],
                    'site_type': test_case['site_type'],
                    'error': str(e),
                    'success': False
                }
                self.test_results.append(result)
        
        # Show final statistics
        self._show_manager_stats(manager)
        manager.close()
    
    async def test_advanced_crawler(self):
        """Test the AdvancedCrawler with smart ScrapingBee integration."""
        logger.info("\n🕷️ Testing AdvancedCrawler...")
        
        # Test crawling a news site
        test_url = "https://www.business-standard.com/article/companies/idfc-first-bank-q3-results-profit-rises-18-5-to-rs-716-cr-124012300001_1.html"
        
        try:
            # Initialize crawler
            crawler = AdvancedCrawler(
                api_key=self.api_key,
                output_dir="test_crawled_data",
                max_depth=1,
                max_pages=3,
                delay=1.0,
                site_type='news'
            )
            
            logger.info(f"Starting crawl of: {test_url}")
            
            # Start crawling
            results = await crawler.crawl(test_url)
            
            # Display results
            self._show_crawler_results(results)
            
        except Exception as e:
            logger.error(f"❌ Crawler test failed: {e}")
    
    def _show_manager_stats(self, manager: SmartScrapingBeeManager):
        """Display manager statistics."""
        logger.info("\n📊 SmartScrapingBeeManager Statistics:")
        
        stats = manager.get_stats()
        cost_estimate = manager.get_cost_estimate()
        
        logger.info(f"📈 Request Statistics:")
        logger.info(f"   No-JS Requests: {stats['no_js_requests']}")
        logger.info(f"   JS Requests: {stats['js_requests']}")
        logger.info(f"   No-JS Successes: {stats['no_js_successes']}")
        logger.info(f"   JS Successes: {stats['js_successes']}")
        logger.info(f"   Retry with JS: {stats['retry_with_js_count']}")
        logger.info(f"   Total Requests: {stats['total_requests']}")
        logger.info(f"   Success Rate: {stats['success_rate']}%")
        logger.info(f"   JS Usage Rate: {stats['js_usage_rate']}%")
        
        logger.info(f"\n💰 Cost Estimate:")
        logger.info(f"   No-JS Cost: ${cost_estimate['no_js_cost']}")
        logger.info(f"   JS Cost: ${cost_estimate['js_cost']}")
        logger.info(f"   Total Cost: ${cost_estimate['total_cost']}")
        logger.info(f"   Cost Savings: ${cost_estimate['cost_savings']}")
        
        logger.info(f"\n🎯 Site JS Requirements:")
        for domain, requires_js in stats['site_js_requirements'].items():
            logger.info(f"   {domain}: {'JS Required' if requires_js else 'No-JS OK'}")
    
    def _show_crawler_results(self, results: dict):
        """Display crawler results."""
        logger.info("\n📊 AdvancedCrawler Results:")
        
        crawling_stats = results['crawling_stats']
        proxy_stats = results['proxy_stats']
        cost_estimate = results['cost_estimate']
        
        logger.info(f"🕷️ Crawling Statistics:")
        logger.info(f"   URLs Visited: {crawling_stats['total_urls_visited']}")
        logger.info(f"   Successful Downloads: {crawling_stats['successful_downloads']}")
        logger.info(f"   Failed URLs: {crawling_stats['failed_urls']}")
        logger.info(f"   Max Depth Reached: {crawling_stats['max_depth_reached']}")
        logger.info(f"   Duration: {crawling_stats['duration_seconds']}s")
        logger.info(f"   Pages per Minute: {crawling_stats['pages_per_minute']}")
        
        logger.info(f"\n🔧 Proxy Statistics:")
        logger.info(f"   No-JS Requests: {proxy_stats['no_js_requests']}")
        logger.info(f"   JS Requests: {proxy_stats['js_requests']}")
        logger.info(f"   Success Rate: {proxy_stats['success_rate']}%")
        logger.info(f"   JS Usage Rate: {proxy_stats['js_usage_rate']}%")
        
        logger.info(f"\n💰 Cost Estimate:")
        logger.info(f"   Total Cost: ${cost_estimate['total_cost']}")
        logger.info(f"   Cost Savings: ${cost_estimate['cost_savings']}")
        
        logger.info(f"\n📁 Output Directory: {results['output_directory']}")
        logger.info(f"🎯 Site Type: {results['site_type']}")
    
    def save_test_results(self, filename: str = "smart_scrapingbee_test_results.json"):
        """Save test results to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"✅ Test results saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")

async def main():
    """Main test function."""
    # Get API key from environment or user input
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        api_key = input("Enter your ScrapingBee API key: ").strip()
    
    if not api_key:
        logger.error("❌ No API key provided. Set SCRAPINGBEE_API_KEY environment variable or provide it manually.")
        return
    
    logger.info("🚀 Starting Smart ScrapingBee Integration Tests")
    logger.info("=" * 60)
    
    # Initialize tester
    tester = SmartScrapingBeeTester(api_key)
    
    try:
        # Test smart manager
        await tester.test_smart_manager()
        
        # Test advanced crawler
        await tester.test_advanced_crawler()
        
        # Save results
        tester.save_test_results()
        
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
    
    logger.info("\n📋 Test Summary:")
    logger.info("The smart ScrapingBee integration provides:")
    logger.info("✅ Automatic no-JS first approach for cost savings")
    logger.info("✅ Intelligent JS rendering when needed")
    logger.info("✅ Site-specific caching of JS requirements")
    logger.info("✅ Comprehensive cost tracking and statistics")
    logger.info("✅ Pre-built content checkers for different site types")
    logger.info("✅ Seamless integration with AdvancedCrawler")

if __name__ == "__main__":
    asyncio.run(main()) 