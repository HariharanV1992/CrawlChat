"""
Advanced crawler with enhanced ScrapingBee integration
"""

import logging
import time
import os
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import mimetypes

from .enhanced_scrapingbee_manager import (
    EnhancedScrapingBeeManager, 
    ProxyMode, 
    JavaScriptScenarios, 
    ContentCheckers
)
from .settings_manager import SettingsManager
from .utils import get_file_extension, is_valid_url

logger = logging.getLogger(__name__)

class AdvancedCrawler:
    """
    Advanced crawler with progressive proxy strategy and enhanced features.
    """
    
    def __init__(self, api_key: str = None, settings: Dict[str, Any] = None):
        self.settings_manager = SettingsManager()
        self.settings = settings or self.settings_manager.get_settings()
        
        # Initialize enhanced ScrapingBee manager
        api_key = api_key or os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            raise ValueError("ScrapingBee API key is required")
        
        # Configure base options
        base_options = {
            "country_code": self.settings.get("country_code", "us"),
            "block_ads": self.settings.get("block_ads", True),
            "block_resources": self.settings.get("block_resources", False),
        }
        
        self.scrapingbee = EnhancedScrapingBeeManager(api_key, base_options)
        
        # Content checkers mapping
        self.content_checkers = {
            "news": ContentCheckers.news_site_checker,
            "ecommerce": ContentCheckers.ecommerce_checker,
            "financial": ContentCheckers.financial_checker,
            "generic": ContentCheckers.generic_checker,
        }
        
        logger.info("Advanced crawler initialized with enhanced ScrapingBee manager")
    
    def crawl_url(self, url: str, content_type: str = "generic", 
                  use_js_scenario: bool = False, js_scenario: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crawl URL with progressive proxy strategy.
        
        Args:
            url: Target URL to crawl
            content_type: Type of content ("news", "ecommerce", "financial", "generic")
            use_js_scenario: Whether to use JavaScript scenario
            js_scenario: Custom JavaScript scenario
        
        Returns:
            Dictionary with crawl results
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        logger.info(f"Starting crawl for {url} with content type: {content_type}")
        
        start_time = time.time()
        
        try:
            # Determine content checker
            content_checker = self.content_checkers.get(content_type, ContentCheckers.generic_checker)
            
            # Check if this is a file URL
            if self._is_file_url(url):
                return self._crawl_file(url)
            
            # Use JavaScript scenario if specified
            if use_js_scenario or js_scenario:
                return self._crawl_with_js_scenario(url, js_scenario, content_checker)
            
            # Use progressive proxy strategy
            response = self.scrapingbee.make_progressive_request(url, content_checker)
            
            crawl_time = time.time() - start_time
            
            result = {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content": response.text,
                "content_length": len(response.text),
                "crawl_time": round(crawl_time, 2),
                "content_type": "html",
                "headers": dict(response.headers),
                "proxy_mode": self._get_used_proxy_mode(url),
                "stats": self.scrapingbee.get_stats(),
            }
            
            logger.info(f"Successfully crawled {url} in {crawl_time:.2f}s")
            return result
            
        except Exception as e:
            crawl_time = time.time() - start_time
            logger.error(f"Failed to crawl {url}: {e}")
            
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "crawl_time": round(crawl_time, 2),
                "stats": self.scrapingbee.get_stats(),
            }
    
    def crawl_with_js_scenario(self, url: str, scenario: Dict[str, Any], 
                              content_type: str = "generic") -> Dict[str, Any]:
        """
        Crawl URL with specific JavaScript scenario.
        
        Args:
            url: Target URL
            scenario: JavaScript scenario
            content_type: Content type for validation
        
        Returns:
            Crawl results
        """
        logger.info(f"Crawling {url} with JavaScript scenario")
        
        start_time = time.time()
        
        try:
            # Use premium mode for JS scenarios (more reliable)
            response = self.scrapingbee.make_js_scenario_request(url, scenario, ProxyMode.PREMIUM)
            
            crawl_time = time.time() - start_time
            
            result = {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content": response.text,
                "content_length": len(response.text),
                "crawl_time": round(crawl_time, 2),
                "content_type": "html",
                "js_scenario": scenario,
                "proxy_mode": "premium",
                "headers": dict(response.headers),
                "stats": self.scrapingbee.get_stats(),
            }
            
            logger.info(f"Successfully crawled {url} with JS scenario in {crawl_time:.2f}s")
            return result
            
        except Exception as e:
            crawl_time = time.time() - start_time
            logger.error(f"Failed to crawl {url} with JS scenario: {e}")
            
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "crawl_time": round(crawl_time, 2),
                "js_scenario": scenario,
                "stats": self.scrapingbee.get_stats(),
            }
    
    def download_file(self, url: str) -> Dict[str, Any]:
        """
        Download file from URL.
        
        Args:
            url: File URL
        
        Returns:
            Download results
        """
        logger.info(f"Downloading file from {url}")
        
        start_time = time.time()
        
        try:
            content = self.scrapingbee.download_file(url)
            
            # Determine file type
            file_type = self._determine_file_type(url, content)
            
            download_time = time.time() - start_time
            
            result = {
                "success": True,
                "url": url,
                "content": content,
                "content_length": len(content),
                "file_type": file_type,
                "download_time": round(download_time, 2),
                "content_type": file_type,
                "proxy_mode": "standard",
                "stats": self.scrapingbee.get_stats(),
            }
            
            logger.info(f"Successfully downloaded {url} ({len(content)} bytes) in {download_time:.2f}s")
            return result
            
        except Exception as e:
            download_time = time.time() - start_time
            logger.error(f"Failed to download {url}: {e}")
            
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "download_time": round(download_time, 2),
                "stats": self.scrapingbee.get_stats(),
            }
    
    def take_screenshot(self, url: str, full_page: bool = True, 
                       selector: str = None) -> Dict[str, Any]:
        """
        Take screenshot of webpage.
        
        Args:
            url: Target URL
            full_page: Take full page screenshot
            selector: CSS selector for specific element
        
        Returns:
            Screenshot results
        """
        logger.info(f"Taking screenshot of {url}")
        
        start_time = time.time()
        
        try:
            screenshot_data = self.scrapingbee.take_screenshot(url, full_page, selector)
            
            screenshot_time = time.time() - start_time
            
            result = {
                "success": True,
                "url": url,
                "screenshot": screenshot_data,
                "content_length": len(screenshot_data),
                "screenshot_time": round(screenshot_time, 2),
                "content_type": "image/png",
                "full_page": full_page,
                "selector": selector,
                "proxy_mode": "premium",
                "stats": self.scrapingbee.get_stats(),
            }
            
            logger.info(f"Successfully took screenshot of {url} in {screenshot_time:.2f}s")
            return result
            
        except Exception as e:
            screenshot_time = time.time() - start_time
            logger.error(f"Failed to take screenshot of {url}: {e}")
            
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "screenshot_time": round(screenshot_time, 2),
                "full_page": full_page,
                "selector": selector,
                "stats": self.scrapingbee.get_stats(),
            }
    
    def crawl_multiple_urls(self, urls: List[str], content_type: str = "generic") -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs with progressive strategy.
        
        Args:
            urls: List of URLs to crawl
            content_type: Content type for validation
        
        Returns:
            List of crawl results
        """
        logger.info(f"Crawling {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"Crawling URL {i}/{len(urls)}: {url}")
            
            try:
                result = self.crawl_url(url, content_type)
                results.append(result)
                
                # Brief delay between requests
                if i < len(urls):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                results.append({
                    "success": False,
                    "url": url,
                    "error": str(e),
                })
        
        logger.info(f"Completed crawling {len(urls)} URLs")
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        return {
            "scrapingbee_stats": self.scrapingbee.get_stats(),
            "cost_estimate": self.scrapingbee.get_cost_estimate(),
            "site_requirements": self.scrapingbee.site_requirements,
        }
    
    def set_country_code(self, country_code: str):
        """Set country code for proxy geolocation."""
        self.scrapingbee.set_country_code(country_code)
        logger.info(f"Set country code to {country_code}")
    
    def save_site_requirements(self, filename: str = None):
        """Save site requirements to file."""
        self.scrapingbee.save_site_requirements(filename)
    
    def load_site_requirements(self, filename: str = None):
        """Load site requirements from file."""
        self.scrapingbee.load_site_requirements(filename)
    
    def reset_stats(self):
        """Reset all statistics."""
        self.scrapingbee.reset_stats()
        logger.info("Statistics reset")
    
    def _is_file_url(self, url: str) -> bool:
        """Check if URL points to a file."""
        file_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.doc', '.docx', '.xls', '.xlsx']
        return any(url.lower().endswith(ext) for ext in file_extensions)
    
    def _crawl_file(self, url: str) -> Dict[str, Any]:
        """Crawl file URL."""
        logger.info(f"Crawling file: {url}")
        return self.download_file(url)
    
    def _crawl_with_js_scenario(self, url: str, scenario: Dict[str, Any], 
                               content_checker) -> Dict[str, Any]:
        """Crawl with JavaScript scenario."""
        return self.crawl_with_js_scenario(url, scenario)
    
    def _determine_file_type(self, url: str, content: bytes) -> str:
        """Determine file type from URL and content."""
        # Try to determine from URL first
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Common file extensions
        if path.endswith('.pdf'):
            return 'application/pdf'
        elif path.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif path.endswith('.png'):
            return 'image/png'
        elif path.endswith('.gif'):
            return 'image/gif'
        elif path.endswith(('.doc', '.docx')):
            return 'application/msword'
        elif path.endswith(('.xls', '.xlsx')):
            return 'application/vnd.ms-excel'
        
        # Try to determine from content
        if content.startswith(b'%PDF'):
            return 'application/pdf'
        elif content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif content.startswith(b'\x89PNG'):
            return 'image/png'
        elif content.startswith(b'GIF8'):
            return 'image/gif'
        
        # Default to binary
        return 'application/octet-stream'
    
    def _get_used_proxy_mode(self, url: str) -> str:
        """Get the proxy mode that was used for a URL."""
        domain = urlparse(url).netloc
        if domain in self.scrapingbee.site_requirements:
            return self.scrapingbee.site_requirements[domain].value
        return "unknown"
    
    def close(self):
        """Close the crawler and cleanup resources."""
        self.scrapingbee.close()
        logger.info("Advanced crawler closed")


# Pre-built scenarios for common use cases
class CrawlScenarios:
    """Pre-built crawl scenarios for common websites."""
    
    @staticmethod
    def news_site_scenario():
        """Scenario for news websites."""
        return JavaScriptScenarios.load_more_content(
            button_selector=".load-more, .show-more, .read-more",
            wait_selector=".article, .story, .content"
        )
    
    @staticmethod
    def ecommerce_scenario():
        """Scenario for ecommerce websites."""
        return JavaScriptScenarios.scroll_and_click(
            scroll_amount=1000,
            selector=".product, .item, .card"
        )
    
    @staticmethod
    def social_media_scenario():
        """Scenario for social media websites."""
        return JavaScriptScenarios.infinite_scroll(max_scrolls=10, delay=2000)
    
    @staticmethod
    def financial_site_scenario():
        """Scenario for financial websites."""
        return JavaScriptScenarios.wait_for_element(
            selector=".financial-data, .report, .statement",
            timeout=15000
        )
    
    @staticmethod
    def blog_scenario():
        """Scenario for blog websites."""
        return JavaScriptScenarios.click_and_wait(
            selector=".pagination .next, .load-more",
            wait_time=3000
        )