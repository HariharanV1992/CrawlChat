#!/usr/bin/env python3
"""
Test script to verify CrawlTask attributes are available
"""

import sys
import os
from pathlib import Path

# Add the common module to path
sys.path.insert(0, str(Path(__file__).parent))

def test_crawl_task_attributes():
    """Test that CrawlTask has all required attributes."""
    try:
        from common.src.models.crawler import CrawlTask, TaskStatus
        
        # Create a test task with minimal required attributes
        task = CrawlTask(
            task_id="test-task-id",
            user_id="test-user-id",
            url="https://example.com",
            max_documents=5,
            max_pages=10,
            max_workers=3
        )
        
        print("✅ CrawlTask created successfully")
        
        # Test all attributes that are accessed in the crawler service
        required_attributes = [
            'task_id', 'user_id', 'url', 'status', 'created_at', 'updated_at',
            'started_at', 'completed_at', 'max_documents', 'max_pages', 'max_workers',
            'timeout', 'total_timeout', 'page_timeout', 'request_timeout',
            'connection_limit', 'tcp_connector_limit', 'keepalive_timeout',
            'delay', 'min_file_size', 'output_dir', 'use_proxy', 'proxy_api_key',
            'proxy_method', 'country_code', 'premium', 'bypass', 'render', 'retry',
            'session_number', 'enable_compression', 'max_pages_without_documents',
            'render_js', 'block_ads', 'block_resources', 'wait', 'wait_for',
            'wait_browser', 'window_width', 'window_height', 'premium_proxy',
            'stealth_proxy', 'own_proxy', 'forward_headers', 'forward_headers_pure',
            'download_file', 'scraping_config', 'pages_crawled', 'documents_downloaded',
            'errors', 'downloaded_files', 's3_files', 'metadata'
        ]
        
        missing_attributes = []
        for attr in required_attributes:
            if hasattr(task, attr):
                print(f"✅ {attr}: {getattr(task, attr)}")
            else:
                print(f"❌ {attr}: MISSING")
                missing_attributes.append(attr)
        
        if missing_attributes:
            print(f"\n❌ Missing attributes: {missing_attributes}")
            return False
        else:
            print(f"\n✅ All {len(required_attributes)} required attributes are present")
            return True
            
    except Exception as e:
        print(f"❌ Error testing CrawlTask attributes: {e}")
        return False

def test_crawl_task_creation_with_all_params():
    """Test creating CrawlTask with all parameters."""
    try:
        from common.src.models.crawler import CrawlTask, TaskStatus
        
        # Create a task with all parameters
        task = CrawlTask(
            task_id="test-task-id",
            user_id="test-user-id",
            url="https://example.com",
            max_documents=5,
            max_pages=10,
            max_workers=3,
            timeout=30,
            total_timeout=1800,
            page_timeout=60,
            request_timeout=30,
            connection_limit=100,
            tcp_connector_limit=100,
            keepalive_timeout=30,
            delay=0.05,
            min_file_size=1024,
            output_dir="/tmp/data/crawled",
            use_proxy=False,
            proxy_api_key=None,
            proxy_method="http",
            country_code="us",
            premium=False,
            bypass=False,
            render=False,
            retry=3,
            session_number=0,
            enable_compression=True,
            max_pages_without_documents=10,
            render_js=True,
            block_ads=False,
            block_resources=True,
            wait=None,
            wait_for=None,
            wait_browser=None,
            window_width=1920,
            window_height=1080,
            premium_proxy=False,
            stealth_proxy=False,
            own_proxy=None,
            forward_headers=False,
            forward_headers_pure=False,
            download_file=False,
            scraping_config=None
        )
        
        print("✅ CrawlTask created with all parameters successfully")
        
        # Test accessing specific attributes that are used in the crawler service
        test_attributes = {
            'url': task.url,
            'render_js': task.render_js,
            'block_ads': task.block_ads,
            'block_resources': task.block_resources,
            'wait': task.wait,
            'wait_for': task.wait_for,
            'wait_browser': task.wait_browser,
            'window_width': task.window_width,
            'window_height': task.window_height,
            'premium_proxy': task.premium_proxy,
            'country_code': task.country_code,
            'stealth_proxy': task.stealth_proxy,
            'own_proxy': task.own_proxy,
            'forward_headers': task.forward_headers,
            'forward_headers_pure': task.forward_headers_pure,
            'download_file': task.download_file,
            'scraping_config': task.scraping_config
        }
        
        print("✅ All crawler-specific attributes accessible:")
        for attr, value in test_attributes.items():
            print(f"  {attr}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating CrawlTask with all parameters: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing CrawlTask Attributes")
    print("=" * 50)
    
    tests = [
        ("Basic Attributes Test", test_crawl_task_attributes),
        ("Full Parameters Test", test_crawl_task_creation_with_all_params),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CrawlTask has all required attributes.")
        return True
    else:
        print("⚠️  Some tests failed. CrawlTask may be missing attributes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 