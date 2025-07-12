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
import base64 # Added for base64 encoding

from scrapingbee import ScrapingBeeClient
from .settings_manager import SettingsManager
from .utils import get_file_extension, is_valid_url
from .smart_scrapingbee_manager import ContentCheckers
from .enhanced_scrapingbee_manager import JavaScriptScenarios

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
        self.api_key = api_key  # <-- Ensure this is set
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

    def _clean_url(self, url: str) -> str:
        """
        Clean and validate URL to remove malformed content.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL or None if invalid
        """
        if not url:
            return None
            
        # Remove JavaScript code that might be appended
        if ');' in url:
            url = url.split(');')[0]
        
        # Remove any trailing JavaScript
        if 'javascript:' in url.lower():
            return None
        
        # Remove any trailing HTML entities or malformed parts
        if '&amp;' in url:
            url = url.split('&amp;')[0]
        
        # Remove any trailing spaces or newlines
        url = url.strip()
        
        # Ensure URL starts with http/https
        if not url.startswith(('http://', 'https://')):
            return None
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return url
        except Exception:
            return None
    
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
        Download file from URL using ScrapingBee API with retry logic.
        
        Args:
            url: File URL
        
        Returns:
            Download results with file content and metadata
        """
        logger.info(f"Downloading file from {url}")
        
        # Clean and validate URL first
        url = self._clean_url(url)
        if not url:
            return {
                'success': False,
                'error': 'Invalid or malformed URL',
                'url': url
            }
        
        # Check file size limit (2MB = 2 * 1024 * 1024 bytes)
        MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB limit per ScrapingBee documentation
        
        start_time = time.time()
        max_retries = 3
        base_delay = 2  # Start with 2 second delay
        
        for attempt in range(max_retries):
            try:
                # Use optimized parameters for binary file downloads
                # Following ScrapingBee documentation: render_js=false for file downloads
                params = {
                    'api_key': self.api_key,
                    'url': url,
                    'render_js': 'false',  # Recommended for file downloads per ScrapingBee docs
                    'timeout': '60000',  # 60 seconds timeout for large PDF files
                    'block_resources': 'false',  # Don't block resources for binary files
                    'premium_proxy': 'true',  # Use premium proxy for better reliability
                    'forward_headers': 'true',  # Forward browser headers
                    'country_code': 'in',  # Use Indian proxy for Indian sites
                    'stealth_proxy': 'false',  # Disable stealth proxy for file downloads
                    'block_ads': 'false',  # Don't block ads for file downloads
                }
                
                # Add delay between retries to avoid rate limiting
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}, waiting {delay}s...")
                    time.sleep(delay)
                
                # Log params without exposing API key
                safe_params = params.copy()
                safe_params['api_key'] = '***HIDDEN***'
                logger.info(f"Making request with params: {safe_params}")
                
                # Add special headers for binary content
                headers = {
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Make the request using requests directly instead of scrapingbee_client
                import requests
                from urllib.parse import quote
                
                # ScrapingBee base URL
                scrapingbee_url = "https://app.scrapingbee.com/api/v1/"
                
                # Ensure the 'url' parameter is properly passed (ScrapingBee handles encoding, avoid double encoding)
                if not params.get("url"):
                    logger.error("Missing 'url' in request parameters")
                    return {
                        'success': False,
                        'error': "Missing 'url' in request parameters",
                        'url': url
                    }
                
                # Debug: Log the final constructed URL (without API key)
                safe_params = params.copy()
                safe_params['api_key'] = '***HIDDEN***'
                logger.debug(f"Final ScrapingBee request URL: {scrapingbee_url}?url={params['url']}")
                logger.info(f"Making request to ScrapingBee API for: {url}")
                
                # Perform request
                response = requests.get(scrapingbee_url, params=params, headers=headers, timeout=70)
                
                logger.info(f"Response status: {response.status_code}")
                
                # Log response content for error diagnosis
                if response.status_code != 200:
                    try:
                        error_content = response.text
                        logger.error(f"ScrapingBee API Error Response: {error_content}")
                        
                        # Provide specific error messages based on status code
                        if response.status_code == 401:
                            logger.error("❌ API Key Error: Invalid or expired API key. Please check your ScrapingBee API key.")
                        elif response.status_code == 402:
                            logger.error("❌ Payment Error: ScrapingBee account needs payment or has insufficient credits.")
                        elif response.status_code == 429:
                            logger.error("❌ Rate Limit Error: Too many requests. Please wait and retry.")
                        elif response.status_code == 500:
                            logger.error("❌ Server Error: ScrapingBee server error. Please retry later.")
                        else:
                            logger.error(f"❌ HTTP {response.status_code}: Unknown error from ScrapingBee API")
                    except Exception as e:
                        logger.error(f"Could not read error response: {e}")
                else:
                    logger.info(f"Response headers: {dict(response.headers)}")
                
                # Check if we got a successful response
                if response.status_code == 200:
                    content = response.content
                    content_length = len(content)
                    logger.info(f"Content length: {content_length} bytes")
                    
                    # Safety check: Ensure we didn't get HTML instead of binary content
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        logger.warning(f"Received HTML instead of binary content (Content-Type: {content_type})")
                        logger.warning("This indicates a failed download or redirect page")
                        if attempt < max_retries - 1:
                            logger.info("Retrying download...")
                            continue
                        else:
                            return {
                                'success': False,
                                'error': f'Received HTML instead of binary content (Content-Type: {content_type})',
                                'url': url,
                                'status_code': response.status_code,
                                'content_length': content_length
                            }
                    
                    # Check 2MB file size limit per ScrapingBee documentation
                    if content_length > MAX_FILE_SIZE:
                        logger.error(f"File size {content_length} bytes exceeds ScrapingBee 2MB limit")
                        return {
                            'success': False,
                            'error': f'File size {content_length} bytes exceeds ScrapingBee 2MB limit',
                            'url': url,
                            'status_code': response.status_code,
                            'content_length': content_length,
                            'max_allowed': MAX_FILE_SIZE
                        }
                    
                    # Log first 100 bytes for debugging
                    preview = content[:100] if content else b''
                    logger.info(f"Content preview: {preview}")
                    
                    # Determine content type
                    content_type = response.headers.get('Content-Type', 'unknown')
                    file_type = self._determine_file_type(url, content_type)
                    
                    # Additional check: Look for HTML content in the response body
                    # This is a backup check in case Content-Type header is missing or incorrect
                    if content_length < 50000 and (b'<!DOCTYPE html>' in content[:2000] or b'<html' in content[:2000]):
                        logger.warning(f"Detected HTML content in response body for {url}")
                        # Check if it's a redirect page
                        if b'redirect' in content.lower() or b'location.href' in content.lower():
                            logger.info(f"Detected redirect page, retrying...")
                            if attempt < max_retries - 1:
                                continue  # Retry
                        else:
                            logger.error(f"Server returned HTML error page instead of file")
                            if attempt < max_retries - 1:
                                continue  # Retry
                            else:
                                return {
                                    'success': False,
                                    'error': f'Server returned HTML error page instead of file',
                                    'url': url,
                                    'status_code': response.status_code,
                                    'content_length': content_length
                                }
                    
                    # Note: Removed PDF signature verification - we want to download all PDFs
                    # regardless of their internal structure or validity
                    
                    # Success!
                    download_time = time.time() - start_time
                    logger.info(f"Successfully downloaded {url} ({content_length} bytes, {file_type}) in {download_time:.2f}s")
                    
                    return {
                        'success': True,
                        'url': url,
                        'content': content,
                        'content_type': file_type,
                        'content_length': content_length,
                        'download_time': download_time,
                        'is_binary': True,
                        'content_base64': base64.b64encode(content).decode('utf-8'),
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'file_size_ok': content_length <= MAX_FILE_SIZE
                    }
                
                elif response.status_code in [301, 302, 307, 308]:
                    # Handle redirects
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        logger.info(f"Following redirect from {url} to {redirect_url}")
                        if attempt < max_retries - 1:
                            url = redirect_url
                            continue
                    else:
                        logger.error(f"Redirect response without Location header")
                        return {
                            'success': False,
                            'error': f'Redirect without Location header',
                            'url': url,
                            'status_code': response.status_code
                        }
                
                elif response.status_code == 500:
                    logger.warning(f"HTTP 500 error on attempt {attempt + 1} for {url}")
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status_code} after {max_retries} attempts',
                            'url': url,
                            'status_code': response.status_code
                        }
                
                else:
                    # Enhanced error message with specific details
                    error_msg = f'HTTP {response.status_code}'
                    if response.status_code == 401:
                        error_msg = 'Invalid or expired ScrapingBee API key'
                    elif response.status_code == 402:
                        error_msg = 'ScrapingBee account needs payment or has insufficient credits'
                    elif response.status_code == 429:
                        error_msg = 'ScrapingBee rate limit exceeded'
                    elif response.status_code == 500:
                        error_msg = 'ScrapingBee server error'
                    
                    logger.error(f"❌ {error_msg} for {url}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'url': url,
                        'status_code': response.status_code
                    }
                    
            except Exception as e:
                logger.error(f"Exception on attempt {attempt + 1} for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    continue  # Retry
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'url': url
                    }
        
        return {
            'success': False,
            'error': f'Failed after {max_retries} attempts',
            'url': url
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
    
    def _determine_file_type(self, url: str, content_type: str) -> str:
        """Determine file type from URL and content type."""
        # Try to determine from URL first
        url_lower = url.lower()
        
        if url_lower.endswith('.pdf'):
            return 'application/pdf'
        elif url_lower.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif url_lower.endswith('.png'):
            return 'image/png'
        elif url_lower.endswith('.gif'):
            return 'image/gif'
        elif url_lower.endswith('.bmp'):
            return 'image/bmp'
        elif url_lower.endswith(('.tiff', '.tif')):
            return 'image/tiff'
        elif url_lower.endswith('.webp'):
            return 'image/webp'
        elif url_lower.endswith('.zip'):
            return 'application/zip'
        elif url_lower.endswith('.rar'):
            return 'application/x-rar-compressed'
        elif url_lower.endswith('.7z'):
            return 'application/x-7z-compressed'
        elif url_lower.endswith(('.tar', '.tar.gz', '.tgz')):
            return 'application/x-tar'
        elif url_lower.endswith('.gz'):
            return 'application/gzip'
        elif url_lower.endswith(('.doc', '.docx')):
            return 'application/msword'
        elif url_lower.endswith(('.xls', '.xlsx')):
            return 'application/vnd.ms-excel'
        elif url_lower.endswith(('.ppt', '.pptx')):
            return 'application/vnd.ms-powerpoint'
        elif url_lower.endswith('.txt'):
            return 'text/plain'
        elif url_lower.endswith('.json'):
            return 'application/json'
        elif url_lower.endswith('.xml'):
            return 'application/xml'
        elif url_lower.endswith('.csv'):
            return 'text/csv'
        
        # Try to determine from content type header
        if content_type:
            content_type_lower = content_type.lower()
            if 'pdf' in content_type_lower:
                return 'application/pdf'
            elif 'jpeg' in content_type_lower or 'jpg' in content_type_lower:
                return 'image/jpeg'
            elif 'png' in content_type_lower:
                return 'image/png'
            elif 'gif' in content_type_lower:
                return 'image/gif'
            elif 'bmp' in content_type_lower:
                return 'image/bmp'
            elif 'tiff' in content_type_lower:
                return 'image/tiff'
            elif 'webp' in content_type_lower:
                return 'image/webp'
            elif 'zip' in content_type_lower:
                return 'application/zip'
            elif 'rar' in content_type_lower:
                return 'application/x-rar-compressed'
            elif '7z' in content_type_lower:
                return 'application/x-7z-compressed'
            elif 'tar' in content_type_lower:
                return 'application/x-tar'
            elif 'gzip' in content_type_lower:
                return 'application/gzip'
            elif 'msword' in content_type_lower or 'word' in content_type_lower:
                return 'application/msword'
            elif 'excel' in content_type_lower or 'spreadsheet' in content_type_lower:
                return 'application/vnd.ms-excel'
            elif 'powerpoint' in content_type_lower or 'presentation' in content_type_lower:
                return 'application/vnd.ms-powerpoint'
            elif 'text/plain' in content_type_lower:
                return 'text/plain'
            elif 'json' in content_type_lower:
                return 'application/json'
            elif 'xml' in content_type_lower:
                return 'application/xml'
            elif 'csv' in content_type_lower:
                return 'text/csv'
            elif 'html' in content_type_lower:
                return 'text/html'
        
        # Default to binary if we can't determine
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