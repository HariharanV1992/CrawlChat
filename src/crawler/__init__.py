"""
Advanced Stock Market Web Crawler Package
A high-performance async web crawler with proxy support and intelligent document detection.
"""

from .advanced_crawler import AdvancedCrawler, CrawlConfig
from .proxy_manager import ProxyManager
from .file_downloader import FileDownloader
from .link_extractor import LinkExtractor
from .settings_manager import SettingsManager
from .utils import (
    get_optimal_thread_count,
    get_optimal_delay,
    load_settings_from_file
)

__version__ = "3.0.0"
__author__ = "Stock Market Crawler Team"

__all__ = [
    'AdvancedCrawler',
    'CrawlConfig',
    'ProxyManager',
    'FileDownloader',
    'LinkExtractor',
    'SettingsManager',
    'get_optimal_thread_count',
    'get_optimal_delay',
    'load_settings_from_file'
] 