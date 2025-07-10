#!/usr/bin/env python3
"""
Test script for crawling Screener SATIN consolidated page using the full advanced crawler.
"""
import os
import sys
import time
from pathlib import Path

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
    # scraping_config="Your-Config-Name",  # Uncomment if you have a preconfigured config
)
elapsed = time.time() - start_time

print(f"Status: {result.get('status_code')}")
print(f"Success: {result.get('success')}")
print(f"Elapsed: {elapsed:.2f}s")
print(f"Content length: {result.get('content_length')}")
print(f"Proxy mode: {result.get('proxy_mode')}")
print(f"Headers: {result.get('headers')}")
print(f"First 500 chars of content:\n{result.get('content', '')[:500]}") 