"""
Main FastAPI application for Stock Market Crawler Service
Updated for deployment testing - Triggering GitHub Actions deployment
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from common.src.core.config import config
from common.src.core.database import mongodb
from common.src.core.logging import setup_logging

# Lazy imports for Lambda optimization
def get_storage_service_lazy():
    from common.src.services.storage_service import get_storage_service
    return get_storage_service()

def get_crawler_service_lazy():
    from common.src.services.crawler_service import crawler_service
    return crawler_service

def get_chat_service_lazy():
    from common.src.services.chat_service import chat_service
    return chat_service

def get_document_service_lazy():
    from common.src.services.document_service import document_service
    return document_service

def get_auth_service_lazy():
    from common.src.services.auth_service import auth_service
    return auth_service

# Import API routers
from common.src.api.v1.auth import router as auth_router
from common.src.api.v1.chat import router as chat_router
from common.src.api.v1.documents import router as documents_router
from common.src.api.v1.vector_store import router as vector_store_router
from common.src.api.v1.preprocessing import router as preprocessing_router

# Setup logger first
logger = logging.getLogger(__name__)

# Import crawler router from new location
try:
    import sys
    import os
    # Add the crawler path to sys.path
    # Try multiple possible paths for Lambda container
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'crawler-service', 'src'),  # Local development
        os.path.join('/var/task', 'crawler-service', 'src'),  # Lambda container
        os.path.join(os.getcwd(), 'crawler-service', 'src'),  # Current working directory
    ]
    
    crawler_path = None
    for path in possible_paths:
        if os.path.exists(path):
            crawler_path = path
            break
    
    if crawler_path:
        sys.path.insert(0, crawler_path)
        logger.info(f"Added crawler path to sys.path: {crawler_path}")
    else:
        logger.warning("Could not find crawler path in any of the expected locations")
    from crawler_router import router as crawler_router
    logger.info("Successfully imported crawler router")
except ImportError as e:
    logger.warning(f"Failed to import crawler router: {e}")
    # Fallback for when crawler is not available
    from fastapi import APIRouter
    crawler_router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])
    
    @crawler_router.get("/health")
    async def crawler_health():
        return {"status": "crawler_not_available", "error": str(e)}
    
    @crawler_router.get("/config")
    async def crawler_config():
        return {"status": "crawler_not_available", "error": str(e)}
    
    @crawler_router.post("/crawl")
    async def crawler_crawl():
        return {"status": "crawler_not_available", "error": str(e)}
    
    @crawler_router.post("/tasks")
    async def create_task():
        import uuid
        task_id = str(uuid.uuid4())
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created successfully (fallback mode)"
        }
    
    @crawler_router.post("/tasks/{task_id}/start")
    async def start_task(task_id: str):
        return {
            "task_id": task_id,
            "status": "running",
            "message": "Task started successfully (fallback mode)"
        }
    
    @crawler_router.get("/tasks/{task_id}")
    async def get_task(task_id: str):
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task completed (fallback mode)",
            "documents_found": 0
        }

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CrawlChat - AI Document Analysis Platform...")
    
    # In Lambda, do minimal startup - defer everything until needed
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        # Lambda environment - minimal startup
        logger.info("Running in Lambda environment - minimal startup")
        # Skip all heavy operations during Lambda cold start
        # These will be done on-demand when endpoints are called
        pass
    else:
        # Non-Lambda environment - full startup
        logger.info("Running in non-Lambda environment - full startup")
        # Setup logging
        setup_logging()
        
        # Connect to MongoDB
        try:
            await mongodb.connect()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise RuntimeError("Database connection failed")
        
        # Create necessary directories
        config.setup_directories()
        
        # Ensure default user exists
        auth_service = get_auth_service_lazy()
        await auth_service.ensure_default_user()
    
    logger.info("CrawlChat - AI Document Analysis Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CrawlChat - AI Document Analysis Platform...")
    
    # Disconnect from MongoDB only if connected and not in Lambda
    if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        await mongodb.disconnect()

# Create FastAPI app
app = FastAPI(
    title="CrawlChat - AI Document Analysis Platform",
    description="Advanced AI-powered document analysis and chat platform for intelligent document processing and insights",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False
)

# Add middleware
import json

origins = os.getenv("CORS_ORIGINS", "[]")
try:
    origins = json.loads(origins)
except Exception:
    origins = ["https://api.crawlchat.site", "https://crawlchat.site", "http://localhost:8000", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add trusted host middleware for production
if config.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual allowed hosts
    )



# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Custom middleware to ensure CORS headers are always present
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses."""
    response = await call_next(request)
    
    # Add CORS headers if not already present
    if "access-control-allow-origin" not in response.headers:
        response.headers["access-control-allow-origin"] = "*"
    if "access-control-allow-methods" not in response.headers:
        response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    if "access-control-allow-headers" not in response.headers:
        response.headers["access-control-allow-headers"] = "*"
    if "access-control-allow-credentials" not in response.headers:
        response.headers["access-control-allow-credentials"] = "true"
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Fast health check - don't block on database operations
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": "healthy",
                "lambda": "healthy"
            },
            "environment": "lambda"
        }
        
        # Only check database if explicitly requested or in non-Lambda environment
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # In Lambda, return fast response without DB check
            return JSONResponse(content=health_status, status_code=200)
        else:
            # In non-Lambda environment, do full health check
            try:
                # Check if MongoDB client exists and is connected
                if mongodb.client is not None and mongodb.db is not None:
                    await mongodb.db.command('ping')
                    db_healthy = True
                else:
                    # Try to reconnect if not connected
                    await mongodb.connect()
                    if mongodb.db is not None:
                        await mongodb.db.command('ping')
                        db_healthy = True
                    else:
                        db_healthy = False
            except Exception as e:
                logger.error(f"MongoDB health check failed: {e}")
                db_healthy = False
            
            # Check storage service
            storage_service = get_storage_service_lazy()
            storage_info = storage_service.get_storage_info()
            
            health_status.update({
                "status": "healthy" if db_healthy else "unhealthy",
                "services": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "storage": "healthy" if storage_service.s3_client else "limited",
                    "crawler": "healthy",
                    "chat": "healthy",
                    "document": "healthy"
                },
                "metrics": {
                    "storage": storage_info
                }
            })
            
            status_code = 200 if db_healthy else 503
            return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Setup Jinja2 templates
