"""
Main FastAPI application for Stock Market Crawler Service
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.core.config import config
from src.core.database import mongodb
from src.core.logging import setup_logging
from src.services.storage_service import get_storage_service
from src.services.crawler_service import crawler_service
from src.services.chat_service import chat_service
from src.services.document_service import document_service
from src.services.auth_service import auth_service

# Import API routers
from src.api.v1.auth import router as auth_router
from src.api.v1.chat import router as chat_router
from src.api.v1.crawler import router as crawler_router
from src.api.v1.documents import router as documents_router
from src.api.v1.vector_store import router as vector_store_router

# Setup logger
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CrawlChat - AI Document Analysis Platform...")
    
    # Setup logging (only if not in Lambda)
    if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
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
    await auth_service.ensure_default_user()
    
    logger.info("CrawlChat - AI Document Analysis Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CrawlChat - AI Document Analysis Platform...")
    
    # Disconnect from MongoDB
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.crawlchat.site", "https://crawlchat.site"],  # Allow both domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check MongoDB connection
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
        storage_service = get_storage_service()
        storage_info = storage_service.get_storage_info()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
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
        }
        
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
templates = Jinja2Templates(directory="templates")

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
    
    # Verify token
    try:
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
    
    # Verify token
    try:
        user = await auth_service.get_current_user(token)
        if not user:
            return RedirectResponse(url="/login")
        
        # User is authenticated, serve chat interface
        return templates.TemplateResponse("chat.html", {"request": request})
    except Exception as e:
        logger.error(f"Error verifying token in chat route: {e}")
        return RedirectResponse(url="/login")

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add Lambda handler for AWS deployment
import json
from mangum import Mangum

# Create Mangum handler for AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda handler for FastAPI application."""
    try:
        # Handle the request through Mangum
        response = handler(event, context)
        return response
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            }
        }

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