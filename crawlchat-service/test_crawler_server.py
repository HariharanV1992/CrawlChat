#!/usr/bin/env python3
"""
Simple test server for crawler functionality
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

# Add the crawler path to sys.path
crawler_path = os.path.join(os.path.dirname(__file__), 'crawler-service', 'src')
sys.path.insert(0, crawler_path)
from crawler.advanced_crawler import AdvancedCrawler
from crawler.link_extractor import LinkExtractor

# Mock storage for tasks
mock_tasks = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Crawler Test Server",
    description="Simple test server for crawler functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="ui/templates")

# Setup static files
try:
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")
    # Create fallback static handler
    @app.get("/static/{path:path}")
    async def static_files(path: str):
        """Fallback static file handler."""
        return {"error": "Static files not available", "path": path}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Crawler Test Server",
        "endpoints": {
            "health": "/health",
            "crawler_health": "/api/v1/crawler/health",
            "crawler_config": "/api/v1/crawler/config",
            "crawl": "/api/v1/crawler/crawl?url=<url>",
            "web_ui": "/crawler"
        }
    }

@app.get("/crawler", response_class=HTMLResponse)
async def crawler_interface(request: Request):
    """Serve the crawler interface."""
    return templates.TemplateResponse("crawler.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_interface(request: Request):
    """Serve the login interface."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_interface(request: Request):
    """Serve the register interface."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

# Mock authentication endpoints
@app.get("/api/v1/auth/verify")
async def verify_auth():
    """Mock authentication verification."""
    return {"authenticated": True, "user": {"id": "test_user", "email": "test@example.com"}}

@app.post("/api/v1/auth/login")
async def login():
    """Mock login endpoint."""
    return {
        "access_token": "mock_token_123", 
        "token_type": "bearer",
        "user": {
            "user_id": "mock_user_123",
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "is_active": True
        },
        "expires_in": 3600
    }

@app.post("/api/v1/auth/register")
async def register():
    """Mock register endpoint."""
    return {
        "access_token": "mock_token_123", 
        "token_type": "bearer",
        "user": {
            "user_id": "mock_user_123",
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "is_active": True
        },
        "expires_in": 3600
    }

@app.get("/api/v1/auth/logout")
async def logout():
    """Mock logout endpoint."""
    return {"message": "Logged out successfully"}

# Mock chat endpoints
@app.get("/api/v1/chat/sessions")
async def get_chat_sessions():
    """Mock chat sessions endpoint."""
    return {"sessions": []}

@app.get("/api/v1/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Mock chat session endpoint."""
    return {"session_id": session_id, "messages": []}

@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_chat_messages(session_id: str):
    """Mock chat messages endpoint."""
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": "msg_1",
                "role": "assistant",
                "content": "Hello! I'm your AI assistant. How can I help you today?",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    }

