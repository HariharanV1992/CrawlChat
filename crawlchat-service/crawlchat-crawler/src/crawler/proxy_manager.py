"""
Proxy Manager for ScrapingBee integration with smart JavaScript rendering control.
"""

import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from .smart_scrapingbee_manager import SmartScrapingBeeManager, ContentCheckers

logger = logging.getLogger(__name__)

class ScrapingBeeProxyManager:
    """
    Proxy manager using ScrapingBee with smart JavaScript rendering control.
    """
    
    def __init__(self, api_key: str, base_options: Dict[str, Any] = None):
        self.api_key = api_key
        self.smart_manager = SmartScrapingBeeManager(api_key, base_options)
        
        # Default options for different site types
        self.site_options = {
            'news': {
                'premium_proxy': True,
                'country_code': 'us',
                'block_ads': True,
                'block_resources': False,
            },
            'stock': {
                'premium_proxy': True,
                'country_code': 'us',
                'block_ads': True,
                'block_resources': False,
            },
            'financial': {
                'premium_proxy': True,
                'country_code': 'us',
                'block_ads': True,
                'block_resources': False,
            }
        }
    
    async def make_request(self, url: str, site_type: str = 'generic', timeout: int = 30) -> aiohttp.ClientResponse:
        """
        Make a smart request using ScrapingBee with automatic JS rendering control.
        
        Args:
            url: Target URL to scrape
            site_type: Type of site ('news', 'stock', 'financial', 'generic')
            timeout: Request timeout in seconds
        
        Returns:
            aiohttp.ClientResponse object
        """
        # Select content checker based on site type
        content_checker = self._get_content_checker(site_type)
        
        # Update options for site type
        if site_type in self.site_options:
            self.smart_manager.base_options.update(self.site_options[site_type])
        
        try:
            # Use the smart manager to make the request
            response = self.smart_manager.make_smart_request(url, content_checker, timeout)
            
            # Convert requests.Response to aiohttp.ClientResponse-like object
            return self._wrap_response(response)
            
        except Exception as e:
            logger.error(f"ScrapingBee request failed for {url}: {e}")
            raise
    
    def _get_content_checker(self, site_type: str):
        """Get appropriate content checker for site type."""
        checkers = {
            'news': ContentCheckers.news_site_checker,
            'stock': ContentCheckers.stock_site_checker,
            'financial': ContentCheckers.financial_report_checker,
            'generic': ContentCheckers.generic_checker,
        }
        return checkers.get(site_type, ContentCheckers.generic_checker)
    
    def _wrap_response(self, requests_response):
        """Wrap requests.Response to be compatible with aiohttp.ClientResponse."""
        class WrappedResponse:
            def __init__(self, response):
                self._response = response
                self.status = response.status_code
                self.headers = response.headers
                self.url = response.url
            
            async def text(self):
                return self._response.text
            
            async def read(self):
                return self._response.content
            
            async def json(self):
                return self._response.json()
            
            def close(self):
                pass
        
        return WrappedResponse(requests_response)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.smart_manager.get_stats()
    
    def get_cost_estimate(self) -> Dict[str, float]:
        """Get cost estimate."""
        return self.smart_manager.get_cost_estimate()
    
    def save_site_requirements(self, filename: str = "/tmp/site_js_requirements.json"):
        """Save site JS requirements."""
        self.smart_manager.save_site_requirements(filename)
    
    def load_site_requirements(self, filename: str = "/tmp/site_js_requirements.json"):
        """Load site JS requirements."""
        self.smart_manager.load_site_requirements(filename)
    
    def close(self):
        """Close the manager."""
        self.smart_manager.close()


# Legacy compatibility - keep the old class name for existing code
ProxyManager = ScrapingBeeProxyManager 