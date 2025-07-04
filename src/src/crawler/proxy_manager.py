"""
Proxy manager for handling ScraperAPI and direct requests.
"""

import requests
import random
import time
import logging
import urllib3
from typing import Optional, Dict, Any
from .utils import rotate_user_agent

# Suppress SSL warnings for ScraperAPI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy requests and fallback strategies."""
    
    def __init__(self, api_key: str, use_proxy: bool = True, scraperapi_base: str = "http://api.scraperapi.com/"):
        self.api_key = api_key
        self.use_proxy = use_proxy
        self.scraperapi_base = scraperapi_base
        self.session = requests.Session()
        
        # Performance tracking
        self.proxy_requests = 0
        self.proxy_failures = 0
        
        # Connection pooling
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
    
    def make_request(self, url: str, is_binary: bool = False, timeout: int = 15) -> requests.Response:
        """Make a request through proxy or direct connection."""
        if not self.use_proxy:
            return self._make_direct_request(url, is_binary, timeout)
        
        return self._make_proxy_request(url, is_binary, timeout)
    
    def _make_proxy_request(self, url: str, is_binary: bool = False, timeout: int = 15) -> requests.Response:
        """Make a request through ScraperAPI proxy using the correct format."""
        self.proxy_requests += 1
        
        # Build ScraperAPI URL with parameters
        proxy_url = f"{self.scraperapi_base}?api_key={self.api_key}&url={url}&render=true&country_code=us&premium=true"
        
        # Enhanced headers for better success rate
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            logger.debug(f"Making proxy request for {url}")
            response = self.session.get(
                proxy_url, 
                headers=headers,
                timeout=timeout, 
                stream=is_binary,
                verify=False  # Disable SSL verification for ScraperAPI
            )
            
            if response.status_code == 200:
                logger.info(f"Proxy request successful for {url}")
                return response
            else:
                logger.warning(f"Proxy returned status {response.status_code} for {url}")
                raise requests.exceptions.RequestException(f"HTTP {response.status_code}")
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            logger.warning(f"Proxy request failed for {url}: {e}")
            self.proxy_failures += 1
            
            # Fallback to direct request
            logger.info(f"Falling back to direct request for {url}")
            return self._make_direct_request(url, is_binary, timeout)
    
    def _make_direct_request(self, url: str, is_binary: bool = False, timeout: int = 15) -> requests.Response:
        """Make a direct request with enhanced configuration to bypass 403 errors."""
        # Enhanced headers to mimic real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Add referer for better success rate
        if 'livemint.com' in url:
            headers['Referer'] = 'https://www.google.com/'
        elif 'cbd.ae' in url:
            headers['Referer'] = 'https://www.google.com/'
        
        try:
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=timeout, 
                stream=is_binary,
                allow_redirects=True
            )
            
            # If we get 403, try with different approach
            if response.status_code == 403:
                logger.warning(f"Got 403 for {url}, trying with different headers")
                return self._retry_with_different_headers(url, is_binary, timeout)
            
            response.raise_for_status()
            logger.info(f"Direct request successful for {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Direct request failed for {url}: {e}")
            raise
    
    def _retry_with_different_headers(self, url: str, is_binary: bool = False, timeout: int = 15) -> requests.Response:
        """Retry request with different headers to bypass 403."""
        # Alternative headers that might work
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.bing.com/',
        }
        
        try:
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=timeout, 
                stream=is_binary,
                allow_redirects=True
            )
            
            if response.status_code == 403:
                logger.warning(f"Still getting 403 for {url}, this site may require JavaScript")
                raise requests.exceptions.RequestException("Site requires JavaScript rendering")
            
            response.raise_for_status()
            logger.info(f"Retry request successful for {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Retry request failed for {url}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get proxy usage statistics."""
        return {
            'proxy_requests': self.proxy_requests,
            'proxy_failures': self.proxy_failures,
            'success_rate': round(((self.proxy_requests - self.proxy_failures) / max(1, self.proxy_requests)) * 100, 2)
        }
    
    def close(self):
        """Close the session."""
        self.session.close() 