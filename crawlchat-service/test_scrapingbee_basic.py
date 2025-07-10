#!/usr/bin/env python3
"""
Basic test using the official ScrapingBee client
"""

import os

def test_scrapingbee_client():
    """Test the official ScrapingBee client with default render_js=True."""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not set")
        return False
    
    print("🧪 Testing Official ScrapingBee Client (render_js=True - default)")
    print("=" * 40)
    
    try:
        # Install the Python ScrapingBee library:    
        # pip install scrapingbee
        from scrapingbee import ScrapingBeeClient
        
        client = ScrapingBeeClient(api_key=api_key)
        
        print("✅ ScrapingBeeClient created successfully")
        
        # Test with default render_js=True (headless browser with JavaScript)
        test_url = "https://httpbin.org/ip"
        print(f"Testing URL: {test_url}")
        print("Using render_js=True (default) - headless browser with JavaScript")
        
        response = client.get(test_url)
        
        print(f'Response HTTP Status Code: {response.status_code}')
        print(f'Response HTTP Response Body: {response.content}')
        
        if response.status_code == 200:
            print("✅ ScrapingBee client test with render_js=True successful")
            return True
        else:
            print(f"❌ ScrapingBee client test with render_js=True failed: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ ScrapingBee library not installed. Run: pip install scrapingbee")
        return False
    except Exception as e:
        print(f"❌ Error in ScrapingBee client test: {e}")
        return False

def test_scrapingbee_without_js():
    """Test the official ScrapingBee client with render_js=False."""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not set")
        return False
    
    print("\n🧪 Testing Official ScrapingBee Client (render_js=False)")
    print("=" * 40)
    
    try:
        # Install the Python ScrapingBee library:      
        # pip install scrapingbee
        from scrapingbee import ScrapingBeeClient
        
        client = ScrapingBeeClient(api_key=api_key)
        
        print("✅ ScrapingBeeClient created successfully")
        
        # Test with render_js=False (no headless browser, no JavaScript)
        test_url = "https://httpbin.org/ip"
        print(f"Testing URL: {test_url}")
        print("Using render_js=False - no headless browser, no JavaScript")
        
        response = client.get(test_url, params={'render_js': 'False'})
        
        print(f'Response HTTP Status Code: {response.status_code}')
        print(f'Response HTTP Response Body: {response.content}')
        
        if response.status_code == 200:
            print("✅ ScrapingBee client test with render_js=False successful")
            return True
        else:
            print(f"❌ ScrapingBee client test with render_js=False failed: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ ScrapingBee library not installed. Run: pip install scrapingbee")
        return False
    except Exception as e:
        print(f"❌ Error in ScrapingBee client test: {e}")
        return False

def test_url_encoding():
    """Test URL encoding handling."""
    print("\n🧪 Testing URL Encoding")
    print("=" * 40)
    
    try:
        from scrapingbee import ScrapingBeeClient
        import urllib.parse
        
        api_key = os.getenv('SCRAPINGBEE_API_KEY')
        if not api_key:
            print("❌ SCRAPINGBEE_API_KEY not set")
            return False
        
        client = ScrapingBeeClient(api_key=api_key)
        
        # Test with a URL that contains special characters
        test_url = "https://httpbin.org/anything?param=value with spaces&another=test+plus"
        print(f"Original URL: {test_url}")
        
        # Show manual encoding (not needed with Python library)
        encoded_url = urllib.parse.quote(test_url)
        print(f"Manually encoded URL: {encoded_url}")
        print("Note: Python ScrapingBee library handles encoding automatically")
        
        # The library should handle encoding automatically
        response = client.get(test_url)
        
        print(f'Response HTTP Status Code: {response.status_code}')
        
        if response.status_code == 200:
            print("✅ URL encoding test successful")
            return True
        else:
            print(f"❌ URL encoding test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in URL encoding test: {e}")
        return False

def main():
    """Run the test."""
    print("🧪 Testing Basic ScrapingBee Integration")
    print("=" * 50)
    
    test1_success = test_scrapingbee_client()
    test2_success = test_scrapingbee_without_js()
    test3_success = test_url_encoding()
    
    print("\n" + "=" * 50)
    print("📊 Results Summary:")
    print(f"  render_js=True Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  render_js=False Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"  URL Encoding Test: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if test1_success and test2_success and test3_success:
        print("\n✅ All tests passed! ScrapingBee client is working correctly.")
    else:
        print("\n❌ Some tests failed. There may be configuration issues.")
    
    return test1_success and test2_success and test3_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 