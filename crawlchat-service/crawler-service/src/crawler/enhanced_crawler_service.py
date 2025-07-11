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

from .advanced_crawler import AdvancedCrawler
from .link_extractor import LinkExtractor
from .s3_document_storage import S3DocumentStorage

logger = logging.getLogger(__name__)

class EnhancedCrawlerService:
    """Enhanced crawler service with max document count support and S3 storage."""
    
    def __init__(self, api_key: str, user_id: str = "default"):
        self.api_key = api_key
        self.user_id = user_id
        self.documents = []
        self.visited_urls = set()
        self.s3_storage = S3DocumentStorage()
        
    def crawl_with_max_docs(self, base_url: str, max_doc_count: int = 1, task_id: str = None) -> Dict[str, Any]:
        """
        Crawl with max document count logic and S3 storage.
        
        Args:
            base_url: URL to crawl
            max_doc_count: Maximum number of documents to extract
            task_id: Task identifier for S3 storage
            
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
            
            # Always crawl the main page first
            logger.info(f"Crawling main page: {base_url}")
            main_page_doc = self._crawl_and_save_page(crawler, base_url, domain)
            if main_page_doc:
                self.documents.append(main_page_doc)
                logger.info(f"Added main page document: {base_url}")
            
            # Always do recursive crawling if we need more documents
            if len(self.documents) < max_doc_count:
                logger.info(f"Starting recursive crawl for additional documents (current: {len(self.documents)}, target: {max_doc_count})")
                # Extract links from the main page and crawl sub-pages
                if main_page_doc and main_page_doc.get('raw_html'):
                    try:
                        soup = BeautifulSoup(main_page_doc['raw_html'], 'html.parser')
                        link_extractor = LinkExtractor(domain)
                        
                        # Extract page links and document links
                        page_links, document_links = link_extractor.extract_links(soup, base_url, self.visited_urls)
                        
                        logger.info(f"Found {len(page_links)} page links and {len(document_links)} document links on main page")
                        
                        # First, try to download documents
                        for doc_url in document_links:
                            if len(self.documents) >= max_doc_count:
                                logger.info(f"Reached max document count, stopping document downloads")
                                break
                            
                            doc = self._crawl_and_save_file(crawler, doc_url)
                            if doc:
                                self.documents.append(doc)
                                logger.info(f"Added document: {doc_url} (total: {len(self.documents)}/{max_doc_count})")
                        
                        # Then, crawl sub-pages if we still have room (limit to first 10 to avoid infinite recursion)
                        sub_pages_to_crawl = page_links[:10]  # Limit to first 10 sub-pages
                        logger.info(f"Crawling {len(sub_pages_to_crawl)} sub-pages out of {len(page_links)} found")
                        
                        for page_url in sub_pages_to_crawl:
                            if len(self.documents) >= max_doc_count:
                                logger.info(f"Reached max document count, stopping page crawling")
                                break
                            
                            logger.info(f"Recursively crawling sub-page: {page_url} (depth: 1)")
                            # Recursively crawl sub-pages
                            self._crawl_recursive(crawler, page_url, domain, max_doc_count, 1)
                            
                    except Exception as e:
                        logger.error(f"Error in recursive crawl for main page: {e}")
                else:
                    logger.warning(f"No raw HTML found in main page, skipping link extraction")
            else:
                logger.info(f"Already have {len(self.documents)} documents, no need for recursive crawl")
            
            # Close crawler
            crawler.close()
            
            # Store documents in S3 if task_id is provided
            s3_results = None
            if task_id and self.documents:
                logger.info(f"Storing {len(self.documents)} documents in S3 for task {task_id}")
                s3_results = self.s3_storage.store_documents_batch(self.user_id, task_id, self.documents)
                logger.info(f"S3 storage results: {s3_results['stored_count']} stored, {s3_results['failed_count']} failed")
            
            # Prepare response
            response = {
                "success": True,
                "url": base_url,
                "documents_found": len(self.documents),
                "max_doc_count": max_doc_count,
                "documents": self.documents,
                "crawl_time": datetime.utcnow().isoformat(),
                "total_pages": len(self.visited_urls),
                "total_documents": len(self.documents),
                "s3_storage": s3_results
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
            # Crawl the page with optimized settings for speed
            # Try without JavaScript first for speed, fallback to JS if needed
            result = crawler.crawl_url(
                url, 
                content_type="generic",
                render_js=False,  # Disable JS for speed
                timeout=30,  # 30 second timeout
                block_resources=True,  # Block images/CSS for speed
                wait=1000  # Wait 1 second after page load
            )
            
            # If no content or very little content, try with JavaScript
            if not result.get('success') or len(result.get('content', '')) < 1000:
                logger.info(f"Retrying {url} with JavaScript rendering")
                result = crawler.crawl_url(
                    url, 
                    content_type="generic",
                    render_js=True,
                    timeout=30,
                    wait=2000  # Wait 2 seconds for JS to load
                )
            
            if not result.get('success'):
                logger.warning(f"Failed to crawl {url}: {result.get('error')}")
                return None
            
            # Extract title and clean content from HTML
            title = self._extract_title(result['content'])
            clean_content = self._extract_clean_content(result['content'])
            
            # Debug: Log content lengths
            raw_content_length = len(result.get('content', ''))
            clean_content_length = len(clean_content)
            logger.info(f"Content lengths for {url}: raw={raw_content_length}, clean={clean_content_length}")
            
            # Debug: Log first 200 characters of raw HTML
            raw_html_preview = result.get('content', '')[:200]
            logger.info(f"Raw HTML preview for {url}: {raw_html_preview}")
            
            # Create document object
            document = {
                "id": f"doc_{len(self.documents) + 1}",
                "url": url,
                "title": title,
                "content": clean_content,  # Use cleaned content
                "raw_html": result['content'],  # Keep original HTML too
                "content_type": "html",
                "content_length": len(clean_content),
                "raw_content_length": result.get('content_length', 0),
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
    
    def _crawl_recursive(self, crawler: AdvancedCrawler, url: str, domain: str, max_doc_count: int, depth: int = 0):
        """Recursively crawl pages and extract documents."""
        if len(self.documents) >= max_doc_count:
            logger.info(f"Reached max document count ({max_doc_count}), stopping crawl")
            return
        
        if url in self.visited_urls:
            return
        
        # Limit recursion depth to prevent infinite loops
        if depth > 2:  # Only go 2 levels deep
            logger.info(f"Reached max depth ({depth}), stopping recursion for {url}")
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
                logger.info(f"Reached max document count after adding page {url}")
                return
            
            # Extract links from the page
            if page_doc and page_doc.get('raw_html'):
                try:
                    soup = BeautifulSoup(page_doc['raw_html'], 'html.parser')
                    link_extractor = LinkExtractor(domain)
                    
                    # Extract page links and document links
                    page_links, document_links = link_extractor.extract_links(soup, url, self.visited_urls)
                    
                    logger.info(f"Found {len(page_links)} page links and {len(document_links)} document links on {url}")
                    
                    # First, try to download documents
                    for doc_url in document_links:
                        if len(self.documents) >= max_doc_count:
                            logger.info(f"Reached max document count, stopping document downloads")
                            break
                        
                        doc = self._crawl_and_save_file(crawler, doc_url)
                        if doc:
                            self.documents.append(doc)
                            logger.info(f"Added document: {doc_url} (total: {len(self.documents)}/{max_doc_count})")
                    
                    # Then, crawl sub-pages if we still have room
                    for page_url in page_links:
                        if len(self.documents) >= max_doc_count:
                            logger.info(f"Reached max document count, stopping page crawling")
                            break
                        
                        logger.info(f"Recursively crawling sub-page: {page_url} (depth: {depth + 1})")
                        # Recursively crawl sub-pages
                        self._crawl_recursive(crawler, page_url, domain, max_doc_count, depth + 1)
                        
                except Exception as e:
                    logger.error(f"Error in recursive crawl for {url}: {e}")
            else:
                logger.warning(f"No raw HTML found in page {url}, skipping link extraction")
                    
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
    
    def _extract_clean_content(self, html_content: str) -> str:
        """Extract clean text content from HTML with focus on financial content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Prioritize financial content areas
            financial_content = []
            
            # Look for financial-specific content areas
            financial_selectors = [
                'div[class*="financial"]', 'div[class*="earnings"]', 'div[class*="report"]',
                'div[class*="statement"]', 'div[class*="filing"]', 'div[class*="disclosure"]',
                'div[class*="announcement"]', 'div[class*="press"]', 'div[class*="news"]',
                'div[class*="data"]', 'div[class*="metrics"]', 'div[class*="results"]',
                'section[class*="financial"]', 'section[class*="earnings"]',
                'article[class*="financial"]', 'article[class*="earnings"]',
                'table[class*="financial"]', 'table[class*="data"]', 'table[class*="results"]',
                
                # News and economics content areas
                'div[class*="news"]', 'div[class*="article"]', 'div[class*="story"]',
                'div[class*="headline"]', 'div[class*="breaking"]', 'div[class*="latest"]',
                'div[class*="economics"]', 'div[class*="economic"]', 'div[class*="macro"]',
                'div[class*="policy"]', 'div[class*="central-bank"]', 'div[class*="fed"]',
                'div[class*="market"]', 'div[class*="trading"]', 'div[class*="analysis"]',
                'div[class*="commentary"]', 'div[class*="opinion"]', 'div[class*="editorial"]',
                'section[class*="news"]', 'section[class*="article"]', 'section[class*="economics"]',
                'article[class*="news"]', 'article[class*="article"]', 'article[class*="economics"]',
                'div[class*="content"]', 'div[class*="main-content"]', 'div[class*="body"]'
            ]
            
            for selector in financial_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:  # Only include substantial content
                        financial_content.append(text)
            
            # If no financial-specific content found, get all text
            if not financial_content:
                text = soup.get_text()
            else:
                # Combine financial content with general content
                general_text = soup.get_text()
                financial_content.append(general_text)
                text = ' '.join(financial_content)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting clean content: {e}")
            return html_content
    
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