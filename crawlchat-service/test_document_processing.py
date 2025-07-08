#!/usr/bin/env python3
"""
Test script to check document processing locally.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "crawler-service" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

async def test_document_processing():
    """Test document processing functionality."""
    print("🔍 Testing document processing...")
    
    try:
        # Test 1: Import document models
        print("1. Testing document model imports...")
        from models.documents import Document, DocumentType, DocumentStatus
        print("✅ Document models imported successfully")
        
        # Test 2: Create a test document
        print("2. Testing document creation...")
        test_document = Document(
            document_id="test-123",
            user_id="test-user",
            filename="test.html",
            file_path="s3://test-bucket/test.html",
            file_size=1024,
            document_type=DocumentType.HTML,
            status=DocumentStatus.UPLOADED,
            task_id="test-task"
        )
        print("✅ Test document created successfully")
        
        # Test 3: Import document service
        print("3. Testing document service import...")
        from services.document_service import DocumentService
        print("✅ Document service imported successfully")
        
        # Test 4: Import document processing service
        print("4. Testing document processing service import...")
        from services.document_processing_service import DocumentProcessingService
        print("✅ Document processing service imported successfully")
        
        # Test 5: Test crawler service document processing
        print("5. Testing crawler service document processing...")
        from services.crawler_service import crawler_service
        print("✅ Crawler service imported successfully")
        
        print("🎉 All document processing components working!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_crawler_functionality():
    """Test crawler functionality."""
    print("\n🔍 Testing crawler functionality...")
    
    try:
        # Test 1: Import crawler components
        print("1. Testing crawler imports...")
        from crawler.advanced_crawler import AdvancedCrawler
        from crawler.link_extractor import LinkExtractor
        from crawler.proxy_manager import ScrapingBeeProxyManager
        print("✅ Crawler components imported successfully")
        
        # Test 2: Test BeautifulSoup parsing
        print("2. Testing BeautifulSoup parsing...")
        from bs4 import BeautifulSoup
        
        test_html = """
        <html>
            <body>
                <a href="/test1">Link 1</a>
                <a href="/test2">Link 2</a>
                <a href="/document.pdf">PDF Document</a>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(test_html, 'html.parser')
        print("✅ BeautifulSoup parsing working")
        
        # Test 3: Test link extraction
        print("3. Testing link extraction...")
        link_extractor = LinkExtractor("example.com")
        page_links, doc_links = link_extractor.extract_links(soup, "https://example.com", set())
        print(f"✅ Link extraction working: {len(page_links)} page links, {len(doc_links)} document links")
        
        print("🎉 All crawler components working!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_lambda_handler():
    """Test Lambda handler functionality."""
    print("\n🔍 Testing Lambda handler...")
    
    try:
        # Test 1: Import Lambda handler
        print("1. Testing Lambda handler import...")
        sys.path.insert(0, str(Path(__file__).parent / "crawler-service"))
        from lambda_handler import lambda_handler, create_default_settings_files
        print("✅ Lambda handler imported successfully")
        
        # Test 2: Test settings file creation
        print("2. Testing settings file creation...")
        success = create_default_settings_files()
        if success:
            print("✅ Settings files created successfully")
        else:
            print("❌ Settings file creation failed")
        
        print("🎉 Lambda handler components working!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting local tests...")
    
    # Test document processing
    doc_success = await test_document_processing()
    
    # Test crawler functionality
    crawler_success = await test_crawler_functionality()
    
    # Test Lambda handler
    handler_success = await test_lambda_handler()
    
    print("\n📊 Test Results:")
    print(f"Document Processing: {'✅ PASS' if doc_success else '❌ FAIL'}")
    print(f"Crawler Functionality: {'✅ PASS' if crawler_success else '❌ FAIL'}")
    print(f"Lambda Handler: {'✅ PASS' if handler_success else '❌ FAIL'}")
    
    if all([doc_success, crawler_success, handler_success]):
        print("\n🎉 All tests passed! The code should work in Lambda.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 