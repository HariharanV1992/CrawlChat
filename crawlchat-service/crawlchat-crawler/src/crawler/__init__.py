"""
Advanced Stock Market Web Crawler Package
A high-performance async web crawler with proxy support and intelligent document detection.
"""

from crawler.advanced_crawler import AdvancedCrawler
from crawler.file_downloader import FileDownloader
from crawler.link_extractor import LinkExtractor
from crawler.proxy_manager import ProxyManager
from crawler.settings_manager import SettingsManager
from crawler.smart_scrapingbee_manager import SmartScrapingBeeManager
from crawler.utils import (
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
    'get_optimal_thread_count',
    'get_optimal_delay',
    'load_settings_from_file',
    'clean_filename',
    'get_file_extension',
    'is_valid_url',
    'normalize_url',
    'sanitize_filename'
] 