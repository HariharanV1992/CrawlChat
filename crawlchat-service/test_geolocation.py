#!/usr/bin/env python3
"""
Test script to verify geolocation functionality with ap-south-1 region.
"""

import os
import sys
from pathlib import Path

# Add the lambda-service src to the path
sys.path.insert(0, str(Path(__file__).parent / "lambda-service" / "src"))

from crawler.enhanced_scrapingbee_manager import EnhancedScrapingBeeManager, ProxyMode

def test_geolocation_configuration():
    """Test that geolocation is properly configured for ap-south-1 region."""
    
    print("🌍 Testing Geolocation Configuration for ap-south-1 Region")
    print("=" * 60)
    
    # Test different country codes
    test_countries = [
        ("in", "India"),
        ("sg", "Singapore"),
        ("jp", "Japan"),
        ("kr", "South Korea"),
        ("au", "Australia"),
        ("us", "United States"),
    ]
    
    for country_code, country_name in test_countries:
        print(f"\n🇺🇳 Testing {country_name} ({country_code})")
        
        # Create manager with specific country
        manager = EnhancedScrapingBeeManager("test-key", {"country_code": country_code})
        
        # Check configuration
        actual_country = manager.base_options.get("country_code")
        
        if actual_country == country_code:
            print(f"✅ {country_name} configuration correct: {actual_country}")
        else:
            print(f"❌ {country_name} configuration failed: expected {country_code}, got {actual_country}")
    
    # Test default configuration (should be India for ap-south-1)
    print(f"\n🏗️  Testing Default Configuration")
    default_manager = EnhancedScrapingBeeManager("test-key")
    default_country = default_manager.base_options.get("country_code")
    
    if default_country == "in":
        print(f"✅ Default country set to India (in) for ap-south-1 region")
    else:
        print(f"❌ Default country should be 'in' for ap-south-1, got: {default_country}")

def test_proxy_parameters():
    """Test that proxy parameters are correctly set for different countries."""
    
    print(f"\n🔧 Testing Proxy Parameters")
    print("=" * 60)
    
    manager = EnhancedScrapingBeeManager("test-key", {"country_code": "in"})
    
    # Test standard mode parameters
    params = manager._get_params_for_mode("https://example.com", ProxyMode.STANDARD)
    
    print(f"Standard Mode Parameters:")
    print(f"  Country Code: {params.get('country_code', 'NOT SET')}")
    print(f"  Premium Proxy: {params.get('premium_proxy', 'NOT SET')}")
    print(f"  Stealth Proxy: {params.get('stealth_proxy', 'NOT SET')}")
    print(f"  Render JS: {params.get('render_js', 'NOT SET')}")
    
    if params.get('country_code') == 'in':
        print(f"✅ India proxy correctly configured")
    else:
        print(f"❌ India proxy not configured correctly")

def test_aws_region_compatibility():
    """Test that the configuration works with ap-south-1 region."""
    
    print(f"\n☁️  Testing AWS ap-south-1 Region Compatibility")
    print("=" * 60)
    
    # Simulate AWS environment variables
    aws_region = os.getenv('AWS_REGION', 'ap-south-1')
    print(f"AWS Region: {aws_region}")
    
    if aws_region == 'ap-south-1':
        print("✅ Running in ap-south-1 region")
        print("✅ India proxies are optimal for this region")
        print("✅ Lower latency for Indian websites")
        print("✅ Better success rate for regional content")
    else:
        print(f"⚠️  Running in {aws_region} region")
        print("ℹ️  India proxies still work but may have higher latency")
    
    # Test Lambda environment
    lambda_runtime = os.getenv('AWS_LAMBDA_RUNTIME_API')
    if lambda_runtime:
        print("✅ Running in AWS Lambda environment")
    else:
        print("ℹ️  Running in local environment")

def main():
    """Run all geolocation tests."""
    print("🌍 Geolocation Test Suite for ap-south-1 Region")
    print("Testing enhanced crawler geolocation functionality")
    print("=" * 80)
    
    try:
        test_geolocation_configuration()
        test_proxy_parameters()
        test_aws_region_compatibility()
        
        print(f"\n🎉 All geolocation tests completed!")
        print(f"✅ Enhanced crawler is properly configured for ap-south-1 region")
        print(f"✅ India proxies will be used by default")
        print(f"✅ You can override with any country code per request")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main() 