"""
Smart ScrapingBee Manager with efficient JavaScript rendering control.
"""

import requests
import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import urllib3
from .s3_cache_manager import S3CacheManager

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class SmartScrapingBeeManager:
    """
    Smart ScrapingBee manager that optimizes cost by using no-JS requests by default
    and only enabling JavaScript rendering when necessary.
    """
    
    def __init__(self, api_key: str, base_options: Dict[str, Any] = None):
        self.api_key = api_key
        self.base_url = "https://app.scrapingbee.com/api/v1/"
        self.session = requests.Session()
        
        # Default options (no-JS, cost-effective)
        self.base_options = base_options or {
            "premium_proxy": True,
            "country_code": "us",
            "block_ads": True,
            "block_resources": False,
        }
        
        # Performance tracking
        self.no_js_requests = 0
        self.js_requests = 0
        self.no_js_successes = 0
        self.js_successes = 0
        self.retry_with_js_count = 0
        
        # Site-specific JS requirements (cache)
        self.site_js_requirements = {}
        
        # S3 cache manager
        self.s3_cache = S3CacheManager()
        
        # Connection pooling
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
    
    def make_binary_request(self, url: str, timeout: int = 30) -> requests.Response:
        """
        Make a request specifically for binary files (PDFs, images, etc.).
        Uses no-JS rendering and proper headers for binary content.
        
        Args:
            url: Target URL to download
            timeout: Request timeout in seconds
        
        Returns:
            requests.Response object
        """
        logger.info(f"Making binary request for {url}")
        
        params = {
            "api_key": self.api_key,
            "url": url,
            # No JavaScript rendering for binary files
            "render_js": "false",
            # Don't block resources for binary files
            "block_resources": "false",
            # Use premium proxy for better reliability
            "premium_proxy": "true",
        }
        params.update(self.base_options)
        
        # Special headers for binary content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',  # Accept all content types
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        try:
            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=timeout,
                verify=False
            )
            
            logger.info(f"Binary request completed for {url}: status={response.status_code}, size={len(response.content)} bytes")
            return response
            
        except Exception as e:
            logger.error(f"Binary request failed for {url}: {e}")
            raise

    def make_smart_request(self, url: str, content_checker=None, timeout: int = 30) -> requests.Response:
        """
        Make a smart request that tries no-JS first, then retries with JS if needed.
        
        Args:
            url: Target URL to scrape
            content_checker: Function to check if content is complete (optional)
            timeout: Request timeout in seconds
        
        Returns:
            requests.Response object
        """
        domain = urlparse(url).netloc
        
        # Check if we know this site requires JS
        if domain in self.site_js_requirements and self.site_js_requirements[domain]:
            logger.debug(f"Site {domain} known to require JS, skipping no-JS attempt")
            return self._make_js_request(url, timeout)
        
        # Step 1: Try no-JS request first (cost-effective)
        try:
            logger.debug(f"Making no-JS request for {url}")
            response = self._make_no_js_request(url, timeout)
            self.no_js_requests += 1
            
            if response.status_code == 200:
                # Check if content is complete
                if content_checker is None or content_checker(response.text, url):
                    self.no_js_successes += 1
                    logger.info(f"No-JS request successful for {url}")
                    return response
                else:
                    logger.info(f"No-JS content incomplete for {url}, retrying with JS")
                    self.retry_with_js_count += 1
            else:
                logger.warning(f"No-JS request failed with status {response.status_code} for {url}")
        
        except Exception as e:
            logger.warning(f"No-JS request failed for {url}: {e}")
        
        # Step 2: Retry with JS rendering
        try:
            logger.debug(f"Making JS request for {url}")
            response = self._make_js_request(url, timeout)
            self.js_requests += 1
            
            if response.status_code == 200:
                self.js_successes += 1
                logger.info(f"JS request successful for {url}")
                
                # Cache that this site requires JS
                self.site_js_requirements[domain] = True
                
                return response
            else:
                logger.error(f"JS request failed with status {response.status_code} for {url}")
                raise requests.exceptions.RequestException(f"Both no-JS and JS requests failed for {url}")
        
        except Exception as e:
            logger.error(f"JS request failed for {url}: {e}")
            raise
    
    def _make_no_js_request(self, url: str, timeout: int = 30) -> requests.Response:
        """Make a no-JS request (cost-effective)."""
        params = {
            "api_key": self.api_key,
            "url": url,
        }
        params.update(self.base_options)
        
        headers = self._get_headers()
        
        response = self.session.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=timeout,
            verify=False
        )
        
        return response
    
    def _make_js_request(self, url: str, timeout: int = 30) -> requests.Response:
        """Make a JS-rendered request (higher cost)."""
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true",
            "wait": "3000",  # Wait 3 seconds for JS to load
        }
        params.update(self.base_options)
        
        headers = self._get_headers()
        
        response = self.session.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=timeout,
            verify=False
        )
        
        return response
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_requests = self.no_js_requests + self.js_requests
        total_successes = self.no_js_successes + self.js_successes
        
        return {
            'no_js_requests': self.no_js_requests,
            'js_requests': self.js_requests,
            'no_js_successes': self.no_js_successes,
            'js_successes': self.js_successes,
            'retry_with_js_count': self.retry_with_js_count,
            'total_requests': total_requests,
            'total_successes': total_successes,
            'success_rate': round((total_successes / max(1, total_requests)) * 100, 2),
            'js_usage_rate': round((self.js_requests / max(1, total_requests)) * 100, 2),
            'site_js_requirements': self.site_js_requirements,
        }
    
    def get_cost_estimate(self) -> Dict[str, float]:
        """Get cost estimate based on usage."""
        # ScrapingBee pricing (approximate)
        no_js_cost_per_request = 0.00049  # $0.00049 per no-JS request
        js_cost_per_request = 0.0049      # $0.0049 per JS request
        
        no_js_cost = self.no_js_requests * no_js_cost_per_request
        js_cost = self.js_requests * js_cost_per_request
        total_cost = no_js_cost + js_cost
        
        return {
            'no_js_cost': round(no_js_cost, 4),
            'js_cost': round(js_cost, 4),
            'total_cost': round(total_cost, 4),
            'cost_savings': round(no_js_cost, 4),  # Money saved by using no-JS first
        }
    
    def save_site_requirements(self, filename: str = None):
        """Save site JS requirements to S3."""
        try:
            self.s3_cache.save_site_js_requirements(self.site_js_requirements)
            logger.info("Site JS requirements saved to S3")
        except Exception as e:
            logger.error(f"Failed to save site requirements to S3: {e}")
    
    def load_site_requirements(self, filename: str = None):
        """Load site JS requirements from S3."""
        try:
            self.site_js_requirements = self.s3_cache.load_site_js_requirements()
            logger.info("Site JS requirements loaded from S3")
        except Exception as e:
            logger.warning(f"Failed to load site requirements from S3: {e}")
            # Initialize empty cache on error
            self.site_js_requirements = {}
    
    def close(self):
        """Close the session."""
        self.session.close()


