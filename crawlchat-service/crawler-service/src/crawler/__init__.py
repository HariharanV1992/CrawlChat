"""
Advanced Stock Market Web Crawler Package
A high-performance async web crawler with proxy support and intelligent document detection.
"""

from .advanced_crawler import AdvancedCrawler
from .file_downloader import FileDownloader
from .link_extractor import LinkExtractor
from .proxy_manager import ProxyManager
from .settings_manager import SettingsManager
from .smart_scrapingbee_manager import SmartScrapingBeeManager
from .s3_document_storage import S3DocumentStorage
from .utils import (
    get_optimal_thread_count,
    get_optimal_delay,
    load_settings_from_file,
    clean_filename,
    get_file_extension,
    is_valid_url,
    normalize_url,
    sanitize_filename
)

__version__ = "3.0.0"
__author__ = "Stock Market Crawler Team"

__all__ = [
    'AdvancedCrawler',
    'FileDownloader',
    'LinkExtractor',
    'ProxyManager',
    'SettingsManager',
    'SmartScrapingBeeManager',
    'S3DocumentStorage',
    'get_optimal_thread_count',
    'get_optimal_delay',
    'load_settings_from_file',
    'clean_filename',
    'get_file_extension',
    'is_valid_url',
    'normalize_url',
    'sanitize_filename'
] 