#!/usr/bin/env python3
"""
Test script for the enhanced crawler with progressive proxy strategy.
Demonstrates all the new features including cost-effective crawling.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the lambda-service src to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.advanced_crawler import AdvancedCrawler, CrawlScenarios
from crawler.enhanced_scrapingbee_manager import ProxyMode, JavaScriptScenarios, ContentCheckers

def test_basic_crawling():
    """Test basic crawling with progressive proxy strategy."""
    print("🧪 Testing Basic Crawling with Progressive Proxy Strategy")
    print("=" * 60)
    
    # Initialize crawler
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test URLs (different types of sites)
    test_urls = [
        "https://example.com",  # Simple site (should work with standard)
        "https://httpbin.org/html",  # Test site
        "https://news.ycombinator.com",  # News site (might need premium)
    ]
    
    for url in test_urls:
        print(f"\n📄 Crawling: {url}")
        try:
            result = crawler.crawl_url(url, content_type="generic")
            
            if result["success"]:
                print(f"✅ Success! Mode: {result.get('proxy_mode', 'unknown')}")
                print(f"   Content length: {result['content_length']} chars")
                print(f"   Crawl time: {result['crawl_time']}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Show statistics
    stats = crawler.get_usage_stats()
    print(f"\n📊 Usage Statistics:")
    print(f"   Total requests: {stats['scrapingbee_stats']['total_requests']}")
    print(f"   Success rate: {stats['scrapingbee_stats']['success_rate']}%")
    print(f"   Cost estimate: ${stats['cost_estimate']['total_cost']}")
    
    crawler.close()
    return True

def test_js_scenarios():
    """Test JavaScript scenarios for interactive sites."""
    print("\n🧪 Testing JavaScript Scenarios")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test different scenarios
    scenarios = {
        "Load More Content": CrawlScenarios.news_site_scenario(),
        "E-commerce": CrawlScenarios.ecommerce_scenario(),
        "Social Media": CrawlScenarios.social_media_scenario(),
        "Financial Site": CrawlScenarios.financial_site_scenario(),
        "Blog": CrawlScenarios.blog_scenario(),
    }
    
    # Test with a simple site that supports JS
    test_url = "https://httpbin.org/delay/2"  # Simple delay test
    
    for scenario_name, scenario in scenarios.items():
        print(f"\n🎭 Testing {scenario_name} scenario")
        try:
            result = crawler.crawl_with_js_scenario(test_url, scenario)
            
            if result["success"]:
                print(f"✅ Success! Proxy mode: {result.get('proxy_mode', 'unknown')}")
                print(f"   Crawl time: {result['crawl_time']}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    crawler.close()
    return True

def test_content_checkers():
    """Test different content checkers."""
    print("\n🧪 Testing Content Checkers")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test different content types
    content_tests = [
        ("https://news.ycombinator.com", "news"),
        ("https://httpbin.org/html", "generic"),
    ]
    
    for url, content_type in content_tests:
        print(f"\n🔍 Testing {content_type} content checker: {url}")
        try:
            result = crawler.crawl_url(url, content_type=content_type)
            
            if result["success"]:
                print(f"✅ Success! Content type: {content_type}")
                print(f"   Content length: {result['content_length']} chars")
                print(f"   Proxy mode: {result.get('proxy_mode', 'unknown')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    crawler.close()
    return True

def test_file_download():
    """Test file downloading capabilities."""
    print("\n🧪 Testing File Download")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test file download (using a simple text file)
    test_file_url = "https://httpbin.org/robots.txt"
    
    print(f"\n📁 Downloading file: {test_file_url}")
    try:
        result = crawler.download_file(test_file_url)
        
        if result["success"]:
            print(f"✅ Success! File type: {result['file_type']}")
            print(f"   File size: {result['content_length']} bytes")
            print(f"   Download time: {result['download_time']}s")
            print(f"   Content preview: {result['content'][:100]}...")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    crawler.close()
    return True

def test_screenshot():
    """Test screenshot capabilities."""
    print("\n🧪 Testing Screenshot")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test screenshot
    test_url = "https://httpbin.org/html"
    
    print(f"\n📸 Taking screenshot: {test_url}")
    try:
        result = crawler.take_screenshot(test_url, full_page=True)
        
        if result["success"]:
            print(f"✅ Success! Screenshot size: {result['content_length']} bytes")
            print(f"   Screenshot time: {result['screenshot_time']}s")
            print(f"   Full page: {result['full_page']}")
            
            # Save screenshot for inspection
            screenshot_path = "/tmp/test_screenshot.png"
            with open(screenshot_path, "wb") as f:
                f.write(result['screenshot'])
            print(f"   Screenshot saved to: {screenshot_path}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    crawler.close()
    return True

def test_progressive_strategy():
    """Test the progressive proxy strategy specifically."""
    print("\n🧪 Testing Progressive Proxy Strategy")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test forcing different proxy modes
    test_url = "https://httpbin.org/html"
    
    for mode in [ProxyMode.STANDARD, ProxyMode.PREMIUM, ProxyMode.STEALTH]:
        print(f"\n🎯 Testing forced {mode.value} mode")
        try:
            # Force specific mode
            result = crawler.scrapingbee.make_progressive_request(
                test_url, 
                force_mode=mode
            )
            
            if result.status_code == 200:
                print(f"✅ Success with {mode.value} mode!")
                print(f"   Content length: {len(result.text)} chars")
            else:
                print(f"❌ Failed with {mode.value} mode: {result.status_code}")
                
        except Exception as e:
            print(f"❌ Exception with {mode.value} mode: {e}")
    
    # Show final statistics
    stats = crawler.get_usage_stats()
    print(f"\n📊 Final Statistics:")
    for mode, mode_stats in stats['scrapingbee_stats']['mode_breakdown'].items():
        print(f"   {mode}: {mode_stats['requests']} requests, "
              f"{mode_stats['success_rate']}% success rate, "
              f"{mode_stats['credits_used']} credits used")
    
    crawler.close()
    return True

def test_cost_effectiveness():
    """Test cost effectiveness of the progressive strategy."""
    print("\n🧪 Testing Cost Effectiveness")
    print("=" * 60)
    
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY environment variable not set")
        return False
    
    crawler = AdvancedCrawler(api_key)
    
    # Test multiple URLs to see cost distribution
    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
    ]
    
    print(f"\n💰 Testing cost effectiveness with {len(test_urls)} URLs")
    
    for url in test_urls:
        try:
            result = crawler.crawl_url(url)
            if result["success"]:
                print(f"✅ {url}: {result.get('proxy_mode', 'unknown')} mode")
            else:
                print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ {url}: Exception - {e}")
    
    # Show cost analysis
    stats = crawler.get_usage_stats()
    cost_estimate = stats['cost_estimate']
    
    print(f"\n💰 Cost Analysis:")
    print(f"   Total cost: ${cost_estimate['total_cost']}")
    print(f"   Total credits used: {cost_estimate['credits_used']}")
    
    for mode, cost in cost_estimate['mode_costs'].items():
        print(f"   {mode} mode: ${cost}")
    
    # Calculate cost savings
    if cost_estimate['mode_costs'].get('standard', 0) > 0:
        print(f"\n💡 Cost Savings:")
        print(f"   If all requests used premium: ${cost_estimate['credits_used'] * 0.025:.4f}")
        print(f"   Actual cost: ${cost_estimate['total_cost']:.4f}")
        savings = (cost_estimate['credits_used'] * 0.025) - cost_estimate['total_cost']
        print(f"   Savings: ${savings:.4f}")
    
    crawler.close()
    return True

def main():
    """Run all tests."""
    print("🚀 Enhanced Crawler Test Suite")
    print("Testing progressive proxy strategy and new features")
    print("=" * 80)
    
    tests = [
        ("Basic Crawling", test_basic_crawling),
        ("JavaScript Scenarios", test_js_scenarios),
        ("Content Checkers", test_content_checkers),
        ("File Download", test_file_download),
        ("Screenshot", test_screenshot),
        ("Progressive Strategy", test_progressive_strategy),
        ("Cost Effectiveness", test_cost_effectiveness),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced crawler is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 