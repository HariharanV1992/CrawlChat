"""
Advanced crawler with enhanced ScrapingBee integration
"""

import logging
import time
import os
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import mimetypes
import json

from scrapingbee import ScrapingBeeClient
from .settings_manager import SettingsManager
from .utils import get_file_extension, is_valid_url
from .smart_scrapingbee_manager import ContentCheckers

logger = logging.getLogger(__name__)

class AdvancedCrawler:
    """
    Advanced crawler with progressive proxy strategy and enhanced features.
    """
    
    def __init__(self, api_key: str = None, settings: Dict[str, Any] = None):
        self.settings_manager = SettingsManager()
        self.settings = settings or self.settings_manager.get_all_settings()
        
        # Initialize ScrapingBee client
        api_key = api_key or os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            raise ValueError("ScrapingBee API key is required")
        
        self.scrapingbee_client = ScrapingBeeClient(api_key=api_key)
        logger.info("Advanced crawler initialized with official ScrapingBee client")
        
        # Content checkers mapping (simplified for now)
        self.content_checkers = {
            "news": ContentCheckers.news_site_checker,
            "ecommerce": ContentCheckers.generic_checker,
            "financial": ContentCheckers.financial_report_checker,
            "generic": ContentCheckers.generic_checker,
        }
        
        logger.info("Advanced crawler initialized with enhanced ScrapingBee manager")
    
    def crawl_url(self, url: str, content_type: str = "generic", 
                  use_js_scenario: bool = False, js_scenario: Dict[str, Any] = None,
                  render_js: bool = True, timeout: int = None, wait: int = None,
                  wait_for: str = None, wait_browser: str = None, 
                  block_ads: bool = None, block_resources: bool = None,
                  window_width: int = None, window_height: int = None,
                  premium_proxy: bool = False, country_code: str = "in",
                  stealth_proxy: bool = False, own_proxy: str = None,
                  forward_headers: bool = False, forward_headers_pure: bool = False,
                  download_file: bool = False, scraping_config: str = None) -> Dict[str, Any]:
        """
        Crawl URL with progressive proxy strategy.
        
        Args:
            url: Target URL to crawl
            content_type: Type of content ("news", "ecommerce", "financial", "generic")
            use_js_scenario: Whether to use JavaScript scenario
            js_scenario: Custom JavaScript scenario
            render_js: Whether to enable JavaScript rendering (default: True)
            timeout: Request timeout in seconds
            wait: Fixed wait time in milliseconds after page load
            wait_for: CSS selector to wait for before scraping
            wait_browser: Browser network condition to wait for
            block_ads: Whether to block ads (default: False, only applies when render_js=True)
            block_resources: Whether to block images and CSS (default: True for speed, only applies when render_js=True)
            window_width: Viewport width in pixels (only applies when render_js=True)
            window_height: Viewport height in pixels (only applies when render_js=True)
            premium_proxy: Use premium/residential proxies for hard-to-scrape sites (costs 25 credits with JS, 10 without)
            country_code: Proxy country code (ISO 3166-1 format, e.g., 'us', 'gb', 'de', 'in')
            stealth_proxy: Use stealth proxies for hardest-to-scrape sites (beta, costs 75 credits, requires render_js=True)
            own_proxy: Use your own proxy (format: protocol://username:password@host:port)
            forward_headers: Forward custom headers to target website (use Spb- prefix in headers)
            forward_headers_pure: Forward headers without ScrapingBee's automatic headers (requires render_js=False)
            download_file: Download file content (images, PDFs, etc.) instead of HTML (recommended with render_js=False)
            scraping_config: Use pre-saved scraping configuration by name
        
        Returns:
            Dictionary with crawl results
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        # Validate stealth_proxy requirements
        if stealth_proxy and not render_js:
            raise ValueError("stealth_proxy=True requires render_js=True")
        
        # Validate forward_headers_pure requirements
        if forward_headers_pure and render_js:
            raise ValueError("forward_headers_pure=True requires render_js=False")
        
        # Validate download_file requirements
        if download_file and render_js:
            logger.warning("download_file=True with render_js=True - recommend using render_js=False for file downloads")
        
        # Validate scraping_config usage
        if scraping_config:
            logger.info(f"Using preconfigured scraping config: {scraping_config}")
        
        logger.info(f"Starting crawl for {url} with content type: {content_type}")
        
        start_time = time.time()
        
        try:
            # Determine content checker
            content_checker = self.content_checkers.get(content_type, ContentCheckers.generic_checker)
            
            # Check if this is a file URL or if download_file is requested
            if self._is_file_url(url) or download_file:
                return self._crawl_file(url, download_file)
            
            # Use JavaScript scenario if specified
            if use_js_scenario or js_scenario:
                return self._crawl_with_js_scenario(url, js_scenario, content_checker)
            
            # Use official ScrapingBee client
            params = {}
            
            # Add scraping_config if provided (this will load preconfigured settings)
            if scraping_config:
                params['scraping_config'] = scraping_config
            
            if not render_js:
                params['render_js'] = 'False'
            if timeout:
                # Ensure timeout is in milliseconds and within ScrapingBee limits (1000-141000)
                timeout_ms = int(timeout)
                if timeout_ms < 1000:
                    timeout_ms = 1000
                elif timeout_ms > 141000:
                    timeout_ms = 141000
                params['timeout'] = str(timeout_ms)
            if wait:
                params['wait'] = str(wait)
            if wait_for:
                params['wait_for'] = wait_for
            if wait_browser:
                params['wait_browser'] = wait_browser
            if block_ads is not None:
                params['block_ads'] = 'True' if block_ads else 'False'
            if block_resources is not None:
                params['block_resources'] = 'True' if block_resources else 'False'
            if window_width is not None:
                params['window_width'] = str(window_width)
            if window_height is not None:
                params['window_height'] = str(window_height)
            if premium_proxy:
                params['premium_proxy'] = 'True'
            if country_code and country_code != "in":  # Only add if not default
                params['country_code'] = country_code
            if stealth_proxy:
                params['stealth_proxy'] = 'True'
            if own_proxy:
                params['own_proxy'] = own_proxy
            if forward_headers:
                params['forward_headers'] = 'True'
            if forward_headers_pure:
                params['forward_headers_pure'] = 'True'
            if js_scenario:
                params['js_scenario'] = json.dumps(js_scenario)
            
            response = self.scrapingbee_client.get(url, params=params)
            
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
                "proxy_mode": "standard",
                "stats": {"requests": 1, "successes": 1, "failures": 0},
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
                "stats": {"requests": 1, "successes": 0, "failures": 1},
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
            # Use JavaScript scenario with ScrapingBee client
            params = {
                'js_scenario': json.dumps(scenario),
                'render_js': 'True'
            }
            response = self.scrapingbee_client.get(url, params=params)
            
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
                "stats": {"requests": 1, "successes": 1, "failures": 0},
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
                "stats": {"requests": 1, "successes": 0, "failures": 1},
            }
    
    def download_file(self, url: str) -> Dict[str, Any]:
        """
        Download file from URL using ScrapingBee API.
        
        Args:
            url: File URL
        
        Returns:
            Download results with file content and metadata
        """
        logger.info(f"Downloading file from {url}")
        
        start_time = time.time()
        
        try:
            # Use optimized parameters for binary file downloads
            params = {
                'render_js': 'False',  # No JS rendering for file downloads
                'timeout': '60',  # Longer timeout for file downloads
                'block_resources': 'False',  # Don't block resources for binary files
                'premium_proxy': 'True',  # Use premium proxy for better reliability
                'forward_headers': 'True',  # Forward headers for better compatibility
            }
            
            # Add special headers for binary content
            headers = {
                'Accept': '*/*',  # Accept all content types
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
            
            logger.info(f"Making request with params: {params}")
            logger.info(f"Request headers: {headers}")
            
            # Make the request with optimized parameters
            response = self.scrapingbee_client.get(url, params=params, headers=headers)
            content = response.content
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Content length: {len(content)} bytes")
            logger.info(f"Content preview: {content[:100]}")  # First 100 bytes
            
            # Check file size (ScrapingBee has 2MB limit)
            if len(content) > 2 * 1024 * 1024:  # 2MB
                logger.warning(f"File size ({len(content)} bytes) exceeds 2MB limit")
                return {
                    "success": False,
                    "url": url,
                    "status_code": 413,  # Payload Too Large
                    "error": "File size exceeds 2MB limit",
                    "download_time": round(time.time() - start_time, 2),
                    "stats": {"requests": 1, "successes": 0, "failures": 1},
                }
            
            # Determine file type
            file_type = self._determine_file_type(url, content)
            
            # Get content type from response headers
            content_type = response.headers.get('content-type', file_type)
            
            download_time = time.time() - start_time
            
            result = {
                "success": True,
                "url": url,
                "status_code": getattr(response, 'status_code', 200),
                "content": content,
                "content_length": len(content),
                "file_type": file_type,
                "content_type": content_type,
                "download_time": round(download_time, 2),
                "proxy_mode": "premium",
                "headers": dict(response.headers),
                "stats": {"requests": 1, "successes": 1, "failures": 0},
            }
            
            logger.info(f"Successfully downloaded {url} ({len(content)} bytes, {file_type}) in {download_time:.2f}s")
            return result
            
        except Exception as e:
            download_time = time.time() - start_time
            logger.error(f"Failed to download {url}: {e}")
            
            return {
                "success": False,
                "url": url,
                "status_code": 500,  # Internal Server Error
                "error": str(e),
                "download_time": round(download_time, 2),
                "stats": {"requests": 1, "successes": 0, "failures": 1},
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
            # Screenshot and advanced features are not supported in the official client stub
            # Remove or replace with NotImplementedError
            raise NotImplementedError("Screenshot feature is not implemented in this version.")
            
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
                "stats": {"requests": 1, "successes": 0, "failures": 1},
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
        return {"requests": "N/A", "successes": "N/A", "failures": "N/A"}
    
    def set_country_code(self, country_code: str):
        """Set country code for proxy geolocation (not implemented)."""
        pass
    
    def save_site_requirements(self, filename: str = None):
        pass
    
    def load_site_requirements(self, filename: str = None):
        pass
    
    def reset_stats(self):
        pass
    
    def _is_file_url(self, url: str) -> bool:
        """Check if URL points to a file."""
        file_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.csv', '.json', '.xml',
            '.zip', '.rar', '.7z', '.tar', '.gz'
        ]
        return any(url.lower().endswith(ext) for ext in file_extensions)
    
    def _crawl_file(self, url: str, download_file: bool = False) -> Dict[str, Any]:
        """Crawl file URL."""
        logger.info(f"Crawling file: {url}")
        if download_file:
            return self.download_file(url)
        else:
            # If not downloading, just return a placeholder result
            return {
                "success": True,
                "url": url,
                "status_code": 200,
                "content": "File content not available for this URL",
                "content_length": 0,
                "file_type": "unknown",
                "download_time": 0,
                "content_type": "text/plain",
                "proxy_mode": "standard",
                "stats": {"requests": 1, "successes": 1, "failures": 0},
            }
    
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
        elif path.endswith('.bmp'):
            return 'image/bmp'
        elif path.endswith('.tiff') or path.endswith('.tif'):
            return 'image/tiff'
        elif path.endswith('.webp'):
            return 'image/webp'
        elif path.endswith('.svg'):
            return 'image/svg+xml'
        elif path.endswith(('.doc', '.docx')):
            return 'application/msword'
        elif path.endswith(('.xls', '.xlsx')):
            return 'application/vnd.ms-excel'
        elif path.endswith(('.ppt', '.pptx')):
            return 'application/vnd.ms-powerpoint'
        elif path.endswith('.txt'):
            return 'text/plain'
        elif path.endswith('.csv'):
            return 'text/csv'
        elif path.endswith('.json'):
            return 'application/json'
        elif path.endswith('.xml'):
            return 'application/xml'
        elif path.endswith('.zip'):
            return 'application/zip'
        elif path.endswith('.rar'):
            return 'application/x-rar-compressed'
        elif path.endswith('.7z'):
            return 'application/x-7z-compressed'
        elif path.endswith('.tar'):
            return 'application/x-tar'
        elif path.endswith('.gz'):
            return 'application/gzip'
        
        # Try to determine from content (magic bytes)
        if content.startswith(b'%PDF'):
            return 'application/pdf'
        elif content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif content.startswith(b'\x89PNG'):
            return 'image/png'
        elif content.startswith(b'GIF8'):
            return 'image/gif'
        elif content.startswith(b'BM'):
            return 'image/bmp'
        elif content.startswith(b'II*\x00') or content.startswith(b'MM\x00*'):
            return 'image/tiff'
        elif content.startswith(b'RIFF') and content[8:12] == b'WEBP':
            return 'image/webp'
        elif content.startswith(b'PK\x03\x04'):
            return 'application/zip'
        elif content.startswith(b'Rar!'):
            return 'application/x-rar-compressed'
        elif content.startswith(b'7z\xbc\xaf\x27\x1c'):
            return 'application/x-7z-compressed'
        elif content.startswith(b'ustar'):
            return 'application/x-tar'
        elif content.startswith(b'\x1f\x8b'):
            return 'application/gzip'
        
        # Try to determine if it's HTML
        if content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            return 'text/html'
        
        # Try to determine if it's JSON
        try:
            content.decode('utf-8')
            if content.strip().startswith(b'{') or content.strip().startswith(b'['):
                return 'application/json'
        except:
            pass
        
        # Default to binary
        return 'application/octet-stream'
    
    def _get_used_proxy_mode(self, url: str) -> str:
        """Get the proxy mode that was used for a URL."""
        return "unknown"
    
    def close(self):
        """Close the crawler and cleanup resources."""
        pass
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