import os
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Lambda environment: {os.environ.get('AWS_LAMBDA_FUNCTION_NAME')}")

# Test template paths
template_paths = ["templates", "/var/task/templates", os.path.join(os.getcwd(), "templates")]
for path in template_paths:
    exists = os.path.exists(path)
    logger.info(f"Template path '{path}': {'EXISTS' if exists else 'NOT FOUND'}")
    if exists:
        try:
            files = os.listdir(path)
            logger.info(f"Files in {path}: {files}")
        except Exception as e:
            logger.error(f"Error listing {path}: {e}")

templates = Jinja2Templates(directory="/var/task/templates")
logger.info("Jinja2Templates created with /var/task/templates")

# Root endpoint - redirect to chat interface
@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to login if not authenticated, otherwise to chat."""
    # Check if user has a valid token in cookies or headers
    auth_header = request.headers.get("authorization")
    cookies = request.cookies
    
    # Check for token in Authorization header or cookies
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    elif "access_token" in cookies:
        token = cookies["access_token"]
    
    # If no token, redirect to login
    if not token:
        return RedirectResponse(url="/login")
    
    # In Lambda, skip token verification for faster page loads
    # The frontend will handle authentication
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        # User has token, redirect to chat (let frontend validate)
        crawl_task = request.query_params.get("crawl_task")
        if crawl_task:
            return RedirectResponse(url=f"/chat?crawl_task={crawl_task}")
        else:
            return RedirectResponse(url="/chat")
    else:
        # Non-Lambda environment - verify token
        try:
            auth_service = get_auth_service_lazy()
            user = await auth_service.get_current_user(token)
            if not user:
                return RedirectResponse(url="/login")
            
            # User is authenticated, redirect to chat
            crawl_task = request.query_params.get("crawl_task")
            if crawl_task:
                return RedirectResponse(url=f"/chat?crawl_task={crawl_task}")
            else:
                return RedirectResponse(url="/chat")
        except Exception as e:
            logger.error(f"Error verifying token in root route: {e}")
            return RedirectResponse(url="/login")

# Web UI routes
@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Serve the chat interface."""
    # Temporarily disable server-side authentication to let frontend handle it
    # The frontend will check authentication and redirect if needed
    return templates.TemplateResponse("chat.html", {"request": request})
    
    # Original authentication code (commented out for now)
    # # Check if user has a valid token in cookies or headers
    # auth_header = request.headers.get("authorization")
    # cookies = request.cookies
    # 
    # # Check for token in Authorization header or cookies
    # token = None
    # if auth_header and auth_header.startswith("Bearer "):
    #     token = auth_header.replace("Bearer ", "")
    # elif "access_token" in cookies:
    #     token = cookies["access_token"]
    # 
    # # If no token, redirect to login
    # if not token:
    #     return RedirectResponse(url="/login")
    # 
    # # In Lambda, skip token verification for faster page loads
    # # The frontend will handle authentication
    # if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    #     # User has token, serve chat interface (let frontend validate)
    #     return templates.TemplateResponse("chat.html", {"request": request})
    # else:
    #     # Non-Lambda environment - verify token
    #     try:
    #         auth_service = get_auth_service_lazy()
    #         user = await auth_service.get_current_user(token)
    #         if not user:
    #             return RedirectResponse(url="/login")
    #         
    #         # User is authenticated, serve chat interface
    #         return templates.TemplateResponse("chat.html", {"request": request})
    #     except Exception as e:
    #         logger.error(f"Error verifying token in chat route: {e}")
    #         return RedirectResponse(url="/login")

