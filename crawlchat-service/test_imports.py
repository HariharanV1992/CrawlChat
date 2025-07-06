#!/usr/bin/env python3
"""
Test script to verify imports work correctly in the new folder structure
"""

import sys
import os
from pathlib import Path

def test_lambda_service_imports():
    """Test Lambda service imports."""
    print("🔍 Testing Lambda service imports...")
    
    # Change to lambda service directory
    lambda_dir = Path(__file__).parent / "lambda-service"
    os.chdir(lambda_dir)
    
    # Add src to path
    sys.path.insert(0, str(lambda_dir / "src"))
    
    try:
        # Test core imports
        from src.core.config import config
        from src.core.database import mongodb
        from src.core.logging import setup_logging
        print("✅ Core imports successful")
        
        # Test service imports
        from src.services.auth_service import auth_service
        from src.services.chat_service import chat_service
        from common.src.services.document_service import document_service
        from src.services.crawler_service import crawler_service
        print("✅ Service imports successful")
        
        # Test API imports
        from src.api.v1.auth import router as auth_router
        from src.api.v1.chat import router as chat_router
        from src.api.v1.crawler import router as crawler_router
        print("✅ API imports successful")
        
        print("✅ Lambda service imports: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Lambda service imports failed: {e}")
        return False

def test_crawler_service_imports():
    """Test Crawler service imports."""
    print("🔍 Testing Crawler service imports...")
    
    # Change to crawler service directory
    crawler_dir = Path(__file__).parent / "crawler-service"
    os.chdir(crawler_dir)
    
    # Add src to path
    sys.path.insert(0, str(crawler_dir / "src"))
    
    try:
        # Test core imports
        from src.core.config import config
        from src.core.database import mongodb
        from src.core.logging import setup_logging
        print("✅ Core imports successful")
        
        # Test crawler imports
        from src.crawler.advanced_crawler import AdvancedCrawler, CrawlConfig
        from src.crawler.settings_manager import SettingsManager
        print("✅ Crawler imports successful")
        
        # Test service imports
        from src.services.crawler_service import crawler_service
        from src.services.storage_service import get_storage_service
        print("✅ Service imports successful")
        
        print("✅ Crawler service imports: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Crawler service imports failed: {e}")
        return False

def test_preprocessor_service_imports():
    """Test Preprocessor service imports."""
    print("🔍 Testing Preprocessor service imports...")
    
    # Change to preprocessor service directory
    preprocessor_dir = Path(__file__).parent / "preprocessor-service"
    os.chdir(preprocessor_dir)
    
    try:
        # Test preprocessing service import
        import preprocessing_service
        print("✅ Preprocessing service import successful")
        
        print("✅ Preprocessor service imports: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Preprocessor service imports failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("🚀 Starting import tests for CrawlChat services...")
    print("=" * 60)
    
    # Store original directory
    original_dir = os.getcwd()
    
    try:
        # Test each service
        lambda_ok = test_lambda_service_imports()
        print()
        
        crawler_ok = test_crawler_service_imports()
        print()
        
        preprocessor_ok = test_preprocessor_service_imports()
        print()
        
        # Summary
        print("=" * 60)
        print("📊 Import Test Results:")
        print(f"  Lambda Service: {'✅ PASSED' if lambda_ok else '❌ FAILED'}")
        print(f"  Crawler Service: {'✅ PASSED' if crawler_ok else '❌ FAILED'}")
        print(f"  Preprocessor Service: {'✅ PASSED' if preprocessor_ok else '❌ FAILED'}")
        
        if all([lambda_ok, crawler_ok, preprocessor_ok]):
            print("\n🎉 All import tests PASSED! Services are ready for deployment.")
        else:
            print("\n⚠️  Some import tests FAILED. Please fix the issues before deployment.")
            
    finally:
        # Restore original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main() 