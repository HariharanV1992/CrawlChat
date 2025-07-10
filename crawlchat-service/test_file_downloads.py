#!/usr/bin/env python3
"""
Test script for file download functionality using ScrapingBee API.
Tests downloading various file types including images, PDFs, and documents.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_file_downloads():
    """Test file download functionality with various file types."""
    
    print("🔧 Initializing AdvancedCrawler...")
    
    try:
        # Try to import the crawler
        from lambda_service.src.crawler.advanced_crawler import AdvancedCrawler
        print("✅ AdvancedCrawler imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import AdvancedCrawler: {e}")
        print("Trying alternative import path...")
        try:
            sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))
            from crawler.advanced_crawler import AdvancedCrawler
            print("✅ AdvancedCrawler imported successfully from alternative path")
        except ImportError as e2:
            print(f"❌ Failed to import from alternative path: {e2}")
            return
    
    # Initialize crawler
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return
    
    crawler = AdvancedCrawler(api_key=api_key)
    print("✅ AdvancedCrawler initialized successfully")
    
    print("\n📁 Testing File Download Functionality")
    print("=" * 60)
    
    # Test URLs for different file types
    test_files = [
        {
            "name": "Sample PDF",
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "expected_type": "application/pdf"
        },
        {
            "name": "Sample Image (JPEG)",
            "url": "https://httpbin.org/image/jpeg",
            "expected_type": "image/jpeg"
        },
        {
            "name": "Sample Image (PNG)",
            "url": "https://httpbin.org/image/png",
            "expected_type": "image/png"
        },
        {
            "name": "Sample Image (WebP)",
            "url": "https://httpbin.org/image/webp",
            "expected_type": "image/webp"
        },
        {
            "name": "Sample JSON",
            "url": "https://httpbin.org/json",
            "expected_type": "application/json"
        },
        {
            "name": "Sample XML",
            "url": "https://httpbin.org/xml",
            "expected_type": "application/xml"
        }
    ]
    
    results = []
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n📋 Test {i}: {test_file['name']}")
        print("-" * 40)
        print(f"   🎯 URL: {test_file['url']}")
        print(f"   📄 Expected Type: {test_file['expected_type']}")
        
        start_time = time.time()
        
        try:
            # Test with download_file=True
            result = crawler.crawl_url(
                url=test_file['url'],
                render_js=False,  # Recommended for file downloads
                download_file=True
            )
            
            download_time = time.time() - start_time
            
            if result.get('success', False):
                print(f"   ✅ Status: {result['status_code']}")
                print(f"   ⏱️  Time: {download_time:.2f}s")
                print(f"   📏 Content length: {result.get('content_length', 0)} bytes")
                print(f"   📄 Detected Type: {result.get('file_type', 'unknown')}")
                print(f"   🏷️  Content-Type: {result.get('content_type', 'unknown')}")
                
                # Check if file size is within limits
                if result.get('content_length', 0) > 2 * 1024 * 1024:
                    print(f"   ⚠️  Warning: File size exceeds 2MB limit")
                
                # Validate file type detection
                detected_type = result.get('file_type', 'unknown')
                if detected_type == test_file['expected_type']:
                    print(f"   ✅ File type detection: Correct")
                else:
                    print(f"   ⚠️  File type detection: Expected {test_file['expected_type']}, got {detected_type}")
                
                results.append({
                    "name": test_file['name'],
                    "success": True,
                    "time": download_time,
                    "size": result.get('content_length', 0),
                    "type": detected_type
                })
                
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                results.append({
                    "name": test_file['name'],
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                "name": test_file['name'],
                "success": False,
                "error": str(e)
            })
    
    # Test file size limit
    print(f"\n📋 Test: Large File (should fail)")
    print("-" * 40)
    print("   🎯 Testing 2MB file size limit")
    
    try:
        # Try to download a large file (this should fail)
        result = crawler.crawl_url(
            url="https://httpbin.org/bytes/3000000",  # 3MB file
            render_js=False,
            download_file=True
        )
        
        if result.get('success', False):
            print(f"   ⚠️  Unexpected success: {result.get('content_length', 0)} bytes")
        else:
            print(f"   ✅ Expected failure: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ✅ Expected exception: {e}")
    
    # Test without download_file parameter
    print(f"\n📋 Test: HTML Page (download_file=False)")
    print("-" * 40)
    print("   🎯 Testing regular HTML crawling")
    
    try:
        result = crawler.crawl_url(
            url="https://httpbin.org/html",
            render_js=False,
            download_file=False
        )
        
        if result.get('success', False):
            print(f"   ✅ Status: {result['status_code']}")
            print(f"   📏 Content length: {result.get('content_length', 0)} chars")
            print(f"   📄 Content type: {result.get('content_type', 'unknown')}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    print("=" * 60)
    
    successful_downloads = [r for r in results if r.get('success', False)]
    failed_downloads = [r for r in results if not r.get('success', False)]
    
    if successful_downloads:
        avg_time = sum(r['time'] for r in successful_downloads) / len(successful_downloads)
        total_size = sum(r['size'] for r in successful_downloads)
        print(f"Successful downloads: {len(successful_downloads)}/{len(results)}")
        print(f"Average download time: {avg_time:.2f}s")
        print(f"Total downloaded: {total_size} bytes ({total_size/1024:.1f} KB)")
        
        print(f"\n📈 Successful Downloads:")
        for result in successful_downloads:
            print(f"   {result['name']}: {result['time']:.2f}s, {result['size']} bytes, {result['type']}")
    
    if failed_downloads:
        print(f"\n❌ Failed Downloads:")
        for result in failed_downloads:
            print(f"   {result['name']}: {result.get('error', 'Unknown error')}")
    
    # Success rate
    success_rate = len(successful_downloads) / len(results) * 100 if results else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    # Usage stats
    print("\n📈 Usage Statistics:")
    print("=" * 60)
    stats = crawler.get_usage_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ File download testing completed!")
    print("\n💡 Usage Tips:")
    print("   - Use download_file=True to download file content")
    print("   - Recommended to use render_js=False for file downloads")
    print("   - File size limit is 2MB per request")
    print("   - Supports images, PDFs, documents, archives, and more")
    print("   - Automatic file type detection from URL and content")
    print("   - Returns binary content for non-text files")
    print("\n🔧 Example Usage:")
    print("   result = crawler.crawl_url(")
    print("       url='https://example.com/document.pdf',")
    print("       render_js=False,")
    print("       download_file=True")
    print("   )")
    print("\n📄 Supported File Types:")
    print("   Images: JPEG, PNG, GIF, BMP, TIFF, WebP, SVG")
    print("   Documents: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX")
    print("   Text: TXT, CSV, JSON, XML")
    print("   Archives: ZIP, RAR, 7Z, TAR, GZ")

if __name__ == "__main__":
    test_file_downloads() 