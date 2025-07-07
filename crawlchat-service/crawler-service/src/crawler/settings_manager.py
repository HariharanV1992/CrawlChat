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
            'timeout': 30,
            'proxy_api_key': "",
            'proxy_method': "api_endpoint",  # "api_endpoint" or "proxy_port"
            'min_file_size': 1024,
            'output_dir': "crawled_data",
            'single_page_mode': False,
            
            # Performance settings
            'connection_limit': 100,
            'tcp_connector_limit': 50,
            'keepalive_timeout': 30,
            'enable_compression': True,
            
            # Timeout settings
            'total_timeout': 1800,  # Total crawl timeout in seconds (30 minutes)
            'page_timeout': 60,     # Timeout per page in seconds
            'request_timeout': 30,  # Timeout per request in seconds
            
            # Early termination settings
            'max_pages_without_documents': 20,  # Stop if no documents found after this many pages
            
            # Content filtering
            'relevant_keywords': [
                'stock', 'market', 'financial', 'investor', 'earnings', 'revenue',
                'profit', 'dividend', 'share', 'equity', 'trading', 'quote',
                'annual', 'quarterly', 'report', 'statement', 'filing', 'sec',
                'board', 'governance', 'corporate', 'news', 'announcement'
            ],
            'exclude_patterns': [
                'login', 'admin', 'private', 'internal', 'test', 'dev',
                'temp', 'cache', 'session', 'cookie', 'tracking', 'advertisement',
                'ad', 'banner', 'social', 'facebook', 'twitter', 'linkedin',
                'youtube', 'instagram', 'subscribe', 'newsletter', 'contact',
                'about', 'careers', 'jobs', 'support', 'help', 'faq'
            ],
            'document_extensions': ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', '.txt', '.csv'],
            
            # ScrapingBee specific settings
            'scrapingbee_api_key': "",
            'scrapingbee_options': {},  # e.g. {"premium_proxy": True, "country_code": "us", ...}
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