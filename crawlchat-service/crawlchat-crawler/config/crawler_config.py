"""
Crawler Configuration
"""

import os
from typing import Dict, Any

class CrawlerConfig:
    """Configuration for the CrawlChat crawler."""
    
    # ScrapingBee API Configuration
    SCRAPINGBEE_API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
    SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1/"
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
    S3_BUCKET = os.getenv('S3_BUCKET', 'crawlchat-documents')
    
    # Crawler Default Settings
    DEFAULT_TIMEOUT = 30
    DEFAULT_DELAY = 0.05
    DEFAULT_MAX_PAGES = 10
    DEFAULT_MAX_DOCUMENTS = 5
    DEFAULT_MAX_WORKERS = 3
    
    # Proxy Configuration
    DEFAULT_COUNTRY_CODE = 'in'
    DEFAULT_PROXY_MODE = 'premium'
    
    # File Download Settings
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.html', '.htm']
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_scrapingbee_params(cls, **kwargs) -> Dict[str, Any]:
        """Get ScrapingBee parameters with defaults."""
        return {
            'render_js': kwargs.get('render_js', True),
            'block_ads': kwargs.get('block_ads', True),
            'block_resources': kwargs.get('block_resources', True),
            'wait': kwargs.get('wait', None),
            'wait_for': kwargs.get('wait_for', None),
            'wait_browser': kwargs.get('wait_browser', None),
            'window_width': kwargs.get('window_width', 1920),
            'window_height': kwargs.get('window_height', 1080),
            'premium_proxy': kwargs.get('premium_proxy', False),
            'country_code': kwargs.get('country_code', cls.DEFAULT_COUNTRY_CODE),
            'stealth_proxy': kwargs.get('stealth_proxy', False),
            'own_proxy': kwargs.get('own_proxy', None),
            'forward_headers': kwargs.get('forward_headers', False),
            'forward_headers_pure': kwargs.get('forward_headers_pure', False),
            'download_file': kwargs.get('download_file', False),
        }
    
    @classmethod
    def get_crawl_config(cls, **kwargs) -> Dict[str, Any]:
        """Get crawl configuration with defaults."""
        return {
            'max_documents': kwargs.get('max_documents', cls.DEFAULT_MAX_DOCUMENTS),
            'max_pages': kwargs.get('max_pages', cls.DEFAULT_MAX_PAGES),
            'max_workers': kwargs.get('max_workers', cls.DEFAULT_MAX_WORKERS),
            'delay': kwargs.get('delay', cls.DEFAULT_DELAY),
            'total_timeout': kwargs.get('total_timeout', 1800),
            'page_timeout': kwargs.get('page_timeout', 60),
            'request_timeout': kwargs.get('request_timeout', cls.DEFAULT_TIMEOUT),
        } 