@app.post("/api/v1/chat/sessions/{session_id}/chat")
async def send_chat_message(session_id: str):
    """Mock send chat message endpoint."""
    return {
        "session_id": session_id,
        "response": "Thank you for your message! I'm here to help you with any questions you have.",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/v1/chat/sessions")
async def create_chat_session():
    """Mock create chat session endpoint."""
    return {"session_id": "mock_session_123", "created": True}

# Mock crawler task endpoints
@app.post("/api/v1/crawler/tasks")
async def create_crawl_task():
    """Create a real crawl task."""
    import uuid
    from datetime import datetime
    
    task_id = str(uuid.uuid4())
    
    # Store the task in mock_tasks
    mock_tasks[task_id] = {
        "task_id": task_id,
        "status": "created",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return {
        "task_id": task_id,
        "status": "created",
        "message": "Crawl task created successfully",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/crawler/tasks/{task_id}")
async def get_crawl_task(task_id: str):
    """Get real crawl task status."""
    from datetime import datetime
    
    # Check if we have a stored result for this task
    task_result = mock_tasks.get(task_id, {})
    
    # Get the actual result from the crawler
    documents_found = len(crawler_documents) if 'crawler_documents' in globals() else 0
    total_documents = documents_found
    total_pages = 1  # For single page crawl
    
    return {
        "task_id": task_id,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": datetime.utcnow().isoformat() + "Z",
        "result": {
            "success": True,
            "documents_found": documents_found,
            "pages_crawled": total_pages,
            "total_documents": total_documents,
            "total_pages": total_pages,
            "downloads": []
        },
        "progress": {
            "documents_downloaded": documents_found,
            "pages_crawled": total_pages,
            "total_documents": total_documents,
            "total_pages": total_pages,
            "current_document": documents_found,
            "current_page": total_pages
        }
    }

@app.get("/api/v1/crawler/tasks")
async def list_crawl_tasks():
    """Mock list crawl tasks endpoint."""
    return {
        "tasks": [
            {
                "task_id": "mock_task_123",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
    }

@app.post("/api/v1/crawler/tasks/{task_id}/start")
async def start_crawl_task(task_id: str, max_doc_count: int = 1):
    """Start a crawl task with max document count."""
    try:
        # Get the task from our mock storage
        task = mock_tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        # For now, let's use a default URL for testing
        test_url = "https://www.irs.gov/forms-pubs"  # IRS has downloadable forms
        
        # Get ScrapingBee API key from environment
        import os
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            return {"error": "SCRAPINGBEE_API_KEY not found in environment"}
        
        logger.info(f"Starting enhanced crawl for task {task_id} with URL: {test_url}, max_doc_count: {max_doc_count}")
        
        # Use the enhanced crawler service
        enhanced_crawler = EnhancedCrawlerService(api_key=api_key)
        result = enhanced_crawler.crawl_with_max_docs(test_url, max_doc_count)
        
        logger.info(f"Enhanced crawl completed for task {task_id}: {result.get('documents_found', 0)} documents found")
        
        # Store documents globally for the documents endpoint
        global crawler_documents
        # Ensure documents are properly structured
        documents = result.get('documents', [])
        if documents and isinstance(documents[0], dict):
            crawler_documents = documents
        else:
            # If documents are raw content, convert to proper structure
            crawler_documents = []
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    # Convert raw HTML to document structure
                    crawler_documents.append({
                        "id": f"doc_{i}",
                        "url": test_url,
                        "title": f"Document {i+1}",
                        "content": doc[:1000] + "..." if len(doc) > 1000 else doc,  # Truncate for display
                        "content_type": "html",
                        "content_length": len(doc)
                    })
                else:
                    crawler_documents.append(doc)
        
        return {
            "task_id": task_id,
            "status": "completed",
            "message": f"Crawl task completed successfully with {result.get('documents_found', 0)} documents",
            "result": result,
            "max_doc_count": max_doc_count,
            "documents_found": result.get('documents_found', 0)
        }
            
    except Exception as e:
        logger.error(f"Failed to start crawl task {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }

# Global variable to store documents from crawler
crawler_documents = []

# Mock documents endpoints
@app.get("/api/v1/documents/")
async def get_documents():
    """Get real documents from crawler."""
    try:
        # Log the documents for debugging
        import logging
        logger = logging.getLogger("__main__")
        logger.info(f"Returning {len(crawler_documents)} documents")
        
        # Ensure documents are properly structured for JSON response
        structured_documents = []
        for i, doc in enumerate(crawler_documents):
            if isinstance(doc, dict):
                structured_documents.append(doc)
            else:
                # Convert raw content to structured format
                structured_documents.append({
                    "id": f"doc_{i}",
                    "url": "unknown",
                    "title": f"Document {i+1}",
                    "content": str(doc)[:1000] + "..." if len(str(doc)) > 1000 else str(doc),
                    "content_type": "html",
                    "content_length": len(str(doc))
                })
        
        return {
            "documents": structured_documents,
            "total": len(structured_documents)
        }
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        return {
            "documents": [],
            "total": 0,
            "error": str(e)
        }

class EnhancedCrawlerService:
    """Enhanced crawler service that handles max_doc_count logic."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.documents = []
        self.visited_urls = set()
        
    def crawl_with_max_docs(self, base_url: str, max_doc_count: int = 1) -> Dict[str, Any]:
        """
        Crawl with max document count logic.
        
        Args:
            base_url: Starting URL to crawl
            max_doc_count: Maximum number of documents to collect
            
        Returns:
            Dictionary with crawl results and documents
        """
        self.documents = []
        self.visited_urls = set()
        
        try:
            # Import required modules
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawler-service', 'src'))
            from crawler.advanced_crawler import AdvancedCrawler
            from crawler.link_extractor import LinkExtractor
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            # Initialize crawler
            crawler = AdvancedCrawler(api_key=self.api_key)
            
            # Extract domain for link extractor
            domain = urlparse(base_url).netloc
            
            # If max_doc_count = 1, only crawl the current page
            if max_doc_count == 1:
                logger.info(f"Crawling single page: {base_url}")
                result = self._crawl_and_save_page(crawler, base_url, domain)
                if result:
                    self.documents.append(result)
            else:
                # If max_doc_count > 1, crawl current page + sub-pages
                logger.info(f"Crawling with max_doc_count={max_doc_count}: {base_url}")
                self._crawl_recursive(crawler, base_url, domain, max_doc_count)
            
            # Clean up
            crawler.close()
            
            return {
                "success": True,
                "base_url": base_url,
                "max_doc_count": max_doc_count,
                "documents_found": len(self.documents),
                "documents": self.documents
            }
            
        except Exception as e:
            logger.error(f"Enhanced crawler failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents": self.documents
            }
    
    def _crawl_and_save_page(self, crawler: AdvancedCrawler, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Crawl a single page and save it as a document."""
        try:
            # Crawl the page
            result = crawler.crawl_url(url, content_type="generic")
            
            if not result.get('success'):
                logger.error(f"Failed to crawl {url}: {result.get('error')}")
                return None
            
            # Create document entry
            doc = {
                "url": url,
                "title": self._extract_title(result['content']),
                "content": result['content'],
                "content_type": "html",
                "content_length": len(result['content']),
                "crawl_time": result.get('crawl_time', 0),
                "status_code": result.get('status_code', 0)
            }
            
            logger.info(f"Saved HTML document: {url}")
            return doc
            
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return None
    
    def _crawl_and_save_file(self, crawler: AdvancedCrawler, url: str) -> Optional[Dict[str, Any]]:
        """Download and save a file (PDF, etc.)."""
        try:
            # Download the file
            result = crawler.download_file(url)
            
            if not result.get('success'):
                logger.error(f"Failed to download {url}: {result.get('error')}")
                return None
            
            # Create document entry
            doc = {
                "url": url,
                "title": self._extract_filename(url),
                "content": result.get('content', ''),
                "content_type": result.get('content_type', 'unknown'),
                "content_length": len(result.get('content', '')),
                "crawl_time": result.get('crawl_time', 0),
                "status_code": result.get('status_code', 0)
            }
            
            logger.info(f"Saved file document: {url}")
            return doc
            
        except Exception as e:
            logger.error(f"Error downloading file {url}: {e}")
            return None
    
    def _crawl_recursive(self, crawler: AdvancedCrawler, url: str, domain: str, max_doc_count: int):
        """Recursively crawl pages and documents until max_doc_count is reached."""
        if len(self.documents) >= max_doc_count:
            logger.info(f"Reached max_doc_count ({max_doc_count}), stopping crawl")
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling: {url} (documents found: {len(self.documents)}/{max_doc_count})")
        
        try:
            # Save the current page as a document first
            page_doc = self._crawl_and_save_page(crawler, url, domain)
            if page_doc:
                self.documents.append(page_doc)
                logger.info(f"Added page document: {url}")
            
            # Check if we've reached the limit
            if len(self.documents) >= max_doc_count:
                logger.info(f"Reached max_doc_count ({max_doc_count}) after adding page")
                return
            
            # Extract links from the page content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_doc['content'], 'html.parser')
            extractor = LinkExtractor(domain=domain)
            page_links, document_links = extractor.extract_links(soup, url, self.visited_urls)
            
            # First, try to download document links (PDFs, etc.)
            for doc_url in document_links:
                if len(self.documents) >= max_doc_count:
                    break
                
                if doc_url not in self.visited_urls:
                    doc = self._crawl_and_save_file(crawler, doc_url)
                    if doc:
                        self.documents.append(doc)
                        self.visited_urls.add(doc_url)
                        logger.info(f"Added file document: {doc_url}")
            
            # Then, crawl sub-pages if we haven't reached the limit
            for page_url in page_links:
                if len(self.documents) >= max_doc_count:
                    break
                
                if page_url not in self.visited_urls:
                    self._crawl_recursive(crawler, page_url, domain, max_doc_count)
                    
        except Exception as e:
            logger.error(f"Error in recursive crawl for {url}: {e}")
    
    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text(strip=True)
            return "Untitled"
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return "Untitled"
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1]
            return filename if filename else "Unknown File"
        except:
            return "Unknown File"

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Mock get document endpoint."""
    return {
        "id": document_id,
        "title": f"Document {document_id}",
        "url": f"https://example.com/{document_id}",
        "content": f"This is the content of document {document_id}...",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "crawler_test_server"}

# Create crawler router fallback (since crawler_router module is not available in test server)
from fastapi import APIRouter
crawler_router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])

@crawler_router.get("/health")
async def crawler_health():
    return {"status": "healthy", "service": "crawler_test_server"}

@crawler_router.get("/config")
async def crawler_config():
    return {"status": "available", "service": "crawler_test_server"}

@crawler_router.post("/crawl")
async def crawler_crawl():
    return {"status": "available", "service": "crawler_test_server"}

app.include_router(crawler_router)

if __name__ == "__main__":
    logger.info("Starting Crawler Test Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 