# Pre-built content checkers for common scenarios
class ContentCheckers:
    """Pre-built content checkers for different types of websites."""
    
    @staticmethod
    def news_site_checker(html: str, url: str) -> bool:
        """Check if news site content is complete."""
        # Look for common news content indicators
        indicators = [
            '<article',
            '<div class="article"',
            '<div class="content"',
            '<div class="story"',
            '<h1',
            '<p>',  # Multiple paragraphs
        ]
        
        # Check if we have substantial content
        if len(html) < 5000:  # Too short for a news article
            return False
        
        # Check for multiple indicators
        found_indicators = sum(1 for indicator in indicators if indicator in html)
        return found_indicators >= 2
    
    @staticmethod
    def stock_site_checker(html: str, url: str) -> bool:
        """Check if stock site content is complete."""
        # Look for stock-related content
        indicators = [
            'price',
            'stock',
            'market',
            'trading',
            'volume',
            'market cap',
            'earnings',
            'dividend',
        ]
        
        # Check for stock data
        found_indicators = sum(1 for indicator in indicators if indicator.lower() in html.lower())
        return found_indicators >= 3
    
    @staticmethod
    def financial_report_checker(html: str, url: str) -> bool:
        """Check if financial report content is complete."""
        # Look for financial report indicators
        indicators = [
            'financial',
            'report',
            'statement',
            'revenue',
            'profit',
            'earnings',
            'quarterly',
            'annual',
            'balance sheet',
            'income statement',
        ]
        
        # Check for substantial financial content
        if len(html) < 10000:  # Financial reports are usually long
            return False
        
        found_indicators = sum(1 for indicator in indicators if indicator.lower() in html.lower())
        return found_indicators >= 4
    
    @staticmethod
    def generic_checker(html: str, url: str) -> bool:
        """Generic content checker."""
        # Basic checks
        if len(html) < 2000:  # Too short
            return False
        
        if '<body' not in html:  # No body tag
            return False
        
        if html.count('<p>') < 2:  # Not enough paragraphs
            return False
        
        return True 