@app.get("/crawler", response_class=HTMLResponse)
async def crawler_interface(request: Request):
    """Serve the crawler interface."""
    # Check if user has a valid token in cookies or headers
    auth_header = request.headers.get("authorization")
    cookies = request.cookies
    
    # Check for token in Authorization header or cookies
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    elif "access_token" in cookies:
        token = cookies["access_token"]
    
    # If no token, serve the page but let client-side handle auth
    if not token:
        return templates.TemplateResponse("crawler.html", {"request": request})
    
    # Verify token
    try:
        auth_service = get_auth_service_lazy()
        user = await auth_service.get_current_user(token)
        if not user:
            # Token invalid, serve the page but let client-side handle auth
            return templates.TemplateResponse("crawler.html", {"request": request})
        
        # User is authenticated, serve crawler interface
        return templates.TemplateResponse("crawler.html", {"request": request})
    except Exception as e:
        logger.error(f"Error verifying token in crawler route: {e}")
        # On error, serve the page but let client-side handle auth
        return templates.TemplateResponse("crawler.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_interface(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_interface(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/confirm-email", response_class=HTMLResponse)
async def confirm_email_interface(request: Request):
    """Email confirmation interface."""
    return templates.TemplateResponse("confirm_email.html", {"request": request})

@app.get("/test-mobile", response_class=HTMLResponse)
async def mobile_test_interface(request: Request):
    """Mobile responsiveness test interface."""
    return templates.TemplateResponse("test_mobile.html", {"request": request})

# Include API routers
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(crawler_router, prefix="/api/v1/crawler")
app.include_router(documents_router, prefix="/api/v1/documents")
app.include_router(vector_store_router, prefix="/api/v1")
app.include_router(preprocessing_router, prefix="/api/v1")

# Debug: List all registered routes
logger.info("=== ALL REGISTERED ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"Route: {route.path} - Methods: {getattr(route, 'methods', 'N/A')}")
        if hasattr(route, 'endpoint'):
            logger.info(f"  Endpoint: {route.endpoint}")
logger.info("=== END ROUTES ===")

# Mount static files - handle Lambda environment gracefully
# Determine the correct static directory path based on environment
STATIC_DIR = "/var/task/static" if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else "static"

logger.info(f"Static directory path: {STATIC_DIR}")
logger.info(f"Static directory exists: {os.path.exists(STATIC_DIR)}")

if os.path.exists(STATIC_DIR):
    # Mount static files using the correct path
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Static files mounted from: {STATIC_DIR}")
else:
    # Create a fallback static handler when static directory doesn't exist
    @app.get("/static/{path:path}")
    async def static_files(path: str):
        """Serve static files from the static directory."""
        static_path = os.path.join(STATIC_DIR, path)
        logger.info(f"Attempting to serve static file: {static_path}")
        
        if os.path.exists(static_path) and os.path.isfile(static_path):
            return FileResponse(static_path)
        else:
            logger.warning(f"Static file not found: {static_path}")
            raise HTTPException(status_code=404, detail="Static file not found")

# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock Market Crawler Service")
    parser.add_argument("--host", default=config.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=config.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=config.workers, help="Number of worker processes")
    
    args = parser.parse_args()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=config.log_level.lower()
    ) 