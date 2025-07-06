"""
Settings manager for the enhanced stock market crawler.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .utils import load_settings_from_file, get_optimal_thread_count, get_optimal_delay

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages all settings and configuration for the crawler."""
    
    def __init__(self, settings_file="stock_market_settings.json"):
        self.settings_file = settings_file
        self.settings = load_settings_from_file(settings_file)
        
    def get_crawler_settings(self, base_url: str, **kwargs) -> Dict[str, Any]:
        """Get crawler settings with defaults and overrides."""
        # Try new format first, then fall back to old format
        crawler_settings = self.settings.get('crawler_settings', self.settings.get('crawler', {}))
        
        # Default settings
        defaults = {
            'max_pages': 5,
            'delay': 2,
            'min_year': 2015,
            'max_year': 2025,
            'max_workers': 3,
            'use_selenium': True,
            'max_documents': 10,
            'min_file_size_bytes': 1000,
            'selenium_timeout': 30,
            'selenium_wait_time': 3,
            'max_retries': 3,
            'retry_delay': 5
        }
        
        # Override with file settings
        for key, value in crawler_settings.items():
            if key in defaults:
                defaults[key] = value
        
        # Override with provided kwargs
        for key, value in kwargs.items():
            if key in defaults:
                defaults[key] = value
        
        # Auto-detect optimal settings if not provided
        if 'delay' not in kwargs:
            defaults['delay'] = get_optimal_delay(base_url)
        
        if 'max_workers' not in kwargs:
            defaults['max_workers'] = get_optimal_thread_count()
        
        return defaults
    
    def get_proxy_settings(self, **kwargs) -> Dict[str, Any]:
        """Get proxy settings."""
        # Try new format first, then fall back to old format
        proxy_settings = self.settings.get('proxy_settings', self.settings.get('proxy', {}))
        
        defaults = {
            'use_proxy': True,
            'api_key': "087071cd4dfe9cad8630b1d893552849",
            'scraperapi_base': "http://api.scraperapi.com/",
            'timeout': 30,
            'country_code': 'us',
            'premium': True,
            'bypass': 'cloudflare'
        }
        
        # Override with file settings
        for key, value in proxy_settings.items():
            if key in defaults:
                defaults[key] = value
        
        # Override with provided kwargs
        for key, value in kwargs.items():
            if key in defaults:
                defaults[key] = value
        
        return defaults
    
    def get_keyword_settings(self, **kwargs) -> Dict[str, Any]:
        """Get keyword filtering settings."""
        # Try new format first, then fall back to old format
        keyword_settings = self.settings.get('keyword_settings', self.settings.get('keywords', {}))
        
        defaults = {
            'url_keywords': [],
            'content_keywords': [],
            'snippet_keywords': []
        }
        
        # Override with file settings
        for key, value in keyword_settings.items():
            if key in defaults:
                defaults[key] = value
        
        # Override with provided kwargs
        for key, value in kwargs.items():
            if key in defaults:
                defaults[key] = value
        
        return defaults
    
    def save_settings(self, settings: Dict[str, Any], filename: Optional[str] = None):
        """Save settings to file."""
        if filename is None:
            filename = self.settings_file
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logger.info(f"Settings saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def update_setting(self, section: str, key: str, value: Any):
        """Update a specific setting."""
        if section not in self.settings:
            self.settings[section] = {}
        
        self.settings[section][key] = value
        self.save_settings(self.settings)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy() 