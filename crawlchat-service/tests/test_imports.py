#!/usr/bin/env python3
"""
Test script to verify all imports work correctly across the service.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_common_imports():
    """Test imports from the common package."""
    print("Testing common package imports...")
    
    try:
        # Test core imports
        from common.src.core.config import settings
        print("✅ common.src.core.config imported successfully")
        
        from common.src.core.database import get_database
        print("✅ common.src.core.database imported successfully")
        
        from common.src.core.logging import setup_logging
        print("✅ common.src.core.logging imported successfully")
        
        # Test API imports
        from common.src.api.dependencies import get_current_user
        print("✅ common.src.api.dependencies imported successfully")
        
        # Test models imports
        from common.src.models.auth import User
        print("✅ common.src.models.auth imported successfully")
        
        from common.src.models.documents import Document
        print("✅ common.src.models.documents imported successfully")
        
        # Test services imports
        from common.src.services.auth_service import AuthService
        print("✅ common.src.services.auth_service imported successfully")
        
        from common.src.services.document_service import DocumentService
        print("✅ common.src.services.document_service imported successfully")
        
        from common.src.services.vector_store_service import VectorStoreService
        print("✅ common.src.services.vector_store_service imported successfully")
        
        print("✅ All common package imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Common package import failed: {e}")
        return False

def test_lambda_service_imports():
    """Test imports from the lambda service."""
    print("\nTesting lambda service imports...")
    
    try:
        # Test lambda service imports
        from lambda_service.src.api.v1.auth import router as auth_router
        print("✅ lambda_service.src.api.v1.auth imported successfully")
        
        from lambda_service.src.api.v1.documents import router as documents_router
        print("✅ lambda_service.src.api.v1.documents imported successfully")
        
        from lambda_service.src.api.v1.chat import router as chat_router
        print("✅ lambda_service.src.api.v1.chat imported successfully")
        
        from lambda_service.src.services.aws_textract_service import AWSTextractService
        print("✅ lambda_service.src.services.aws_textract_service imported successfully")
        
        print("✅ All lambda service imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Lambda service import failed: {e}")
        return False

def test_crawler_service_imports():
    """Test imports from the crawler service."""
    print("\nTesting crawler service imports...")
    
    try:
        # Test crawler imports
        from crawler_service.src.crawler.advanced_crawler import AdvancedCrawler
        print("✅ crawler_service.src.crawler.advanced_crawler imported successfully")
        
        from crawler_service.src.crawler.smart_scrapingbee_manager import SmartScrapingBeeManager
        print("✅ crawler_service.src.crawler.smart_scrapingbee_manager imported successfully")
        
        from crawler_service.src.crawler.proxy_manager import ScrapingBeeProxyManager
        print("✅ crawler_service.src.crawler.proxy_manager imported successfully")
        
        from crawler_service.src.crawler.link_extractor import LinkExtractor
        print("✅ crawler_service.src.crawler.link_extractor imported successfully")
        
        from crawler_service.src.crawler.file_downloader import FileDownloader
        print("✅ crawler_service.src.crawler.file_downloader imported successfully")
        
        from crawler_service.src.crawler.settings_manager import SettingsManager
        print("✅ crawler_service.src.crawler.settings_manager imported successfully")
        
        print("✅ All crawler service imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Crawler service import failed: {e}")
        return False

def test_lambda_service_crawler_imports():
    """Test imports from the lambda service crawler module."""
    print("\nTesting lambda service crawler imports...")
    
    try:
        # Test lambda service crawler imports
        from lambda_service.src.crawler.advanced_crawler import AdvancedCrawler
        print("✅ lambda_service.src.crawler.advanced_crawler imported successfully")
        
        from lambda_service.src.crawler.smart_scrapingbee_manager import SmartScrapingBeeManager
        print("✅ lambda_service.src.crawler.smart_scrapingbee_manager imported successfully")
        
        from lambda_service.src.crawler.proxy_manager import ScrapingBeeProxyManager
        print("✅ lambda_service.src.crawler.proxy_manager imported successfully")
        
        print("✅ All lambda service crawler imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Lambda service crawler import failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("🧪 Starting import tests...\n")
    
    results = []
    
    # Test common package
    results.append(test_common_imports())
    
    # Test lambda service
    results.append(test_lambda_service_imports())
    
    # Test crawler service
    results.append(test_crawler_service_imports())
    
    # Test lambda service crawler
    results.append(test_lambda_service_crawler_imports())
    
    # Summary
    print("\n" + "="*50)
    print("📊 Import Test Summary")
    print("="*50)
    
    if all(results):
        print("✅ All import tests passed!")
        print("🚀 All services are ready for deployment!")
        return 0
    else:
        print("❌ Some import tests failed!")
        print("🔧 Please check the failed imports above.")
        return 1

if __name__ == "__main__":
    exit(main()) 