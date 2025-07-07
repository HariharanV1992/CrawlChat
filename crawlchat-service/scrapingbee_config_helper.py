#!/usr/bin/env python3
"""
ScrapingBee Configuration Helper
Easy configuration for different proxy scenarios.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ScrapingBeeConfig:
    """Helper class for ScrapingBee configurations."""
    
    @staticmethod
    def basic(api_key: str, country: str = "us") -> Dict[str, Any]:
        """Basic configuration for simple sites."""
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": {
                "render_js": True,
                "country_code": country,
                "premium_proxy": False,
            },
            "use_proxy": True
        }
    
    @staticmethod
    def premium(api_key: str, country: str = "us") -> Dict[str, Any]:
        """Premium configuration for difficult sites."""
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": {
                "premium_proxy": True,
                "country_code": country,
                "render_js": True,
                "wait": 2000,
            },
            "use_proxy": True
        }
    
    @staticmethod
    def stealth(api_key: str, country: str = "us") -> Dict[str, Any]:
        """Stealth configuration for very difficult sites."""
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": {
                "stealth_proxy": True,
                "country_code": country,
                "render_js": True,
                "wait": 5000,
            },
            "use_proxy": True
        }
    
    @staticmethod
    def india(api_key: str) -> Dict[str, Any]:
        """Configuration optimized for Indian websites."""
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": {
                "premium_proxy": True,
                "country_code": "in",
                "render_js": True,
                "wait": 3000,
            },
            "use_proxy": True
        }
    
    @staticmethod
    def own_proxy(api_key: str, proxy_url: str) -> Dict[str, Any]:
        """Configuration using your own proxy."""
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": {
                "own_proxy": proxy_url,
                "render_js": True,
            },
            "use_proxy": True
        }
    
    @staticmethod
    def advanced(api_key: str, country: str = "us", **kwargs) -> Dict[str, Any]:
        """Advanced configuration with custom options."""
        options = {
            "premium_proxy": True,
            "country_code": country,
            "render_js": True,
            "wait": 2000,
            "block_ads": True,
            "block_resources": False,
            "window_width": 1920,
            "window_height": 1080,
            "device": "desktop",
        }
        options.update(kwargs)
        
        return {
            "scrapingbee_api_key": api_key,
            "scrapingbee_options": options,
            "use_proxy": True
        }

def get_config_for_site(site_type: str, api_key: str, **kwargs) -> Dict[str, Any]:
    """Get recommended configuration for different types of sites."""
    
    configs = {
        "simple": ScrapingBeeConfig.basic,
        "news": ScrapingBeeConfig.premium,
        "ecommerce": ScrapingBeeConfig.premium,
        "social": ScrapingBeeConfig.stealth,
        "search": ScrapingBeeConfig.stealth,
        "government": ScrapingBeeConfig.premium,
        "india": ScrapingBeeConfig.india,
    }
    
    if site_type not in configs:
        raise ValueError(f"Unknown site type: {site_type}. Available: {list(configs.keys())}")
    
    return configs[site_type](api_key, **kwargs)

def print_config_examples():
    """Print example configurations."""
    print("🔧 ScrapingBee Configuration Examples")
    print("="*50)
    
    api_key = "YOUR_API_KEY"  # Replace with your key
    
    print("\n1️⃣ Basic Configuration (Simple sites):")
    config = ScrapingBeeConfig.basic(api_key)
    print(f"   {config}")
    
    print("\n2️⃣ Premium Configuration (Difficult sites):")
    config = ScrapingBeeConfig.premium(api_key)
    print(f"   {config}")
    
    print("\n3️⃣ Stealth Configuration (Very difficult sites):")
    config = ScrapingBeeConfig.stealth(api_key)
    print(f"   {config}")
    
    print("\n4️⃣ India Configuration (Indian websites):")
    config = ScrapingBeeConfig.india(api_key)
    print(f"   {config}")
    
    print("\n5️⃣ Advanced Configuration (Custom options):")
    config = ScrapingBeeConfig.advanced(api_key, wait=5000, device="mobile")
    print(f"   {config}")
    
    print("\n6️⃣ Site-specific recommendations:")
    sites = {
        "simple": "Basic websites, blogs",
        "news": "News sites, articles",
        "ecommerce": "Online stores, product pages",
        "social": "Social media, forums",
        "search": "Search engines, directories",
        "government": "Government websites",
        "india": "Indian websites specifically"
    }
    
    for site_type, description in sites.items():
        print(f"   {site_type}: {description}")

if __name__ == "__main__":
    print_config_examples() 