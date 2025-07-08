#!/usr/bin/env python3
"""
Optimized Lambda handler for CrawlChat API with cold start optimization.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Setup basic logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

# Global variables for lazy loading
_app = None
_handler = None

def get_app():
    """Lazy load the FastAPI app to avoid cold start issues."""
    global _app
    
    if _app is None:
        try:
            logger.info("Loading FastAPI app...")
            
            # Import only what's needed for the app
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            from mangum import Mangum
            
            # Import API routers
            from common.src.api.v1.auth import router as auth_router
            from common.src.api.v1.chat import router as chat_router
            from common.src.api.v1.crawler import router as crawler_router
            from common.src.api.v1.documents import router as documents_router
            from common.src.api.v1.vector_store import router as vector_store_router
            from common.src.api.v1.preprocessing import router as preprocessing_router
            
            # Create minimal FastAPI app
            app = FastAPI(
                title="CrawlChat - AI Document Analysis Platform",
                description="Advanced AI-powered document analysis and chat platform",
                version="2.0.0",
                docs_url="/docs",
                redoc_url="/redoc"
            )
            
            # Add CORS middleware
            origins = os.getenv("CORS_ORIGINS", "[]")
            try:
                origins = json.loads(origins)
            except Exception:
                origins = ["https://api.crawlchat.site", "https://crawlchat.site"]
            
            app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Add health check endpoint
            @app.get("/health")
            async def health_check():
                """Fast health check endpoint."""
                return {
                    "status": "healthy",
                    "environment": "lambda",
                    "timestamp": "2025-07-08T10:30:00Z"
                }
            
            # Include API routers
            app.include_router(auth_router, prefix="/api/v1/auth")
            app.include_router(chat_router, prefix="/api/v1/chat")
            app.include_router(crawler_router, prefix="/api/v1/crawler")
            app.include_router(documents_router, prefix="/api/v1/documents")
            app.include_router(vector_store_router, prefix="/api/v1")
            app.include_router(preprocessing_router, prefix="/api/v1")
            
            _app = app
            logger.info("FastAPI app loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FastAPI app: {e}")
            raise
    
    return _app

def get_handler():
    """Lazy load the Mangum handler."""
    global _handler
    
    if _handler is None:
        try:
            logger.info("Creating Mangum handler...")
            from mangum import Mangum
            app = get_app()
            _handler = Mangum(app, lifespan="off")
            logger.info("Mangum handler created successfully")
        except Exception as e:
            logger.error(f"Failed to create Mangum handler: {e}")
            raise
    
    return _handler

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        logger.info(f"Lambda handler called with event type: {event.get('httpMethod', 'unknown')}")
        
        # Get the handler and process the request
        handler = get_handler()
        response = handler(event, context)
        
        logger.info("Lambda handler completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        
        # Return a proper error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": "2025-07-08T10:30:00Z"
            })
        }

# For local testing
if __name__ == "__main__":
    # Test the handler locally
    test_event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {},
        "queryStringParameters": None,
        "body": None
    }
    
    test_context = None
    
    response = lambda_handler(test_event, test_context)
    print("Test response:", json.dumps(response, indent=2)) 