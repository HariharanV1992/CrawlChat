"""
Advanced high-performance stock market crawler with optimizations.
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import hashlib
from pathlib import Path
from typing import Set, List, Tuple, Optional
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import re
import aiofiles
import tempfile
import os

# Import storage service for S3 uploads
try:
    from common.src.services.storage_service import StorageService
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    logging.warning("Storage service not available, files will be saved locally only")

logger = logging.getLogger(__name__)

@dataclass
class CrawlConfig:
    """Configuration for the advanced crawler."""
    max_pages: int = 50
    max_documents: int = 5
    max_workers: int = 10
    timeout: int = 10
    delay: float = 0.1
    use_proxy: bool = True
    proxy_api_key: str = ""
    proxy_method: str = "api_endpoint"  # "api_endpoint" or "proxy_port"
    min_file_size: int = 1024
    output_dir: str = "crawled_data"
    single_page_mode: bool = False  # New parameter for single page crawling
    
    # ScraperAPI specific settings
    country_code: str = "us"
    premium: bool = True
    bypass: str = "cloudflare"
    render: bool = False
    retry: int = 2
    session_number: int = 1
    
    # Performance settings
    connection_limit: int = 100
    tcp_connector_limit: int = 50
    keepalive_timeout: int = 30
    enable_compression: bool = True
    
    # Timeout settings
    total_timeout: int = 1800  # Total crawl timeout in seconds (30 minutes)
    page_timeout: int = 60     # Timeout per page in seconds
    request_timeout: int = 30  # Timeout per request in seconds
    
    # Early termination settings
    max_pages_without_documents: int = 20  # Stop if no documents found after this many pages
    
    # Content filtering
    relevant_keywords: List[str] = None
    exclude_patterns: List[str] = None
    document_extensions: List[str] = None
    
    def __post_init__(self):
        # Enable single page mode if max_documents is 1
        if self.max_documents == 1:
            self.single_page_mode = True
            self.max_pages = 1  # Force single page when single page mode is enabled
        
        if self.relevant_keywords is None:
            self.relevant_keywords = [
                'stock', 'market', 'financial', 'investor', 'earnings', 'revenue',
                'profit', 'dividend', 'share', 'equity', 'trading', 'quote',
                'annual', 'quarterly', 'report', 'statement', 'filing', 'sec',
                'board', 'governance', 'corporate', 'news', 'announcement'
            ]
        
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                'login', 'admin', 'private', 'internal', 'test', 'dev',
                'temp', 'cache', 'session', 'cookie', 'tracking', 'advertisement',
                'ad', 'banner', 'social', 'facebook', 'twitter', 'linkedin',
                'youtube', 'instagram', 'subscribe', 'newsletter', 'contact',
                'about', 'careers', 'jobs', 'support', 'help', 'faq'
            ]
        
        if self.document_extensions is None:
            self.document_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', '.txt', '.csv']

class AdvancedCrawler:
    """High-performance async crawler with optimizations."""
    
    def __init__(self, base_url: str, config: CrawlConfig, progress_callback=None, user_id: Optional[str] = None):
        """Initialize the advanced crawler."""
        self.base_url = base_url
        self.config = config
        self.progress_callback = progress_callback
        self.user_id = user_id  # Add user_id for user-specific storage
        
        # Parse domain for same-domain checking
        parsed_url = urlparse(base_url)
        self.domain = parsed_url.netloc
        
        # Initialize state
        self.session = None
        self.cancelled = False
        self.cancelled_by_user = False
        self.completed_normally = False  # New flag to track normal completion
        self.cancel_event = asyncio.Event()
        
        # Initialize storage service for S3 uploads with user_id
        self.storage_service = None
        if STORAGE_AVAILABLE:
            try:
                self.storage_service = StorageService()
                logger.info("Storage service initialized for S3 uploads")
            except Exception as e:
                logger.warning(f"Failed to initialize storage service: {e}")
                self.storage_service = None
        
        # Statistics
        self.pages_crawled = 0
        self.documents_downloaded = 0
        self.pages_without_documents = 0
        self.visited_urls = set()
        self.url_queue = asyncio.Queue()
        
        # Performance tracking
        self.start_time = None
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'bytes_downloaded': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        # Create output directory (for temporary storage before S3 upload)
        self.output_dir = Path(config.output_dir) / self.domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.pages_crawled = 0
        self.documents_downloaded = 0
        self.pages_without_documents = 0  # Track consecutive pages without documents
        self.visited_urls: Set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(config.max_workers)
    
    def cancel(self):
        """Cancel the crawling operation."""
        self.cancelled = True
        self.cancelled_by_user = True  # Mark as cancelled by user
        self.cancel_event.set()
        logger.info("Crawl cancellation requested")
    
    def is_cancelled(self) -> bool:
        """Check if crawling has been cancelled."""
        return self.cancelled
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _create_session(self):
        """Create optimized aiohttp session."""
        connector = aiohttp.TCPConnector(
            limit=self.config.connection_limit,
            limit_per_host=self.config.tcp_connector_limit,
            keepalive_timeout=self.config.keepalive_timeout,
            enable_cleanup_closed=True,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=self.config.request_timeout // 2,
            sock_read=self.config.request_timeout * 2  # Give more time for reading
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
    
    async def _close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is from same domain."""
        return urlparse(url).netloc == self.domain
    
    def _is_document_url(self, url: str) -> bool:
        """Check if URL points to a document file."""
        url_lower = url.lower()
        
        # Common document extensions
        document_extensions = [
            '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', 
            '.csv', '.json', '.xml', '.txt', '.rtf', '.odt', '.ods',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
            '.epub', '.mobi', '.azw', '.azw3', '.azw4'
        ]
        
        # Check for document extensions
        for ext in document_extensions:
            if ext in url_lower:
                return True
        
        # Check for document patterns in URL
        document_patterns = [
            '/pdf/', '/documents/', '/files/', '/downloads/',
            '/reports/', '/annual/', '/quarterly/', '/financial/',
            '/filings/', '/sec/', '/edgar/', '/investor/',
            '/shareholder/', '/proxy/', '/10-k/', '/10-q/',
            '/8-k/', '/form-', '/filing/', '/disclosure/',
            '/press-release/', '/news-release/', '/media/',
            '/assets/', '/resources/', '/publications/',
            '/white-paper/', '/whitepaper/', '/case-study/',
            '/data-sheet/', '/datasheet/', '/brochure/',
            '/catalog/', '/manual/', '/guide/', '/handbook/',
            '/policy/', '/procedure/', '/standard/', '/specification/'
        ]
        
        for pattern in document_patterns:
            if pattern in url_lower:
                return True
        
        # Check for document-related query parameters
        doc_params = ['download', 'file', 'document', 'report', 'pdf', 'doc']
        for param in doc_params:
            if f'?{param}=' in url_lower or f'&{param}=' in url_lower:
                return True
        
        return False
    
    def _is_html_document(self, url: str) -> bool:
        """Check if URL is an HTML document (article, news, content page)."""
        url_lower = url.lower()
        
        # Skip common non-content pages
        skip_patterns = [
            '/static/', '/assets/', '/css/', '/js/', '/images/', '/img/',
            '/api/', '/ajax/', '/search', '/login', '/register', '/admin',
            '/sitemap', '/robots.txt', '/favicon', '/ads', '/analytics',
            '/tracking', '/pixel', '/beacon', '/monitoring', '/cdn/',
            '/cache/', '/temp/', '/tmp/', '/test/', '/dev/', '/staging/',
            'mailto:', 'tel:', 'javascript:', 'data:', 'file:'
        ]
        
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Consider most pages as HTML documents unless they're clearly not
        # This is more permissive than the previous version
        
        # Must have a meaningful path (not just domain)
        path = urlparse(url).path
        if len(path) < 3:  # Too short to be meaningful content
            return False
        
        # Skip if it's clearly a document file
        if any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', '.txt', '.csv', '.zip', '.rar']):
            return False
        
        # Consider it an HTML document if it passes the above checks
        return True
    
    def _is_relevant_url(self, url: str, link_text: str = "") -> bool:
        """Check if URL is relevant for crawling."""
        url_lower = url.lower()
        link_text_lower = link_text.lower()
        
        # Skip common non-content patterns
        skip_patterns = [
            '/static/', '/assets/', '/css/', '/js/', '/images/', '/img/',
            '/api/', '/ajax/', '/search', '/login', '/register', '/admin',
            '/sitemap', '/robots.txt', '/favicon', '/ads', '/analytics',
            '/tracking', '/pixel', '/beacon', '/monitoring', '/cdn/',
            '/cache/', '/temp/', '/tmp/', '/test/', '/dev/', '/staging/',
            'mailto:', 'tel:', 'javascript:', 'data:', 'file:'
        ]
        
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Check for relevant keywords in URL
        url_keywords = [
            'investor', 'financial', 'report', 'news', 'announcement', 
            'filing', 'document', 'pdf', 'annual', 'quarterly', 'earnings',
            'dividend', 'shareholder', 'board', 'management', 'corporate',
            'governance', 'esg', 'sustainability', 'environmental', 'social',
            'about', 'company', 'business', 'press', 'media', 'contact',
            'careers', 'jobs', 'team', 'leadership', 'board', 'directors'
        ]
        
        for keyword in url_keywords:
            if keyword in url_lower:
                return True
        
        # Check for relevant keywords in link text
        text_keywords = [
            'investor', 'financial', 'report', 'news', 'announcement',
            'about', 'company', 'business', 'press', 'media', 'contact',
            'careers', 'team', 'leadership', 'board', 'directors'
        ]
        
        for keyword in text_keywords:
            if keyword in link_text_lower:
                return True
        
        # Check for content-like URL patterns
        content_patterns = [
            '/about/', '/company/', '/business/', '/investor/', '/news/',
            '/press/', '/media/', '/contact/', '/careers/', '/team/',
            '/leadership/', '/board/', '/directors/', '/governance/',
            '/sustainability/', '/esg/', '/environmental/', '/social/'
        ]
        
        for pattern in content_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """Extract links from HTML content."""
        page_links = []
        document_links = []
        
        try:
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                
                # Skip if not same domain
                if not self._is_same_domain(full_url):
                    continue
                
                # Skip if already visited
                if full_url in self.visited_urls:
                    continue
                
                # Get link text for better relevance detection
                link_text = link.get_text(strip=True).lower()
                
                # Check if it's a document
                if self._is_document_url(full_url):
                    document_links.append(full_url)
                    continue
                
                # Check if it's a relevant page
                if self._is_relevant_url(full_url, link_text):
                    page_links.append(full_url)
                    
            # Also check for links in script tags (for SPA sites)
            for script in soup.find_all('script'):
                if script.string:
                    # Look for URLs in JavaScript
                    import re
                    urls = re.findall(r'["\']([^"\']*\.(?:html|htm|php|asp|aspx|jsp))["\']', script.string)
                    for url in urls:
                        full_url = urljoin(base_url, url)
                        if (self._is_same_domain(full_url) and 
                            full_url not in self.visited_urls and
                            self._is_relevant_url(full_url)):
                            page_links.append(full_url)
                            
            # Remove duplicates while preserving order
            page_links = list(dict.fromkeys(page_links))
            document_links = list(dict.fromkeys(document_links))
            
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            
        return page_links, document_links
    
    async def _make_request(self, url: str, binary_mode: bool = False) -> Optional[aiohttp.ClientResponse]:
        """Make HTTP request with proxy support and fallback."""
        # Check for cancellation before making request
        if self.cancelled:
            logger.info(f"Request cancelled for {url}")
            return None
            
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # Ensure session exists
            if not self.session:
                await self._create_session()
                
            if self.config.use_proxy and self.config.proxy_api_key:
                # Validate proxy API key
                if not self.config.proxy_api_key.strip():
                    logger.warning("Proxy API key is empty, falling back to direct requests")
                    self.config.use_proxy = False
                else:
                    # Try proxy first with optimized parameters
                    try:
                        if self.config.proxy_method == "proxy_port":
                            # Use proxy port method with increased timeout
                            proxy_url = f"http://scraperapi:{self.config.proxy_api_key}@proxy-server.scraperapi.com:8001"
                            target_url = url
                            logger.debug(f"Making proxy port request to: {url}")
                            
                            # Use longer timeout for proxy requests
                            proxy_timeout = aiohttp.ClientTimeout(
                                total=min(120, self.config.request_timeout * 3),  # 3x longer for proxy
                                connect=30,
                                sock_read=60
                            )
                            
                            async with self.semaphore:
                                response = await self.session.get(
                                    target_url,
                                    headers=headers,
                                    proxy=proxy_url,
                                    ssl=False,
                                    timeout=proxy_timeout
                                )
                        else:
                            # Use API endpoint method with optimized parameters
                            proxy_params = {
                                'api_key': self.config.proxy_api_key,
                                'url': url,
                                'render': str(self.config.render).lower(),  # Use config value
                                'country_code': self.config.country_code,  # Use config value
                                'premium': str(self.config.premium).lower(),  # Use config value
                                'bypass': self.config.bypass,  # Use config value
                                'keep_headers': 'true',
                                'retry': str(self.config.retry),  # Use config value
                                'session_number': str(self.config.session_number)  # Use config value
                            }
                            
                            # For binary files, add binary_target parameter
                            if binary_mode:
                                proxy_params['binary_target'] = 'true'
                            
                            proxy_url = "http://api.scraperapi.com"
                            logger.debug(f"Making proxy API request to: {url}")
                            
                            # Use longer timeout for proxy requests
                            proxy_timeout = aiohttp.ClientTimeout(
                                total=min(120, self.config.request_timeout * 3),  # 3x longer for proxy
                                connect=30,
                                sock_read=60
                            )
                            
                            async with self.semaphore:
                                response = await self.session.get(
                                    proxy_url, 
                                    params=proxy_params,
                                    headers=headers,
                                    ssl=False, 
                                    timeout=proxy_timeout
                                )
                        
                        if response.status == 200:
                            return response
                        else:
                            try:
                                error_content = await response.text()
                                # Only log critical errors
                                if response.status in [401, 403, 429, 500, 502, 503, 504]:
                                    logger.warning(f"Proxy error {response.status} for {url}")
                            except:
                                pass
                    except asyncio.TimeoutError:
                        logger.warning(f"Proxy timeout for {url}")
                    except Exception as e:
                        error_msg = str(e)
                        # Only log critical errors
                        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                            logger.warning(f"Proxy error for {url}: {error_msg}")
                    logger.info(f"Falling back to direct request for {url}")
            else:
                if self.config.use_proxy and not self.config.proxy_api_key:
                    logger.debug(f"Proxy disabled - no API key configured for {url}")
                elif not self.config.use_proxy:
                    logger.debug(f"Proxy disabled - making direct request for {url}")

            # Direct request with standard timeout
            async with self.semaphore:
                response = await self.session.get(
                    url,
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                )
            logger.debug(f"Direct response status: {response.status}")
            
            if response.status == 200:
                # For binary mode, don't try to read as text
                if not binary_mode:
                    try:
                        text = await response.text()
                        logger.debug(f"Direct response preview: {text[:200]}...")
                    except UnicodeDecodeError:
                        logger.warning(f"Direct response contains binary data for {url}, skipping text preview")
                return response
            else:
                logger.warning(f"Direct request returned status {response.status} for {url}")
                return None
        except Exception as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None
    
    async def _crawl_page(self, url: str) -> bool:
        """Crawl a single page and extract links."""
        try:
            # Check for cancellation
            if self.cancelled:
                return False
                
            logger.debug(f"Crawling page: {url}")
            
            # Make request
            response = await self._make_request(url)
            if not response:
                logger.warning(f"Failed to get response for {url}")
                return False
                
            # Read content
            try:
                content = await response.text()
            except Exception as e:
                logger.warning(f"Failed to read content from {url}: {e}")
                return False
            finally:
                response.close()
                
            # Parse HTML
            try:
                soup = BeautifulSoup(content, 'html.parser')
            except Exception as e:
                logger.warning(f"Failed to parse HTML from {url}: {e}")
                return False
                
            # Extract links
            page_links, document_links = self._extract_links(soup, url)
            
            # Add new page links to queue
            new_pages_added = 0
            for link in page_links:
                if link not in self.visited_urls:
                    try:
                        # Check if already in queue
                        if link not in [item for item in self.url_queue._queue]:
                            self.url_queue.put_nowait(link)
                            new_pages_added += 1
                            logger.debug(f"Added to queue: {link}")
                    except asyncio.QueueFull:
                        logger.debug(f"Queue full, skipping {link}")
                        break
                        
            logger.debug(f"Added {new_pages_added} new pages to queue from {url}")
            
            # Download the current page as HTML document if we haven't reached the limit
            documents_found = 0
            if self.documents_downloaded < self.config.max_documents:
                try:
                    # Save the current page as HTML document temporarily
                    url_hash = self._get_url_hash(url)
                    filename = f"document_{url_hash}_{int(time.time())}.html"
                    file_path = self.output_dir / filename
                    
                    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                        await f.write(content)
                    
                    # Upload to S3 if storage service is available
                    s3_key = None
                    if self.storage_service:
                        try:
                            # Generate S3 key with domain prefix
                            s3_key = f"crawled_documents/{self.domain}/{filename}"
                            s3_result = await self.storage_service.upload_file(str(file_path), s3_key)
                            
                            if s3_result:
                                logger.info(f"✅ Uploaded to S3: {s3_key}")
                                
                                # Before saving document to database
                                logger.info(f"[DEBUG] About to save document to database: {filename}, s3_key={s3_key}, content_length={len(content)}")
                                await self._save_document_to_database(filename, s3_key, len(content))
                                logger.info(f"[DEBUG] Finished saving document to database: {filename}")
                                
                                # Optionally delete local file after successful upload
                                try:
                                    os.remove(file_path)
                                    logger.debug(f"Deleted local file after S3 upload: {filename}")
                                except Exception as e:
                                    logger.warning(f"Failed to delete local file {filename}: {e}")
                            else:
                                logger.warning(f"Failed to upload to S3: {filename}")
                                
                        except Exception as e:
                            logger.error(f"Error uploading to S3: {e}")
                    
                    self.documents_downloaded += 1
                    documents_found += 1
                    self.stats['bytes_downloaded'] += len(content.encode('utf-8'))
                    
                    if s3_key:
                        logger.info(f"✅ Downloaded and uploaded to S3: {s3_key} ({len(content):,} bytes)")
                    else:
                        logger.info(f"Downloaded HTML document: {filename} ({len(content):,} bytes)")
                        
                except Exception as e:
                    logger.error(f"Error saving HTML document for {url}: {e}")
            
            # Download additional documents found on this page
            for doc_url in document_links:
                if self.documents_downloaded >= self.config.max_documents:
                    break
                    
                if await self._download_document(doc_url):
                    documents_found += 1
                    
            # Update counters
            self.pages_crawled += 1
            if documents_found == 0:
                self.pages_without_documents += 1
                
            # Log the total documents downloaded for this page (including the HTML page itself)
            total_docs_for_page = documents_found
            logger.info(f"Crawled {url} - Found {len(page_links)} pages, {total_docs_for_page} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return False
    
    async def _download_document(self, url: str) -> bool:
        """Download a document."""
        try:
            # Check for cancellation before starting download
            if self.cancelled:
                logger.info(f"Document download cancelled for {url}")
                return False
                
            # Check if this is actually a document we want to download
            if not self._is_document_url(url):
                logger.debug(f"Skipping non-document URL: {url}")
                return False
            
            # Make request in binary mode
            response = await self._make_request(url, binary_mode=True)
            if not response or response.status != 200:
                logger.warning(f"Failed to get response for document {url}")
                return False
            
            # Read binary content
            try:
                content = await response.read()
            except Exception as e:
                logger.error(f"Failed to read binary content from {url}: {e}")
                return False
            finally:
                response.close()
            
            if len(content) < self.config.min_file_size:
                logger.debug(f"Document {url} too small ({len(content)} bytes), skipping")
                return False
            
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = parsed_url.path.split('/')[-1]
            if not filename or '.' not in filename:
                # Generate filename based on content type or URL
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type:
                    filename = f"document_{int(time.time())}.pdf"
                elif 'word' in content_type or 'document' in content_type:
                    filename = f"document_{int(time.time())}.docx"
                elif 'excel' in content_type or 'spreadsheet' in content_type:
                    filename = f"document_{int(time.time())}.xlsx"
                else:
                    filename = f"document_{int(time.time())}.bin"
            
            # Double-check the filename doesn't have unwanted extensions
            if any(ext in filename.lower() for ext in ['.bin', '.dat', '.tmp', '.cache', '.log']):
                logger.debug(f"Skipping unwanted file type: {filename}")
                return False
            
            # Ensure filename is safe
            filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            if not filename:
                filename = f"document_{int(time.time())}.bin"
            
            # Save file temporarily (for S3 upload)
            file_path = self.output_dir / filename
            
            # Write binary content
            try:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
            except Exception as e:
                logger.error(f"Failed to write document {filename}: {e}")
                return False
            
            # Upload to S3 if storage service is available
            s3_key = None
            if self.storage_service:
                try:
                    # Generate S3 key with domain prefix
                    s3_key = f"crawled_documents/{self.domain}/{filename}"
                    s3_result = await self.storage_service.upload_file(str(file_path), s3_key)
                    
                    if s3_result:
                        logger.info(f"✅ Uploaded to S3: {s3_key}")
                        
                        # Before saving document to database
                        logger.info(f"[DEBUG] About to save document to database: {filename}, s3_key={s3_key}, content_length={len(content)}")
                        await self._save_document_to_database(filename, s3_key, len(content))
                        logger.info(f"[DEBUG] Finished saving document to database: {filename}")
                        
                        # Optionally delete local file after successful upload
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted local file after S3 upload: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to delete local file {filename}: {e}")
                    else:
                        logger.warning(f"Failed to upload to S3: {filename}")
                        
                except Exception as e:
                    logger.error(f"Error uploading to S3: {e}")
            
            self.documents_downloaded += 1
            self.stats['bytes_downloaded'] += len(content)
            
            if s3_key:
                logger.info(f"✅ Downloaded and uploaded to S3: {s3_key} ({len(content):,} bytes)")
            else:
                logger.info(f"✅ Downloaded document: {filename} ({len(content):,} bytes)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    async def crawl(self):
        """Main crawling method."""
        self.start_time = time.time()
        
        try:
            # Ensure session is created
            if not self.session:
                await self._create_session()
            
            if self.config.single_page_mode:
                logger.info(f"Starting single page crawl for {self.base_url}")
                await self._crawl_single_page()
            else:
                logger.info(f"Starting advanced crawl for {self.base_url}")
                await self._crawl_multiple_pages()
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            raise
        finally:
            # Always close session
            await self._close_session()
        
        # Print statistics
        elapsed_time = time.time() - self.start_time
        logger.info(f"Crawling completed in {elapsed_time:.2f}s")
        logger.info(f"Pages crawled: {self.pages_crawled}/{self.config.max_pages}")
        logger.info(f"Documents downloaded: {self.documents_downloaded}/{self.config.max_documents}")
        logger.info(f"Requests made: {self.stats['requests_made']}")
        logger.info(f"Requests failed: {self.stats['requests_failed']}")
        logger.info(f"Bytes downloaded: {self.stats['bytes_downloaded']}")
        logger.info(f"Avg response time: {self.stats['avg_response_time']:.2f}s")
        
        if self.cancelled:
            if self.cancelled_by_user:
                logger.info("🛑 Crawl was cancelled by user")
            else:
                logger.info("✅ Crawl completed - limits reached")
        else:
            logger.info("✅ Crawl completed successfully")
        
        logger.info(f"📄 Crawled pages: {self.pages_crawled}/{self.config.max_pages}")
        if self.pages_without_documents > 0:
            logger.info(f"📊 Pages without documents: {self.pages_without_documents}")
    
    async def _crawl_single_page(self):
        """Crawl only the specified URL without following any links."""
        try:
            # Check for cancellation before starting
            if self.cancelled:
                logger.info("Single page crawl cancelled before starting")
                return
            
            # Check if this is a document URL (PDF, DOC, etc.) first
            if self._is_document_url(self.base_url):
                # Download as document using binary mode
                if await self._download_document(self.base_url):
                    self.documents_downloaded += 1
                    self.pages_crawled += 1
                    logger.info(f"✅ Downloaded document from {self.base_url}")
                    
                    # Update progress
                    await self._update_progress()
                else:
                    logger.error(f"Failed to download document from {self.base_url}")
            else:
                # Check for cancellation before making request
                if self.cancelled:
                    logger.info("Single page crawl cancelled before making request")
                    return
                
                # Make request to the URL for HTML content
                response = await self._make_request(self.base_url)
                if not response or response.status != 200:
                    logger.error(f"Failed to fetch {self.base_url}: {response.status if response else 'No response'}")
                    return
                
                # Check for cancellation before processing content
                if self.cancelled:
                    logger.info("Single page crawl cancelled before processing content")
                    return
                
                # Get content
                content = await response.text()
                content_length = len(content.encode('utf-8'))
                self.stats['bytes_downloaded'] += content_length
                
                # Check for cancellation before saving file
                if self.cancelled:
                    logger.info("Single page crawl cancelled before saving file")
                    return
                
                # Save as HTML document temporarily
                url_hash = self._get_url_hash(self.base_url)
                filename = f"document_{url_hash}_{int(time.time())}.html"
                file_path = self.output_dir / filename
                
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                
                # Check for cancellation before S3 upload
                if self.cancelled:
                    logger.info("Single page crawl cancelled before S3 upload")
                    return
                
                # Upload to S3 if storage service is available
                s3_key = None
                if self.storage_service:
                    try:
                        # Generate S3 key with domain prefix
                        s3_key = f"crawled_documents/{self.domain}/{filename}"
                        s3_result = await self.storage_service.upload_file(str(file_path), s3_key)
                        
                        if s3_result:
                            logger.info(f"✅ Uploaded to S3: {s3_key}")
                            
                            # Before saving document to database
                            logger.info(f"[DEBUG] About to save document to database: {filename}, s3_key={s3_key}, content_length={len(content)}")
                            await self._save_document_to_database(filename, s3_key, len(content))
                            logger.info(f"[DEBUG] Finished saving document to database: {filename}")
                            
                            # Optionally delete local file after successful upload
                            try:
                                os.remove(file_path)
                                logger.debug(f"Deleted local file after S3 upload: {filename}")
                            except Exception as e:
                                logger.warning(f"Failed to delete local file {filename}: {e}")
                        else:
                            logger.warning(f"Failed to upload to S3: {filename}")
                            
                    except Exception as e:
                        logger.error(f"Error uploading to S3: {e}")
                
                self.documents_downloaded += 1
                self.pages_crawled += 1
                
                if s3_key:
                    logger.info(f"✅ Downloaded and uploaded to S3: {s3_key}")
                    logger.info(f"📄 Content length: {content_length:,} bytes")
                else:
                    logger.info(f"✅ Downloaded HTML document: {filename}")
                    logger.info(f"📄 Content length: {content_length:,} bytes")
                
                # Update progress
                await self._update_progress()
            
        except Exception as e:
            logger.error(f"Error in single page crawl: {e}")
    
    async def _crawl_multiple_pages(self):
        """Original multi-page crawling logic."""
        # Add initial URL to queue
        await self.url_queue.put(self.base_url)
        
        # Create tasks for workers
        workers = [asyncio.create_task(self._worker()) for _ in range(self.config.max_workers)]
        
        # Create status monitoring task
        status_task = asyncio.create_task(self._status_monitor())
        
        # Create timeout monitor task
        timeout_task = asyncio.create_task(self._timeout_monitor())
        
        # Wait for all workers to complete or limits to be reached
        try:
            await asyncio.gather(*workers, status_task, timeout_task, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
        finally:
            # Cancel any remaining tasks if cancelled
            if self.cancelled:
                logger.info("Cancelling all remaining tasks...")
                for worker in workers:
                    if not worker.done():
                        worker.cancel()
                if not status_task.done():
                    status_task.cancel()
                if not timeout_task.done():
                    timeout_task.cancel()
                
                # Wait for tasks to actually cancel
                await asyncio.gather(*workers, status_task, timeout_task, return_exceptions=True)
    
    async def _worker(self):
        """Worker coroutine for processing URLs."""
        while True:
            try:
                # Check for cancellation at the start of each loop
                if self.cancelled:
                    logger.info("Worker cancelled, stopping")
                    break
                
                # Check limits before getting URL from queue
                if (self.pages_crawled >= self.config.max_pages or 
                    self.documents_downloaded >= self.config.max_documents or
                    self.pages_without_documents >= self.config.max_pages_without_documents):
                    logger.info(f"Worker stopping - limits reached: pages={self.pages_crawled}/{self.config.max_pages}, docs={self.documents_downloaded}/{self.config.max_documents}")
                    self.completed_normally = True  # Mark as completed normally
                    break
                
                # Get URL from queue with shorter timeout to check cancellation more frequently
                try:
                    url = await asyncio.wait_for(self.url_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Check cancellation and limits again after timeout
                    if self.cancelled:
                        logger.info("Worker cancelled during timeout, stopping")
                        break
                    if (self.pages_crawled >= self.config.max_pages or 
                        self.documents_downloaded >= self.config.max_documents or
                        self.pages_without_documents >= self.config.max_pages_without_documents):
                        logger.info(f"Worker stopping during timeout - limits reached")
                        self.completed_normally = True  # Mark as completed normally
                        break
                    continue
                
                # Skip if already visited
                if url in self.visited_urls:
                    self.url_queue.task_done()
                    continue
                
                # Check limits again before processing
                if (self.pages_crawled >= self.config.max_pages or 
                    self.documents_downloaded >= self.config.max_documents or
                    self.pages_without_documents >= self.config.max_pages_without_documents or
                    self.cancelled):
                    self.url_queue.task_done()
                    logger.info(f"Worker stopping before processing - limits reached")
                    self.completed_normally = True  # Mark as completed normally
                    break
                
                self.visited_urls.add(url)
                
                # Check cancellation before processing URL
                if self.cancelled:
                    logger.info("Worker cancelled before processing URL, stopping")
                    break
                
                # Crawl page (this will now download the HTML content)
                if await self._crawl_page(url):
                    # Update progress
                    await self._update_progress()
                
                # Mark task as done
                self.url_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker: {e}")
                if 'url' in locals():
                    self.url_queue.task_done()
                if self.cancelled:
                    break
    
    async def _status_monitor(self):
        """Monitor and log crawling progress."""
        while not self.cancelled:
            try:
                elapsed = time.time() - self.start_time
                logger.info(f"Progress: {self.pages_crawled}/{self.config.max_pages} pages, "
                          f"{self.documents_downloaded}/{self.config.max_documents} documents, "
                          f"{self.pages_without_documents} pages without docs "
                          f"({elapsed:.1f}s elapsed)")
                
                # Check if we should stop
                if (self.documents_downloaded >= self.config.max_documents or
                    self.pages_crawled >= self.config.max_pages or
                    self.pages_without_documents >= self.config.max_pages_without_documents or
                    self.cancelled):
                    logger.info("Status monitor stopping - limits reached or cancelled")
                    # Signal workers to stop by setting cancelled flag (but not cancelled_by_user)
                    if not self.cancelled:
                        self.cancelled = True  # Set cancelled but not cancelled_by_user
                        self.completed_normally = True  # Mark as completed normally
                        self.cancel_event.set()
                    break
                
                # Check for cancellation more frequently (every 2 seconds instead of 10)
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in status monitor: {e}")
                if self.cancelled:
                    break
                await asyncio.sleep(2)
    
    async def _timeout_monitor(self):
        """Monitor total crawl time and cancel if timeout is reached."""
        start_time = time.time()
        while not self.cancelled:
            elapsed_time = time.time() - start_time
            if elapsed_time >= self.config.total_timeout:
                logger.warning(f"Crawl timed out after {self.config.total_timeout} seconds")
                self.cancel()
                break
            await asyncio.sleep(1)  # Check every second
    
    async def _update_progress(self):
        """Update progress and call callback if provided."""
        if self.progress_callback:
            try:
                await self.progress_callback({
                    'documents_downloaded': self.documents_downloaded,
                    'pages_crawled': self.pages_crawled,
                    'pages_without_documents': self.pages_without_documents
                })
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    async def _save_document_to_database(self, filename: str, s3_key: str, content_length: int):
        """Save document record to database for API access."""
        try:
            # Import necessary modules for new structure
            import uuid
            from datetime import datetime
            from pathlib import Path
            
            # Import the new document service
            try:
                from common.src.services.document_service import DocumentService
                from common.src.models.documents import Document, DocumentType, DocumentStatus
                from common.src.core.database import mongodb
                
                # Initialize document service
                document_service = DocumentService()
                
                # Determine document type from filename
                extension = Path(filename).suffix.lower()
                document_type_map = {
                    '.pdf': DocumentType.PDF,
                    '.doc': DocumentType.DOC,
                    '.docx': DocumentType.DOCX,
                    '.txt': DocumentType.TXT,
                    '.html': DocumentType.HTML,
                    '.htm': DocumentType.HTML,
                    # Map other extensions to TXT as fallback
                    '.xlsx': DocumentType.TXT,
                    '.xls': DocumentType.TXT,
                    '.ppt': DocumentType.TXT,
                    '.pptx': DocumentType.TXT,
                    '.csv': DocumentType.TXT,
                    '.json': DocumentType.TXT
                }
                document_type = document_type_map.get(extension, DocumentType.TXT)
                
                # Create document record using new model
                document = Document(
                    document_id=str(uuid.uuid4()),
                    user_id=self.user_id,  # Use the user_id passed to constructor
                    filename=filename,
                    file_path=s3_key,  # Use S3 key as file path
                    file_size=content_length,
                    document_type=document_type,
                    status=DocumentStatus.UPLOADED,
                    uploaded_at=datetime.utcnow(),
                    task_id=getattr(self, 'task_id', None),  # Will be set by crawler service
                    metadata={
                        'crawled_at': datetime.utcnow().isoformat(),
                        'domain': self.domain,
                        'uploaded_to_s3': True,
                        's3_key': s3_key
                    }
                )
                
                # Save document to MongoDB using the document service
                await document_service.create_document(document)
                
                logger.info(f"Saved document record to database: {filename}")
                
                # Note: Embeddings will be created on-demand when user queries the documents
                # This makes the crawler much faster and more efficient
                
            except ImportError as e:
                logger.warning(f"New document service not available: {e}")
                # Fallback: just log the document info
                logger.info(f"Document downloaded but not saved to database: {filename} ({content_length} bytes)")
                
        except Exception as e:
            logger.error(f"Error saving document record to database: {e}")
            # Don't raise the exception to avoid breaking the crawl process