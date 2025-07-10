#!/usr/bin/env python3
"""
Test script for crawling Screener SATIN consolidated page and saving the HTML content.
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

url = "https://www.screener.in/company/SATIN/consolidated/"

print(f"\n🌐 Crawling: {url}\n{'='*60}")

start_time = time.time()
result = crawler.crawl_url(
    url=url,
    render_js=True,  # Screener pages are JS-heavy
    block_ads=True,
    block_resources=False,  # To get all financial tables
    window_width=1920,
    window_height=1080,
    premium_proxy=True,  # For higher success rate
    country_code="IN",   # Screener is an Indian site
    forward_headers=True,
    wait=2000,           # Wait for JS to load
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
    filename = f"satin_screener_{timestamp}.html"
    file_path = output_dir / filename
    
    # Save HTML content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(result.get('content'))
    
    print(f"\n💾 HTML saved to: {file_path}")
    print(f"📁 Full path: {file_path.absolute()}")
    print(f"📏 File size: {file_path.stat().st_size} bytes")
    
    # Also save as a simple text file for easier viewing
    txt_filename = f"satin_screener_{timestamp}.txt"
    txt_path = output_dir / txt_filename
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"URL: {url}\n")
        f.write(f"Crawled at: {datetime.now().isoformat()}\n")
        f.write(f"Status: {result.get('status_code')}\n")
        f.write(f"Content length: {result.get('content_length')}\n")
        f.write("="*80 + "\n")
        f.write(result.get('content'))
    
    print(f"📄 Text version saved to: {txt_path}")
    
    # Show first 500 chars of content
    print(f"\n📋 First 500 chars of content:\n{result.get('content', '')[:500]}")
    
else:
    print(f"❌ Failed to save: {result.get('error', 'Unknown error')}")

print(f"\n📂 Output directory: {output_dir.absolute()}")
print(f"🔍 You can view the files with:")
print(f"   cat {file_path}")
print(f"   or open in a web browser: {file_path}") 