"""
Utility functions for the enhanced stock market crawler.
"""

import json
import multiprocessing
import re
import hashlib
import random
from pathlib import Path
from typing import Dict, Any, List
import logging
import os
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

def clean_filename(filename: str) -> str:
    """Clean filename by removing invalid characters and limiting length."""
    # Remove invalid characters for filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remove leading/trailing underscores and dots
    cleaned = cleaned.strip('_.')
    # Limit length
    if len(cleaned) > 200:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:200-len(ext)] + ext
    return cleaned

def get_file_extension(url: str) -> str:
    """Extract file extension from URL."""
    parsed = urlparse(url)
    path = parsed.path
    if '.' in path:
        return os.path.splitext(path)[1].lower()
    return ''

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalize URL by resolving relative URLs and removing fragments."""
    try:
        if base_url:
            url = urljoin(base_url, url)
        parsed = urlparse(url)
        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    except:
        return url

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_.')
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'unnamed_file'
    return sanitized

def load_settings_from_file(settings_file="/tmp/stock_market_settings.json"):
    """Load settings and keywords from JSON file"""
    try:
        # Try multiple possible locations for the settings file
        possible_paths = [
            Path(settings_file),  # Current directory
            Path(__file__).parent.parent / settings_file,  # stock_market_crawler directory
            Path.cwd() / settings_file,  # Current working directory
        ]
        
        for settings_path in possible_paths:
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Loaded settings from {settings_path}")
                return settings
        
        logger.warning(f"Settings file {settings_file} not found in any location, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Error loading settings file: {e}")
        return {}

def get_default_keywords(settings, keyword_type):
    """Get default keywords from settings file based on type"""
    if not settings:
        return []
    
    # Map keyword types to settings keys
    keyword_mapping = {
        'url': 'url_patterns',
        'content': 'keywords',
        'snippet': 'url_patterns'  # Use URL patterns for snippets too
    }
    
    settings_key = keyword_mapping.get(keyword_type)
    if not settings_key or settings_key not in settings:
        return []
    
    # Flatten all keyword lists from the specified section
    keywords = []
    for category, keyword_list in settings[settings_key].items():
        if isinstance(keyword_list, list):
            keywords.extend(keyword_list)
    
    return keywords

def get_optimal_thread_count():
    """Automatically determine optimal thread count based on system resources"""
    cpu_count = multiprocessing.cpu_count()
    # Use 2x CPU cores for I/O bound tasks like web crawling
    optimal_threads = min(cpu_count * 2, 16)  # Cap at 16 threads
    return optimal_threads

def get_optimal_delay(url):
    """Determine optimal delay based on domain and response time"""
    # Faster delays for local/development servers
    if 'localhost' in url or '127.0.0.1' in url:
        return 0.5
    # Moderate delays for most sites
    elif any(domain in url for domain in ['gov.in', 'nic.in', 'org']):
        return 1
    # Conservative delays for commercial sites
    else:
        return 2

def get_url_hash(url):
    """Generate hash for URL"""
    return hashlib.md5(url.encode()).hexdigest()

def rotate_user_agent():
    """Rotate user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    return random.choice(user_agents) 