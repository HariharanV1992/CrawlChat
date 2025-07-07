#!/usr/bin/env python3
"""
Comprehensive service health check for CrawlChat platform
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the common module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'common', 'src'))

def check_file_structure():
    """Check if all required files and directories exist"""
    print("🔍 Checking file structure...")
    print("=" * 60)
    
    required_files = [
        "common/src/services/auth_service.py",
        "common/src/services/chat_service.py", 
        "common/src/services/crawler_service.py",
        "common/src/services/document_service.py",
        "common/src/services/storage_service.py",
        "common/src/services/vector_store_service.py",
        "common/src/services/email_service.py",
        "common/src/services/aws_textract_service.py",
        "common/src/services/document_processing_service.py",
        "common/src/services/aws_background_service.py",
        "common/src/api/v1/auth.py",
        "common/src/api/v1/chat.py",
        "common/src/api/v1/crawler.py", 
        "common/src/api/v1/documents.py",
        "common/src/api/v1/vector_store.py",
        "common/src/core/config.py",
        "common/src/core/database.py",
        "common/src/core/exceptions.py",
        "common/src/core/logging.py",
        "common/src/models/auth.py",
        "common/src/models/chat.py",
        "common/src/models/crawler.py",
        "common/src/models/documents.py",
        "common/src/utils/prompts.py",
        "common/src/utils/security.py",
        "common/src/utils/validators.py",
        "lambda-service/main.py",
        "lambda-service/lambda_handler.py",
        "lambda-service/src/crawler/advanced_crawler.py",
        "lambda-service/src/crawler/settings_manager.py",
        "crawler-service/main.py",
        "crawler-service/lambda_handler.py",
        "preprocessor-service/preprocessing_service.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files found")
        return True

def check_service_instances():
    """Check if all service instances are properly created"""
    print("\n🔍 Checking service instances...")
    print("=" * 60)
    
    try:
        from services.auth_service import auth_service
        print("✅ auth_service instance created")
    except Exception as e:
        print(f"❌ auth_service error: {e}")
        return False
    
    try:
        from services.chat_service import chat_service
        print("✅ chat_service instance created")
    except Exception as e:
        print(f"❌ chat_service error: {e}")
        return False
    
    try:
        from services.crawler_service import crawler_service
        print("✅ crawler_service instance created")
    except Exception as e:
        print(f"❌ crawler_service error: {e}")
        return False
    
    try:
        from services.document_service import document_service
        print("✅ document_service instance created")
    except Exception as e:
        print(f"❌ document_service error: {e}")
        return False
    
    try:
        # Try direct import first
        from services.storage_service import StorageService
        storage_service = StorageService()
        print("✅ storage_service instance created")
    except Exception as e:
        print(f"❌ storage_service error: {e}")
        # Try alternative import
        try:
            from services.storage_service import get_storage_service
            storage_service = get_storage_service()
            print("✅ storage_service instance created (alternative)")
        except Exception as e2:
            print(f"❌ storage_service alternative error: {e2}")
            return False
    
    try:
        from services.vector_store_service import vector_store_service
        print("✅ vector_store_service instance created")
    except Exception as e:
        print(f"❌ vector_store_service error: {e}")
        return False
    
    try:
        from services.email_service import email_service
        print("✅ email_service instance created")
    except Exception as e:
        print(f"❌ email_service error: {e}")
        return False
    
    return True

def check_crawler_imports():
    """Check if crawler modules can be imported"""
    print("\n🔍 Checking crawler imports...")
    print("=" * 60)
    
    try:
        from services.crawler_service import crawler_service
        print("✅ crawler_service imported")
        
        # Check if crawler modules are available
        if hasattr(crawler_service, 'AdvancedCrawler') and crawler_service.AdvancedCrawler is not None:
            print("✅ AdvancedCrawler available")
        else:
            print("⚠️  AdvancedCrawler not available (may be lazy loaded)")
            
        if hasattr(crawler_service, 'CrawlConfig') and crawler_service.CrawlConfig is not None:
            print("✅ CrawlConfig available")
        else:
            print("⚠️  CrawlConfig not available (may be lazy loaded)")
            
        if hasattr(crawler_service, 'SettingsManager') and crawler_service.SettingsManager is not None:
            print("✅ SettingsManager available")
        else:
            print("⚠️  SettingsManager not available (may be lazy loaded)")
        
        # Check if we can import the models directly
        try:
            from models.crawler import CrawlConfig
            print("✅ CrawlConfig model imported")
        except Exception as e:
            print(f"❌ CrawlConfig model import error: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Crawler import error: {e}")
        return False

def check_configuration():
    """Check if configuration is properly loaded"""
    print("\n🔍 Checking configuration...")
    print("=" * 60)
    
    try:
        from core.config import config
        
        required_configs = [
            'mongodb_uri',
            'mongodb_db', 
            'secret_key',
            's3_bucket',
            's3_region',
            'openai_api_key',
            'smtp_username',
            'smtp_password'
        ]
        
        missing_configs = []
        for config_name in required_configs:
            if hasattr(config, config_name):
                value = getattr(config, config_name)
                if value:
                    print(f"✅ {config_name}: {'*' * len(str(value)) if 'password' in config_name or 'key' in config_name else str(value)[:20] + '...' if len(str(value)) > 20 else str(value)}")
                else:
                    print(f"⚠️  {config_name}: Not set")
                    missing_configs.append(config_name)
            else:
                print(f"❌ {config_name}: Not found")
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"\n⚠️  {len(missing_configs)} configurations missing or not set")
            return False
        else:
            print(f"\n✅ All configurations properly loaded")
            return True
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_api_routers():
    """Check if all API routers are properly defined"""
    print("\n🔍 Checking API routers...")
    print("=" * 60)
    
    try:
        from api.v1.auth import router as auth_router
        print("✅ auth_router imported")
    except Exception as e:
        print(f"❌ auth_router error: {e}")
        return False
    
    try:
        from api.v1.chat import router as chat_router
        print("✅ chat_router imported")
    except Exception as e:
        print(f"❌ chat_router error: {e}")
        return False
    
    try:
        from api.v1.crawler import router as crawler_router
        print("✅ crawler_router imported")
    except Exception as e:
        print(f"❌ crawler_router error: {e}")
        return False
    
    try:
        from api.v1.documents import router as documents_router
        print("✅ documents_router imported")
    except Exception as e:
        print(f"❌ documents_router error: {e}")
        return False
    
    try:
        from api.v1.vector_store import router as vector_store_router
        print("✅ vector_store_router imported")
    except Exception as e:
        print(f"❌ vector_store_router error: {e}")
        return False
    
    return True

def check_models():
    """Check if all models are properly defined"""
    print("\n🔍 Checking models...")
    print("=" * 60)
    
    try:
        from models.auth import User, UserCreate, Token, TokenData, UserResponse
        print("✅ Auth models imported")
    except Exception as e:
        print(f"❌ Auth models error: {e}")
        return False
    
    try:
        from models.chat import ChatMessage, ChatResponse, ChatRequest
        print("✅ Chat models imported")
    except Exception as e:
        print(f"❌ Chat models error: {e}")
        return False
    
    try:
        from models.crawler import CrawlTask, TaskStatus, CrawlConfig
        print("✅ Crawler models imported")
    except Exception as e:
        print(f"❌ Crawler models error: {e}")
        return False
    
    try:
        from models.documents import Document, DocumentType, DocumentUpload
        print("✅ Document models imported")
    except Exception as e:
        print(f"❌ Document models error: {e}")
        return False
    
    return True

def check_utils():
    """Check if utility modules are working"""
    print("\n🔍 Checking utilities...")
    print("=" * 60)
    
    try:
        from utils.prompts import PromptManager
        print("✅ PromptManager imported")
        
        # Test prompt detection
        test_queries = [
            ("thank you", "simple_acknowledgment"),
            ("what is the salary", "calculation"),
            ("summarize this", "summary"),
            ("analyze this document", "stock_analysis")
        ]
        
        for query, expected_type in test_queries:
            detected_type = PromptManager.detect_query_type(query)
            if detected_type == expected_type:
                print(f"✅ Query detection: '{query}' -> {detected_type}")
            else:
                print(f"❌ Query detection: '{query}' -> {detected_type} (expected: {expected_type})")
                return False
                
    except Exception as e:
        print(f"❌ Prompts utility error: {e}")
        return False
    
    try:
        from utils.security import verify_password, get_password_hash
        print("✅ Security utilities imported")
    except Exception as e:
        print(f"❌ Security utilities error: {e}")
        return False
    
    try:
        from utils.validators import validate_email, validate_password
        print("✅ Validator utilities imported")
    except Exception as e:
        print(f"❌ Validator utilities error: {e}")
        return False
    
    return True

async def check_database_connection():
    """Check if database connection works"""
    print("\n🔍 Checking database connection...")
    print("=" * 60)
    
    try:
        from core.database import mongodb
        
        # Try to connect
        await mongodb.connect()
        print("✅ MongoDB connection successful")
        
        # Test a simple operation
        collection = mongodb.get_collection("test")
        await collection.find_one({"_id": "test"})
        print("✅ MongoDB query successful")
        
        # Disconnect
        await mongodb.disconnect()
        print("✅ MongoDB disconnection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Run all health checks"""
    print("🏥 CrawlChat Service Health Check")
    print("=" * 60)
    
    results = []
    
    # File structure check
    results.append(("File Structure", check_file_structure()))
    
    # Service instances check
    results.append(("Service Instances", check_service_instances()))
    
    # Crawler imports check
    results.append(("Crawler Imports", check_crawler_imports()))
    
    # Configuration check
    results.append(("Configuration", check_configuration()))
    
    # API routers check
    results.append(("API Routers", check_api_routers()))
    
    # Models check
    results.append(("Models", check_models()))
    
    # Utilities check
    results.append(("Utilities", check_utils()))
    
    # Database connection check (async)
    async def run_db_check():
        return await check_database_connection()
    
    try:
        db_result = asyncio.run(run_db_check())
        results.append(("Database Connection", db_result))
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        results.append(("Database Connection", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All services are correctly configured and working!")
        return True
    else:
        print(f"\n⚠️  {failed} service(s) need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 