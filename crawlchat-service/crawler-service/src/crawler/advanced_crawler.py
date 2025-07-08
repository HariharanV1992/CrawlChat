"""
Advanced web crawler with ScrapingBee integration and smart JavaScript rendering control.
"""

import asyncio
import logging
import time
import hashlib
import os
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiofiles
from .proxy_manager import ScrapingBeeProxyManager
from .link_extractor import LinkExtractor
from .file_downloader import FileDownloader
from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class AdvancedCrawler:
    """
    Advanced web crawler with ScrapingBee integration and smart JavaScript rendering control.
    """
    
    def __init__(self, api_key: str, base_url: str, output_dir: str = "crawled_data", max_depth: int = 2, 
                 max_pages: int = 50, delay: float = 1.0, site_type: str = 'generic'):
        self.api_key = api_key
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.site_type = site_type
        
        # Extract domain from base_url
        self.domain = urlparse(base_url).netloc
        
        # Initialize components
        self.proxy_manager = ScrapingBeeProxyManager(api_key)
        self.link_extractor = LinkExtractor(self.domain)
        self.file_downloader = FileDownloader(self.output_dir)
        self.settings_manager = SettingsManager()
        
        # Crawling state
        self.visited_urls: Set[str] = set()
        self.downloaded_files: List[str] = []
        self.failed_urls: List[str] = []
        self.current_depth = 0
        
        # Performance tracking
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    async def crawl(self, start_url: str) -> Dict[str, Any]:
        """
        Crawl a website starting from the given URL.
        
        Args:
            start_url: The starting URL for crawling
        
        Returns:
            Dictionary with crawling results and statistics
        """
        logger.info(f"Starting crawl from {start_url} with site type: {self.site_type}")
        
        try:
            # Detect site type if not specified
            if self.site_type == 'generic':
                self.site_type = self._detect_site_type(start_url)
                logger.info(f"Detected site type: {self.site_type}")
            
            # Load existing site requirements
            self.proxy_manager.load_site_requirements()
            
            # Start crawling
            await self._crawl_recursive(start_url, depth=0)
            
            # Save site requirements for future use
            self.proxy_manager.save_site_requirements()
            
            # Generate results
            results = self._generate_results()
            
            logger.info(f"Crawling completed. Downloaded {len(self.downloaded_files)} files.")
            return results
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            raise
        finally:
            self.proxy_manager.close()
    
    async def _crawl_recursive(self, url: str, depth: int):
        """Recursively crawl URLs up to max_depth."""
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        self.current_depth = depth
        
        try:
            logger.info(f"Crawling {url} at depth {depth}")
            
            # Download the page
            content = await self._download_page(url)
            if not content:
                self.failed_urls.append(url)
                return
            
            # Save the page
            await self._save_page(url, content)
            self.downloaded_files.append(url)
            self.successful_requests += 1
            
            # Extract links for next level
            if depth < self.max_depth:
                page_links, document_links = self.link_extractor.extract_links(content, url, self.visited_urls)
                links = page_links + document_links
                logger.info(f"Found {len(links)} links on {url}")
                
                # Crawl links with delay
                for link in links[:10]:  # Limit links per page
                    if len(self.visited_urls) >= self.max_pages:
                        break
                    
                    await asyncio.sleep(self.delay)
                    await self._crawl_recursive(link, depth + 1)
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            self.failed_urls.append(url)
    
    async def _download_page(self, url: str) -> Optional[str]:
        """Download a page using the smart proxy manager."""
        self.total_requests += 1
        
        try:
            response = await self.proxy_manager.make_request(url, self.site_type)
            
            if response.status == 200:
                content = await response.text()
                logger.debug(f"Successfully downloaded {url} ({len(content)} bytes)")
                return content
            else:
                logger.warning(f"Failed to download {url}: HTTP {response.status}")
                return None
        
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    async def _save_page(self, url: str, content: str):
        """Save a page to the output directory."""
        try:
            # Create filename from URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            path = parsed_url.path.strip('/') or 'index'
            
            # Clean filename
            filename = path.replace('/', '_').replace('?', '_').replace('&', '_')
            if len(filename) > 100:
                filename = filename[:100]
            
            # Add timestamp to avoid conflicts
            timestamp = int(time.time())
            filename = f"document_{hashlib.md5(filename.encode()).hexdigest()}_{timestamp}.html"
            
            # Create domain directory
            domain_dir = os.path.join(self.output_dir, domain)
            os.makedirs(domain_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(domain_dir, filename)
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.debug(f"Saved {url} to {filepath}")
        
        except Exception as e:
            logger.error(f"Error saving {url}: {e}")
    
    def _detect_site_type(self, url: str) -> str:
        """Detect the type of website based on URL and domain."""
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        
        # News sites
        news_domains = ['news', 'times', 'post', 'tribune', 'herald', 'daily', 'weekly']
        if any(keyword in domain for keyword in news_domains):
            return 'news'
        
        # Stock/financial sites
        stock_domains = ['finance', 'market', 'stock', 'trading', 'investing', 'yahoo.com/finance']
        if any(keyword in domain or keyword in path for keyword in stock_domains):
            return 'stock'
        
        # Financial reports
        financial_keywords = ['financial', 'report', 'statement', 'earnings', 'quarterly', 'annual']
        if any(keyword in path for keyword in financial_keywords):
            return 'financial'
        
        return 'generic'
    
    def _generate_results(self) -> Dict[str, Any]:
        """Generate comprehensive crawling results."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Get proxy manager stats
        proxy_stats = self.proxy_manager.get_stats()
        cost_estimate = self.proxy_manager.get_cost_estimate()
        
        return {
            'crawling_stats': {
                'total_urls_visited': len(self.visited_urls),
                'successful_downloads': len(self.downloaded_files),
                'failed_urls': len(self.failed_urls),
                'max_depth_reached': self.current_depth,
                'duration_seconds': round(duration, 2),
                'pages_per_minute': round(len(self.downloaded_files) / (duration / 60), 2),
            },
            'proxy_stats': proxy_stats,
            'cost_estimate': cost_estimate,
            'site_type': self.site_type,
            'downloaded_files': self.downloaded_files,
            'failed_urls': self.failed_urls,
            'output_directory': self.output_dir,
        }
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time crawling statistics."""
        current_time = time.time()
        duration = current_time - self.start_time
        
        return {
            'urls_visited': len(self.visited_urls),
            'files_downloaded': len(self.downloaded_files),
            'failed_urls': len(self.failed_urls),
            'current_depth': self.current_depth,
            'duration_seconds': round(duration, 2),
            'proxy_stats': self.proxy_manager.get_stats(),
            'cost_estimate': self.proxy_manager.get_cost_estimate(),
        }