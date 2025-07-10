"""
Enhanced Crawler Service for Lambda deployment
Implements max_doc_count logic and document extraction
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Add the crawler path to sys.path
crawler_path = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, crawler_path)

from advanced_crawler import AdvancedCrawler
from link_extractor import LinkExtractor

logger = logging.getLogger(__name__)

class EnhancedCrawlerService:
    """Enhanced crawler service with max document count support."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.documents = []
        self.visited_urls = set()
        
    def crawl_with_max_docs(self, base_url: str, max_doc_count: int = 1) -> Dict[str, Any]:
        """
        Crawl with max document count logic.
        
        Args:
            base_url: URL to crawl
            max_doc_count: Maximum number of documents to extract
            
        Returns:
            Dictionary with crawl results
        """
        logger.info(f"Starting enhanced crawl for {base_url} with max_doc_count: {max_doc_count}")
        
        # Reset state
        self.documents = []
        self.visited_urls = set()
        
        try:
            # Initialize crawler
            crawler = AdvancedCrawler(self.api_key)
            
            # Extract domain for link filtering
            domain = urlparse(base_url).netloc
            
            if max_doc_count == 1:
                # Single page crawl
                logger.info(f"Crawling single page: {base_url}")
                result = self._crawl_and_save_page(crawler, base_url, domain)
                if result:
                    self.documents.append(result)
            else:
                # Multi-page crawl with document extraction
                logger.info(f"Crawling with max_doc_count={max_doc_count}: {base_url}")
                self._crawl_recursive(crawler, base_url, domain, max_doc_count)
            
            # Close crawler
            crawler.close()
            
            # Prepare response
            response = {
                "success": True,
                "url": base_url,
                "documents_found": len(self.documents),
                "max_doc_count": max_doc_count,
                "documents": self.documents,
                "crawl_time": datetime.utcnow().isoformat(),
                "total_pages": len(self.visited_urls),
                "total_documents": len(self.documents)
            }
            
            logger.info(f"Enhanced crawl completed: {len(self.documents)} documents found")
            return response
            
        except Exception as e:
            logger.error(f"Enhanced crawl failed: {e}")
            return {
                "success": False,
                "url": base_url,
                "error": str(e),
                "documents_found": len(self.documents),
                "documents": self.documents
            }
    
    def _crawl_and_save_page(self, crawler: AdvancedCrawler, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Crawl a single page and save as document."""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        try:
            # Crawl the page
            result = crawler.crawl_url(url, content_type="generic")
            
            if not result.get('success'):
                logger.warning(f"Failed to crawl {url}: {result.get('error')}")
                return None
            
            # Extract title from HTML
            title = self._extract_title(result['content'])
            
            # Create document object
            document = {
                "id": f"doc_{len(self.documents) + 1}",
                "url": url,
                "title": title,
                "content": result['content'],
                "content_type": "html",
                "content_length": result.get('content_length', 0),
                "crawl_time": result.get('crawl_time', 0),
                "status_code": result.get('status_code', 0),
                "headers": result.get('headers', {}),
                "extracted_at": datetime.utcnow().isoformat(),
                "domain": domain
            }
            
            logger.info(f"Saved HTML document: {url}")
            return document
            
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return None
    
    def _crawl_and_save_file(self, crawler: AdvancedCrawler, url: str) -> Optional[Dict[str, Any]]:
        """Crawl and save a file (PDF, Excel, etc.)."""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        try:
            # Download file
            result = crawler.download_file(url)
            
            if not result.get('success'):
                logger.warning(f"Failed to download {url}: {result.get('error')}")
                return None
            
            # Extract filename
            filename = self._extract_filename(url)
            
            # Create document object
            document = {
                "id": f"doc_{len(self.documents) + 1}",
                "url": url,
                "title": filename,
                "content": result.get('content', ''),
                "content_type": result.get('content_type', 'unknown'),
                "content_length": result.get('content_length', 0),
                "crawl_time": result.get('crawl_time', 0),
                "status_code": result.get('status_code', 0),
                "headers": result.get('headers', {}),
                "extracted_at": datetime.utcnow().isoformat(),
                "filename": filename
            }
            
            logger.info(f"Saved file document: {url}")
            return document
            
        except Exception as e:
            logger.error(f"Error downloading file {url}: {e}")
            return None
    
    def _crawl_recursive(self, crawler: AdvancedCrawler, url: str, domain: str, max_doc_count: int):
        """Recursively crawl pages and extract documents."""
        if len(self.documents) >= max_doc_count:
            logger.info(f"Reached max document count ({max_doc_count}), stopping crawl")
            return
        
        if url in self.visited_urls:
            return
        
        logger.info(f"Crawling: {url} (documents found: {len(self.documents)}/{max_doc_count})")
        
        try:
            # Crawl current page
            page_doc = self._crawl_and_save_page(crawler, url, domain)
            if page_doc:
                self.documents.append(page_doc)
                logger.info(f"Added page document: {url}")
            
            # Check if we've reached the limit
            if len(self.documents) >= max_doc_count:
                return
            
            # Extract links from the page
            if page_doc and page_doc.get('content'):
                try:
                    soup = BeautifulSoup(page_doc['content'], 'html.parser')
                    link_extractor = LinkExtractor(domain)
                    
                    # Extract page links and document links
                    page_links, document_links = link_extractor.extract_links(soup, url, self.visited_urls)
                    
                    # First, try to download documents
                    for doc_url in document_links:
                        if len(self.documents) >= max_doc_count:
                            break
                        
                        doc = self._crawl_and_save_file(crawler, doc_url)
                        if doc:
                            self.documents.append(doc)
                            logger.info(f"Added document: {doc_url}")
                    
                    # Then, crawl sub-pages if we still have room
                    for page_url in page_links:
                        if len(self.documents) >= max_doc_count:
                            break
                        
                        # Recursively crawl sub-pages
                        self._crawl_recursive(crawler, page_url, domain, max_doc_count)
                        
                except Exception as e:
                    logger.error(f"Error in recursive crawl for {url}: {e}")
                    
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text(strip=True)
            
            # Fallback to h1
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text(strip=True)
            
            return "Untitled Document"
        except Exception:
            return "Untitled Document"
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        try:
            parsed = urlparse(url)
            path = parsed.path
            if path:
                filename = path.split('/')[-1]
                if filename:
                    return filename
            return "unknown_file"
        except Exception:
            return "unknown_file" 