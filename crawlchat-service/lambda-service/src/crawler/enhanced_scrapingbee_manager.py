"""
Enhanced ScrapingBee Manager with Progressive Proxy Strategy
Implements cost-effective crawling with fallback to higher-credit modes only when needed.
"""

import requests
import logging
import time
import json
import os
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlparse
import urllib3
from dataclasses import dataclass
from enum import Enum

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class ProxyMode(Enum):
    """Proxy modes with their credit costs."""
    STANDARD = "standard"      # 5 credits
    PREMIUM = "premium"        # 25 credits  
    STEALTH = "stealth"        # 75 credits

@dataclass
class ProxyConfig:
    """Configuration for each proxy mode."""
    mode: ProxyMode
    credits_per_request: int
    timeout: int
    wait_time: int
    retry_count: int
    description: str

class EnhancedScrapingBeeManager:
    """
    Enhanced ScrapingBee manager with progressive proxy strategy.
    Tries lower-cost options first, only using high-credit modes when necessary.
    """
    
    def __init__(self, api_key: str, base_options: Dict[str, Any] = None):
        self.api_key = api_key
        self.base_url = "https://app.scrapingbee.com/api/v1/"
        self.session = requests.Session()
        
        # Proxy configurations
        self.proxy_configs = {
            ProxyMode.STANDARD: ProxyConfig(
                mode=ProxyMode.STANDARD,
                credits_per_request=5,
                timeout=30,
                wait_time=2000,
                retry_count=2,
                description="Standard proxy (5 credits)"
            ),
            ProxyMode.PREMIUM: ProxyConfig(
                mode=ProxyMode.PREMIUM,
                credits_per_request=25,
                timeout=45,
                wait_time=3000,
                retry_count=2,
                description="Premium proxy (25 credits)"
            ),
            ProxyMode.STEALTH: ProxyConfig(
                mode=ProxyMode.STEALTH,
                credits_per_request=75,
                timeout=60,
                wait_time=5000,
                retry_count=1,
                description="Stealth proxy (75 credits)"
            )
        }
        
        # Base options
        self.base_options = base_options or {
            "country_code": "us",
            "block_ads": True,
            "block_resources": False,
        }
        
        # Performance tracking
        self.request_stats = {
            ProxyMode.STANDARD: {"requests": 0, "successes": 0, "failures": 0},
            ProxyMode.PREMIUM: {"requests": 0, "successes": 0, "failures": 0},
            ProxyMode.STEALTH: {"requests": 0, "successes": 0, "failures": 0},
        }
        
        # Site-specific requirements cache
        self.site_requirements = {}
        
        # Connection pooling
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
    
    def make_progressive_request(self, url: str, content_checker=None, 
                               force_mode: Optional[ProxyMode] = None) -> requests.Response:
        """
        Make a progressive request: Standard → Premium → Stealth
        Only uses higher-cost modes if lower-cost modes fail.
        
        Args:
            url: Target URL to scrape
            content_checker: Function to validate content completeness
            force_mode: Force specific proxy mode (for testing)
        
        Returns:
            requests.Response object
        """
        domain = urlparse(url).netloc
        
        # Check if we know this site requires specific mode
        if domain in self.site_requirements and not force_mode:
            required_mode = self.site_requirements[domain]
            logger.info(f"Site {domain} requires {required_mode.value} mode")
            return self._make_request_with_mode(url, required_mode, content_checker)
        
        # Progressive strategy: Standard → Premium → Stealth
        modes_to_try = [ProxyMode.STANDARD, ProxyMode.PREMIUM, ProxyMode.STEALTH]
        
        if force_mode:
            modes_to_try = [force_mode]
        
        for mode in modes_to_try:
            try:
                logger.info(f"Trying {mode.value} mode for {url}")
                response = self._make_request_with_mode(url, mode, content_checker)
                
                if response.status_code == 200:
                    # Cache successful mode for this domain
                    if not force_mode:
                        self.site_requirements[domain] = mode
                        logger.info(f"Cached {mode.value} mode for {domain}")
                    
                    return response
                else:
                    logger.warning(f"{mode.value} mode failed with status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"{mode.value} mode failed: {e}")
                continue
        
        # All modes failed
        raise requests.exceptions.RequestException(f"All proxy modes failed for {url}")
    
    def _make_request_with_mode(self, url: str, mode: ProxyMode, 
                               content_checker=None) -> requests.Response:
        """Make request with specific proxy mode."""
        config = self.proxy_configs[mode]
        
        for attempt in range(config.retry_count):
            try:
                params = self._get_params_for_mode(url, mode)
                headers = self._get_headers()
                
                logger.debug(f"Making {mode.value} request (attempt {attempt + 1})")
                
                response = self.session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=config.timeout,
                    verify=False
                )
                
                # Update statistics
                self.request_stats[mode]["requests"] += 1
                
                if response.status_code == 200:
                    # Check content if checker provided
                    if content_checker and not content_checker(response.text, url):
                        logger.info(f"Content incomplete for {mode.value} mode, retrying...")
                        continue
                    
                    self.request_stats[mode]["successes"] += 1
                    return response
                else:
                    self.request_stats[mode]["failures"] += 1
                    logger.warning(f"{mode.value} mode failed with status {response.status_code}")
                    
            except Exception as e:
                self.request_stats[mode]["failures"] += 1
                logger.warning(f"{mode.value} mode attempt {attempt + 1} failed: {e}")
                
                if attempt < config.retry_count - 1:
                    time.sleep(1)  # Brief delay before retry
                    continue
        
        raise requests.exceptions.RequestException(f"{mode.value} mode failed after {config.retry_count} attempts")
    
    def _get_params_for_mode(self, url: str, mode: ProxyMode) -> Dict[str, Any]:
        """Get ScrapingBee parameters for specific proxy mode."""
        config = self.proxy_configs[mode]
        
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true",
            "wait": str(config.wait_time),
        }
        
        # Add mode-specific parameters
        if mode == ProxyMode.STANDARD:
            params.update({
                "premium_proxy": "false",
                "stealth_proxy": "false",
            })
        elif mode == ProxyMode.PREMIUM:
            params.update({
                "premium_proxy": "true",
                "stealth_proxy": "false",
            })
        elif mode == ProxyMode.STEALTH:
            params.update({
                "premium_proxy": "false",
                "stealth_proxy": "true",
            })
        
        # Add base options
        params.update(self.base_options)
        
        return params
    
    def make_js_scenario_request(self, url: str, scenario: Dict[str, Any], 
                                mode: ProxyMode = ProxyMode.PREMIUM) -> requests.Response:
        """
        Make request with JavaScript scenario (click, scroll, wait, etc.)
        
        Args:
            url: Target URL
            scenario: JavaScript scenario instructions
            mode: Proxy mode to use (default: Premium for JS scenarios)
        
        Returns:
            requests.Response object
        """
        config = self.proxy_configs[mode]
        
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true",
            "js_scenario": json.dumps(scenario),
            "wait": str(config.wait_time),
        }
        
        # Add mode-specific parameters
        if mode == ProxyMode.STANDARD:
            params.update({"premium_proxy": "false", "stealth_proxy": "false"})
        elif mode == ProxyMode.PREMIUM:
            params.update({"premium_proxy": "true", "stealth_proxy": "false"})
        elif mode == ProxyMode.STEALTH:
            params.update({"premium_proxy": "false", "stealth_proxy": "true"})
        
        params.update(self.base_options)
        
        logger.info(f"Making JS scenario request with {mode.value} mode")
        
        response = self.session.get(
            self.base_url,
            params=params,
            headers=self._get_headers(),
            timeout=config.timeout,
            verify=False
        )
        
        self.request_stats[mode]["requests"] += 1
        if response.status_code == 200:
            self.request_stats[mode]["successes"] += 1
        else:
            self.request_stats[mode]["failures"] += 1
        
        return response
    
    def download_file(self, url: str, file_type: str = "auto") -> bytes:
        """
        Download file (PDF, image, etc.) from URL.
        
        Args:
            url: File URL
            file_type: File type ("pdf", "image", "auto")
        
        Returns:
            File content as bytes
        """
        # For file downloads, use standard mode (no JS needed)
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "false",  # Files don't need JS rendering
            "premium_proxy": "false",
            "stealth_proxy": "false",
        }
        
        params.update(self.base_options)
        
        logger.info(f"Downloading file from {url}")
        
        response = self.session.get(
            self.base_url,
            params=params,
            headers=self._get_headers(),
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise requests.exceptions.RequestException(f"File download failed: {response.status_code}")
    
    def take_screenshot(self, url: str, full_page: bool = True, 
                       selector: str = None, mode: ProxyMode = ProxyMode.PREMIUM) -> bytes:
        """
        Take screenshot of webpage.
        
        Args:
            url: Target URL
            full_page: Take full page screenshot
            selector: CSS selector for specific element
            mode: Proxy mode to use
        
        Returns:
            Screenshot as PNG bytes
        """
        config = self.proxy_configs[mode]
        
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true",
            "screenshot": "true",
            "wait": str(config.wait_time),
        }
        
        if full_page:
            params["screenshot_full_page"] = "true"
        
        if selector:
            params["screenshot_selector"] = selector
        
        # Add mode-specific parameters
        if mode == ProxyMode.STANDARD:
            params.update({"premium_proxy": "false", "stealth_proxy": "false"})
        elif mode == ProxyMode.PREMIUM:
            params.update({"premium_proxy": "true", "stealth_proxy": "false"})
        elif mode == ProxyMode.STEALTH:
            params.update({"premium_proxy": "false", "stealth_proxy": "true"})
        
        params.update(self.base_options)
        
        logger.info(f"Taking screenshot with {mode.value} mode")
        
        response = self.session.get(
            self.base_url,
            params=params,
            headers=self._get_headers(),
            timeout=config.timeout,
            verify=False
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise requests.exceptions.RequestException(f"Screenshot failed: {response.status_code}")
    
    def set_country_code(self, country_code: str):
        """Set country code for proxy geolocation."""
        self.base_options["country_code"] = country_code
        logger.info(f"Set country code to {country_code}")
    
    def set_custom_headers(self, headers: Dict[str, str]):
        """Set custom headers for requests."""
        # Note: ScrapingBee doesn't support custom headers directly
        # This would need to be implemented differently
        logger.warning("Custom headers not supported in current implementation")
    
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
        """Get comprehensive usage statistics."""
        total_requests = sum(stats["requests"] for stats in self.request_stats.values())
        total_successes = sum(stats["successes"] for stats in self.request_stats.values())
        total_failures = sum(stats["failures"] for stats in self.request_stats.values())
        
        stats = {
            'total_requests': total_requests,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'success_rate': round((total_successes / max(1, total_requests)) * 100, 2),
            'mode_breakdown': {},
            'site_requirements': self.site_requirements,
        }
        
        # Add breakdown by mode
        for mode, mode_stats in self.request_stats.items():
            mode_requests = mode_stats["requests"]
            if mode_requests > 0:
                stats['mode_breakdown'][mode.value] = {
                    'requests': mode_requests,
                    'successes': mode_stats["successes"],
                    'failures': mode_stats["failures"],
                    'success_rate': round((mode_stats["successes"] / mode_requests) * 100, 2),
                    'credits_used': mode_requests * self.proxy_configs[mode].credits_per_request,
                }
        
        return stats
    
    def get_cost_estimate(self) -> Dict[str, float]:
        """Get cost estimate based on usage."""
        total_cost = 0
        mode_costs = {}
        
        for mode, stats in self.request_stats.items():
            config = self.proxy_configs[mode]
            # Approximate cost per credit (adjust based on your plan)
            cost_per_credit = 0.001  # $0.001 per credit (example)
            
            credits_used = stats["requests"] * config.credits_per_request
            mode_cost = credits_used * cost_per_credit
            
            mode_costs[mode.value] = round(mode_cost, 4)
            total_cost += mode_cost
        
        return {
            'total_cost': round(total_cost, 4),
            'mode_costs': mode_costs,
            'credits_used': sum(stats["requests"] * self.proxy_configs[mode].credits_per_request 
                              for mode, stats in self.request_stats.items()),
        }
    
    def save_site_requirements(self, filename: str = "/tmp/site_requirements.json"):
        """Save site requirements to file."""
        try:
            # Convert enum to string for JSON serialization
            serializable_requirements = {
                domain: mode.value for domain, mode in self.site_requirements.items()
            }
            
            with open(filename, 'w') as f:
                json.dump(serializable_requirements, f, indent=2)
            logger.info(f"Site requirements saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save site requirements: {e}")
    
    def load_site_requirements(self, filename: str = "/tmp/site_requirements.json"):
        """Load site requirements from file."""
        try:
            with open(filename, 'r') as f:
                requirements = json.load(f)
            
            # Convert string back to enum
            self.site_requirements = {
                domain: ProxyMode(mode) for domain, mode in requirements.items()
            }
            logger.info(f"Site requirements loaded from {filename}")
        except Exception as e:
            logger.warning(f"Failed to load site requirements: {e}")
    
    def reset_stats(self):
        """Reset all statistics."""
        for mode in self.request_stats:
            self.request_stats[mode] = {"requests": 0, "successes": 0, "failures": 0}
        logger.info("Statistics reset")
    
    def close(self):
        """Close the session."""
        self.session.close()


# Pre-built JavaScript scenarios
class JavaScriptScenarios:
    """Pre-built JavaScript scenarios for common interactions."""
    
    @staticmethod
    def load_more_content(button_selector: str = "#load-more", wait_selector: str = ".content-loaded"):
        """Load more content scenario."""
        return {
            "instructions": [
                {"wait": 2000},
                {"click": button_selector},
                {"wait_for": wait_selector},
                {"wait": 1000}
            ]
        }
    
    @staticmethod
    def infinite_scroll(max_scrolls: int = 5, delay: int = 1000):
        """Infinite scroll scenario."""
        return {
            "instructions": [
                {"infinite_scroll": {"max_count": max_scrolls, "delay": delay}}
            ]
        }
    
    @staticmethod
    def click_and_wait(selector: str, wait_time: int = 2000):
        """Click element and wait scenario."""
        return {
            "instructions": [
                {"click": selector},
                {"wait": wait_time}
            ]
        }
    
    @staticmethod
    def scroll_and_click(scroll_amount: int = 1000, selector: str = None):
        """Scroll and optionally click scenario."""
        instructions = [
            {"scroll_y": scroll_amount},
            {"wait": 1000}
        ]
        
        if selector:
            instructions.append({"click": selector})
        
        return {"instructions": instructions}
    
    @staticmethod
    def wait_for_element(selector: str, timeout: int = 10000):
        """Wait for element to appear scenario."""
        return {
            "instructions": [
                {"wait_for": selector},
                {"wait": 1000}
            ]
        }


# Content checkers for different site types
class ContentCheckers:
    """Content checkers for validating scraped content."""
    
    @staticmethod
    def news_site_checker(html: str, url: str) -> bool:
        """Check if news site content is complete."""
        indicators = [
            '<article', '<div class="article"', '<div class="content"',
            '<div class="story"', '<h1', '<p>'
        ]
        
        if len(html) < 5000:
            return False
        
        found_indicators = sum(1 for indicator in indicators if indicator in html)
        return found_indicators >= 2
    
    @staticmethod
    def ecommerce_checker(html: str, url: str) -> bool:
        """Check if ecommerce site content is complete."""
        indicators = [
            'price', 'add to cart', 'buy now', 'product', 'shopping',
            'currency', 'stock', 'availability'
        ]
        
        found_indicators = sum(1 for indicator in indicators if indicator.lower() in html.lower())
        return found_indicators >= 3
    
    @staticmethod
    def financial_checker(html: str, url: str) -> bool:
        """Check if financial site content is complete."""
        indicators = [
            'financial', 'report', 'statement', 'revenue', 'profit',
            'earnings', 'quarterly', 'annual', 'balance sheet'
        ]
        
        if len(html) < 10000:
            return False
        
        found_indicators = sum(1 for indicator in indicators if indicator.lower() in html.lower())
        return found_indicators >= 4
    
    @staticmethod
    def generic_checker(html: str, url: str) -> bool:
        """Generic content checker."""
        if len(html) < 2000:
            return False
        
        if '<body' not in html:
            return False
        
        if html.count('<p>') < 2:
            return False
        
        return True 