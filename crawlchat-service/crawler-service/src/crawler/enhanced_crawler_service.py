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
import concurrent.futures
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the crawler path to sys.path
crawler_path = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, crawler_path)

from .advanced_crawler import AdvancedCrawler
from .link_extractor import LinkExtractor
from .s3_document_storage import S3DocumentStorage

logger = logging.getLogger(__name__)

class EnhancedCrawlerService:
    """Enhanced crawler service with max document count support and S3 storage."""
    
    def __init__(self, api_key: str, user_id: str = "default", task_id: str = None, max_threads: int = 3):
        self.api_key = api_key
        self.user_id = user_id
        self.task_id = task_id
        self.documents = []
        self.visited_urls = set()
        self.s3_storage = S3DocumentStorage()
        self.mongodb_helper = None
        self.max_threads = max_threads
        # Initialize MongoDB helper for progress updates
        try:
            from .mongodb_helper import MongoDBHelper
            self.mongodb_helper = MongoDBHelper()
        except ImportError:
            logger.warning("MongoDB helper not available for progress tracking")
    
    def crawl_with_max_docs(self, base_url: str, max_doc_count: int = 1, task_id: str = None, max_threads: int = None) -> Dict[str, Any]:
        logger.info(f"Starting enhanced crawl for {base_url} with max_doc_count: {max_doc_count}, max_threads: {max_threads or self.max_threads}")
        self.documents = []
        self.visited_urls = set()
        if task_id:
            self.task_id = task_id
        if max_threads is not None:
            self.max_threads = max_threads
        try:
            crawler = AdvancedCrawler(self.api_key)
            self._update_progress(0, max_doc_count, "Starting crawl...")
            domain = urlparse(base_url).netloc
            logger.info(f"Crawling main page: {base_url}")
            main_page_doc = self._crawl_and_save_page(crawler, base_url, domain)
            if main_page_doc:
                self.documents.append(main_page_doc)
                logger.info(f"Added main page document: {base_url}")
                self._update_progress(len(self.documents), max_doc_count, f"Found main page document")
            if len(self.documents) < max_doc_count:
                logger.info(f"Starting recursive crawl for additional documents (current: {len(self.documents)}, target: {max_doc_count})")
                if main_page_doc and main_page_doc.get('raw_html'):
                    try:
                        soup = BeautifulSoup(main_page_doc['raw_html'], 'html.parser')
                        link_extractor = LinkExtractor(domain)
                        page_links, document_links = link_extractor.extract_links(soup, base_url, self.visited_urls)
                        logger.info(f"Found {len(page_links)} page links and {len(document_links)} document links on main page")
                        # Multithreaded document downloads
                        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                            futures = []
                            for doc_url in document_links:
                                if len(self.documents) >= max_doc_count:
                                    break
                                futures.append(executor.submit(self._crawl_and_save_file, crawler, doc_url))
                            for future in concurrent.futures.as_completed(futures):
                                if len(self.documents) >= max_doc_count:
                                    break
                                doc = future.result()
                                if doc:
                                    self.documents.append(doc)
                                    logger.info(f"Added document: {doc['url']} (total: {len(self.documents)}/{max_doc_count})")
                                    self._update_progress(len(self.documents), max_doc_count, f"Found document: {doc['url']}")
                        # Multithreaded sub-page crawling (limit to first 10)
                        sub_pages_to_crawl = page_links[:10]
                        logger.info(f"Crawling {len(sub_pages_to_crawl)} sub-pages out of {len(page_links)} found")
                        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                            futures = []
                            for page_url in sub_pages_to_crawl:
                                if len(self.documents) >= max_doc_count:
                                    break
                                futures.append(executor.submit(self._crawl_recursive, crawler, page_url, domain, max_doc_count, 1))
                            for future in concurrent.futures.as_completed(futures):
                                if len(self.documents) >= max_doc_count:
                                    break
                                # No need to collect result, _crawl_recursive updates self.documents
                    except Exception as e:
                        logger.error(f"Error in recursive crawl for main page: {e}")
                else:
                    logger.warning(f"No raw HTML found in main page, skipping link extraction")
            else:
                logger.info(f"Already have {len(self.documents)} documents, no need for recursive crawl")
            crawler.close()
            s3_results = None
            if task_id and self.documents:
                logger.info(f"Storing {len(self.documents)} documents in S3 for task {task_id}")
                s3_results = self.s3_storage.store_documents_batch(self.user_id, task_id, self.documents)
                logger.info(f"S3 storage results: {s3_results['stored_count']} stored, {s3_results['failed_count']} failed")
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
    def _crawl_recursive(self, crawler: AdvancedCrawler, url: str, domain: str, max_doc_count: int, depth: int = 0):
        if len(self.documents) >= max_doc_count:
            logger.info(f"Reached max document count ({max_doc_count}), stopping crawl")
            return
        if url in self.visited_urls:
            return
        if depth > 2:
            logger.info(f"Reached max depth ({depth}), stopping recursion for {url}")
            return
        logger.info(f"Crawling: {url} (documents found: {len(self.documents)}/{max_doc_count})")
        try:
            page_doc = self._crawl_and_save_page(crawler, url, domain)
            if page_doc:
                self.documents.append(page_doc)
                logger.info(f"Added page document: {url}")
            if len(self.documents) >= max_doc_count:
                logger.info(f"Reached max document count after adding page {url}")
                return
            if page_doc and page_doc.get('raw_html'):
                try:
                    soup = BeautifulSoup(page_doc['raw_html'], 'html.parser')
                    link_extractor = LinkExtractor(domain)
                    page_links, document_links = link_extractor.extract_links(soup, url, self.visited_urls)
                    logger.info(f"Found {len(page_links)} page links and {len(document_links)} document links on {url}")
                    # Multithreaded document downloads
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                        futures = []
                        for doc_url in document_links:
                            if len(self.documents) >= max_doc_count:
                                break
                            futures.append(executor.submit(self._crawl_and_save_file, crawler, doc_url))
                        for future in concurrent.futures.as_completed(futures):
                            if len(self.documents) >= max_doc_count:
                                break
                            doc = future.result()
                            if doc:
                                self.documents.append(doc)
                                logger.info(f"Added document: {doc['url']} (total: {len(self.documents)}/{max_doc_count})")
                    # Multithreaded sub-page crawling
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                        futures = []
                        for page_url in page_links:
                            if len(self.documents) >= max_doc_count:
                                break
                            futures.append(executor.submit(self._crawl_recursive, crawler, page_url, domain, max_doc_count, depth + 1))
                        for future in concurrent.futures.as_completed(futures):
                            if len(self.documents) >= max_doc_count:
                                break
                except Exception as e:
                    logger.error(f"Error in recursive crawl for {url}: {e}")
            else:
                logger.warning(f"No raw HTML found in page {url}, skipping link extraction")
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
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
                timeout=30000,  # 30 second timeout in milliseconds
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
                    timeout=30000,  # 30 second timeout in milliseconds
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
                "id": self._generate_document_id(url),
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
            
            # Extract filename and determine file type
            filename = self._extract_filename(url)
            file_type = result.get('file_type', 'unknown')
            content_type = result.get('content_type', 'unknown')
            raw_content = result.get('content', b'')
            
            # Handle different file types appropriately
            if file_type == 'application/pdf' or url.lower().endswith('.pdf'):
                # For PDFs, convert binary content to base64 and extract text if possible
                import base64
                content_base64 = base64.b64encode(raw_content).decode('utf-8')
                
                # Try to extract text from PDF (simplified - in production you'd use PyPDF2 or similar)
                pdf_text = self._extract_pdf_text(raw_content)
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": pdf_text,  # Extracted text content
                    "content_base64": content_base64,  # Binary content as base64
                    "content_type": "application/pdf",
                    "file_type": "pdf",
                    "content_length": len(raw_content),
                    "text_length": len(pdf_text),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": True
                }
                
            elif file_type.startswith('image/'):
                # For images, convert to base64 and add description
                import base64
                content_base64 = base64.b64encode(raw_content).decode('utf-8')
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": f"Image file: {filename} ({file_type})",
                    "content_base64": content_base64,
                    "content_type": file_type,
                    "file_type": "image",
                    "content_length": len(raw_content),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": True
                }
                
            elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                # For Excel files, convert to base64 and add description
                import base64
                content_base64 = base64.b64encode(raw_content).decode('utf-8')
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": f"Excel file: {filename} - Contains spreadsheet data",
                    "content_base64": content_base64,
                    "content_type": file_type,
                    "file_type": "excel",
                    "content_length": len(raw_content),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": True
                }
                
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                # For Word documents, convert to base64 and add description
                import base64
                content_base64 = base64.b64encode(raw_content).decode('utf-8')
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": f"Word document: {filename} - Contains document content",
                    "content_base64": content_base64,
                    "content_type": file_type,
                    "file_type": "word",
                    "content_length": len(raw_content),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": True
                }
                
            elif file_type in ['text/plain', 'text/csv', 'application/json', 'application/xml']:
                # For text-based files, decode content
                try:
                    text_content = raw_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = raw_content.decode('latin-1')
                    except:
                        text_content = f"Binary content from {filename}"
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": text_content,
                    "content_type": file_type,
                    "file_type": "text",
                    "content_length": len(raw_content),
                    "text_length": len(text_content),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": False
                }
                
            else:
                # For other file types, convert to base64 and add generic description
                import base64
                content_base64 = base64.b64encode(raw_content).decode('utf-8')
                
                document = {
                    "id": self._generate_document_id(url),
                    "url": url,
                    "title": filename,
                    "content": f"File: {filename} ({file_type}) - Binary content available",
                    "content_base64": content_base64,
                    "content_type": file_type,
                    "file_type": "binary",
                    "content_length": len(raw_content),
                    "crawl_time": result.get('crawl_time', 0),
                    "status_code": result.get('status_code', 0),
                    "headers": result.get('headers', {}),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "filename": filename,
                    "is_binary": True
                }
            
            logger.info(f"Saved file document: {url} (type: {file_type}, size: {len(raw_content)} bytes)")
            return document
            
        except Exception as e:
            logger.error(f"Error downloading file {url}: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            # Try to extract text using PyPDF2 if available
            try:
                import PyPDF2
                import io
                
                pdf_file = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_content = []
                for page_num in range(len(pdf_reader.pages)):
                    try:
                        page = pdf_reader.pages[page_num]
                        text_content.append(page.extract_text())
                    except Exception as e:
                        logger.warning(f"Failed to extract text from PDF page {page_num}: {e}")
                        continue
                
                extracted_text = '\n'.join(text_content)
                if extracted_text.strip():
                    return extracted_text
                    
            except ImportError:
                logger.info("PyPDF2 not available, using fallback PDF text extraction")
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")
            
            # Fallback: Check if it's a valid PDF and return basic info
            if pdf_content.startswith(b'%PDF'):
                return f"PDF document (binary content available, {len(pdf_content)} bytes)"
            else:
                return f"Binary file (possibly corrupted PDF, {len(pdf_content)} bytes)"
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return f"PDF document (text extraction failed, {len(pdf_content)} bytes)"
    
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
    
    def _generate_document_id(self, url: str) -> str:
        """Generate a unique document ID based on URL hash."""
        try:
            import hashlib
            
            # Create a hash of the URL
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]  # Use first 16 characters
            
            # Add timestamp to ensure uniqueness
            # timestamp = str(int(datetime.utcnow().timestamp()))[-6:]  # Last 6 digits of timestamp
            
            return url_hash
            
        except Exception as e:
            logger.error(f"Error generating document ID for {url}: {e}")
            # Fallback to simple hash
            try:
                import hashlib
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
                return f"doc_{url_hash}"
            except:
                return f"doc_{len(self.documents) + 1}"
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL using hash."""
        try:
            import hashlib
            
            # Create a hash of the URL
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]  # Use first 12 characters
            
            # Try to get original filename from URL path
            parsed = urlparse(url)
            path = parsed.path
            original_filename = None
            
            if path:
                original_filename = path.split('/')[-1]
                # Check if it has a valid extension
                if original_filename and '.' in original_filename:
                    # Keep original filename with hash
                    name_without_ext = original_filename.rsplit('.', 1)[0]
                    ext = original_filename.rsplit('.', 1)[1]
                    return f"{name_without_ext}_{url_hash}.{ext}"
            
            # If no valid filename found, use hash with appropriate extension
            if url.lower().endswith('.pdf'):
                return f"document_{url_hash}.pdf"
            elif url.lower().endswith(('.doc', '.docx')):
                return f"document_{url_hash}.docx"
            elif url.lower().endswith(('.xls', '.xlsx')):
                return f"document_{url_hash}.xlsx"
            elif url.lower().endswith(('.ppt', '.pptx')):
                return f"document_{url_hash}.pptx"
            elif url.lower().endswith('.csv'):
                return f"document_{url_hash}.csv"
            elif url.lower().endswith('.json'):
                return f"document_{url_hash}.json"
            elif url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                ext = url.lower().split('.')[-1]
                return f"image_{url_hash}.{ext}"
            else:
                return f"document_{url_hash}.html"
                
        except Exception as e:
            logger.error(f"Error generating filename for {url}: {e}")
            # Fallback to simple hash
            try:
                import hashlib
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
                return f"document_{url_hash}.html"
            except:
                return "unknown_file"
    
    def _update_progress(self, current_count: int, max_count: int, message: str = ""):
        """Update progress in MongoDB for real-time tracking."""
        if not self.mongodb_helper or not self.task_id:
            return
        
        try:
            progress_data = {
                "documents_found": current_count,
                "documents_downloaded": current_count,
                "max_documents": max_count,
                "progress_percentage": min(100, int((current_count / max_count) * 100)) if max_count > 0 else 0,
                "status_message": message,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update task progress in MongoDB
            self.mongodb_helper.update_task_progress(self.task_id, progress_data)
            logger.info(f"Progress updated: {current_count}/{max_count} documents - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}") 

    async def download_files(self, file_urls: List[str], max_threads: int = 3) -> List[Dict[str, Any]]:
        """
        Download multiple files concurrently with rate limiting.
        
        Args:
            file_urls: List of file URLs to download
            max_threads: Maximum number of concurrent downloads
            
        Returns:
            List of download results
        """
        logger.info(f"Starting download of {len(file_urls)} files with {max_threads} threads")
        
        results = []
        
        # Process files in batches to avoid overwhelming the server
        batch_size = max(1, max_threads // 2)  # Use fewer concurrent downloads
        delay_between_batches = 3  # 3 second delay between batches
        
        for i in range(0, len(file_urls), batch_size):
            batch = file_urls[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} files")
            
            # Download batch concurrently
            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                batch_results = list(executor.map(self.crawler.download_file, batch))
                results.extend(batch_results)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(file_urls):
                logger.info(f"Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)
        
        # Log summary
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        logger.info(f"Download complete: {successful} successful, {failed} failed")
        
        return results 