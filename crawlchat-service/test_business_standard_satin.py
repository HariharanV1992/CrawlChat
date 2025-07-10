#!/usr/bin/env python3
"""
Test script for crawling Business Standard search results for SATIN news using the advanced crawler.
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add lambda-service/src to path for import
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

try:
    from crawler.advanced_crawler import AdvancedCrawler
except ImportError as e:
    print(f"❌ Failed to import AdvancedCrawler: {e}")
    sys.exit(1)

api_key = os.getenv('SCRAPINGBEE_API_KEY')
if not api_key:
    print("❌ SCRAPINGBEE_API_KEY environment variable not set")
    sys.exit(1)

crawler = AdvancedCrawler(api_key=api_key)

url = "https://www.business-standard.com/search?q=satin&type=news"

print(f"\n🌐 Crawling: {url}\n{'='*60}")

start_time = time.time()
result = crawler.crawl_url(
    url=url,
    render_js=True,  # Business Standard uses dynamic content
    block_ads=True,
    block_resources=False,  # To get all news content
    window_width=1920,
    window_height=1080,
    premium_proxy=True,  # For higher success rate
    country_code="IN",   # Business Standard is an Indian site
    forward_headers=True,
    wait=3000,           # Wait longer for news content to load
    download_file=False  # Not a file download, just HTML
)
elapsed = time.time() - start_time

print(f"Status: {result.get('status_code')}")
print(f"Success: {result.get('success')}")
print(f"Elapsed: {elapsed:.2f}s")
print(f"Content length: {result.get('content_length')}")

# Save the HTML content to a file
if result.get('success') and result.get('content'):
    # Create output directory
    output_dir = Path(__file__).parent / "crawled_data"
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"business_standard_satin_news_{timestamp}.html"
    file_path = output_dir / filename
    
    # Save HTML content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(result.get('content'))
    
    print(f"\n💾 HTML saved to: {file_path}")
    print(f"📁 Full path: {file_path.absolute()}")
    print(f"📏 File size: {file_path.stat().st_size} bytes")
    
    # Show first 500 chars of content
    print(f"\n📋 First 500 chars of content:\n{result.get('content', '')[:500]}")
    
else:
    print(f"❌ Failed to save: {result.get('error', 'Unknown error')}")

print(f"\n📂 Output directory: {output_dir.absolute()}")
print(f"🔍 You can view the file with:")
print(f"   cat {file_path}")
print(f"   or open in a web browser: {file_path}") 