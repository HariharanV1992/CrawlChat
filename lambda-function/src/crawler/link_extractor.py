"""
Link extraction logic for the enhanced stock market crawler.
"""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from typing import List, Tuple
import re

logger = logging.getLogger(__name__)

class LinkExtractor:
    """Extracts and normalizes links from HTML content."""
    def __init__(self, domain: str):
        self.domain = domain
        self.document_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', '.csv', '.json']
        
        # Keywords that indicate relevant financial content
        self.relevant_keywords = [
            'stock', 'market', 'financial', 'investor', 'earnings', 'revenue',
            'profit', 'dividend', 'share', 'equity', 'trading', 'quote',
            'annual', 'quarterly', 'report', 'statement', 'filing', 'sec',
            'board', 'governance', 'corporate', 'news', 'announcement',
            'press', 'release', 'update', 'information', 'data', 'analysis'
        ]
        
        # Patterns to exclude (less relevant)
        self.exclude_patterns = [
            'login', 'admin', 'private', 'internal', 'test', 'dev',
            'temp', 'cache', 'session', 'cookie', 'tracking', 'advertisement',
            'ad', 'banner', 'social', 'facebook', 'twitter', 'linkedin',
            'youtube', 'instagram', 'subscribe', 'newsletter', 'contact',
            'about', 'careers', 'jobs', 'support', 'help', 'faq'
        ]
    
    def is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self.domain
    
    def is_document_link(self, url: str) -> bool:
        """Check if URL points to a document."""
        # Check for document extensions
        if not any(ext in url.lower() for ext in self.document_extensions):
            return False
        
        # Exclude common non-document JSON files and API responses
        json_exclude_patterns = [
            'customresponse.json', 'customResponse.json', 'api.json', 'config.json',
            'settings.json', 'data.json', 'response.json', 'result.json',
            'status.json', 'health.json', 'metrics.json', 'stats.json',
            'customresponse', 'customResponse', 'api/', 'config/', 'settings/',
            'data/', 'response/', 'result/', 'status/', 'health/', 'metrics/',
            'stats/', 'endpoint', 'service', 'rest', 'graphql', 'swagger',
            'openapi', 'docs', 'documentation', 'schema', 'spec'
        ]
        
        url_lower = url.lower()
        for pattern in json_exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Additional checks for API-like patterns
        api_patterns = ['/api/', '/v1/', '/v2/', '/v3/', '/rest/', '/graphql/']
        if any(pattern in url_lower for pattern in api_patterns):
            return False
        
        # Check if URL contains query parameters (likely API call)
        if '?' in url and any(param in url_lower for param in ['api_key', 'token', 'auth', 'callback']):
            return False
        
        return True
    
    def is_relevant_link(self, url: str, link_text: str = "") -> bool:
        """Check if a link is relevant to financial/stock market content."""
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        # Check for exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in url_lower or pattern in text_lower:
                return False
        
        # Check for relevant keywords
        for keyword in self.relevant_keywords:
            if keyword in url_lower or keyword in text_lower:
                return True
        
        # If no relevant keywords found, still include if it's not explicitly excluded
        return True
    
    def extract_links(self, soup: BeautifulSoup, base_url: str, visited_urls: set) -> Tuple[List[str], List[str]]:
        """Extract both page links and document links from HTML content."""
        page_links = []
        document_links = []
        
        # 1. Extract from <a> tags (standard links)
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)
            
            if self.is_same_domain(full_url) and full_url not in visited_urls:
                if self.is_document_link(full_url):
                    document_links.append(full_url)
                elif self.is_relevant_link(full_url, link_text):
                    page_links.append(full_url)
        
        # 2. Extract from buttons with onclick handlers
        for button in soup.find_all(['button', 'div', 'span'], onclick=True):
            onclick = button.get('onclick', '')
            if onclick:
                # Extract URLs from onclick handlers
                urls = re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', onclick, re.IGNORECASE)
                for url_match in urls:
                    full_url = urljoin(base_url, url_match)
                    if self.is_same_domain(full_url) and full_url not in visited_urls:
                        document_links.append(full_url)
        
        # 3. Extract from data attributes
        for element in soup.find_all(attrs={'data-url': True}):
            data_url = element.get('data-url')
            if data_url:
                full_url = urljoin(base_url, data_url)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    if self.is_document_link(full_url):
                        document_links.append(full_url)
                    elif self.is_relevant_link(full_url):
                        page_links.append(full_url)
        
        # 4. Extract from data-href attributes
        for element in soup.find_all(attrs={'data-href': True}):
            data_href = element.get('data-href')
            if data_href:
                full_url = urljoin(base_url, data_href)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    if self.is_document_link(full_url):
                        document_links.append(full_url)
                    elif self.is_relevant_link(full_url):
                        page_links.append(full_url)
        
        # 5. Extract from data-pdf attributes
        for element in soup.find_all(attrs={'data-pdf': True}):
            data_pdf = element.get('data-pdf')
            if data_pdf:
                full_url = urljoin(base_url, data_pdf)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    document_links.append(full_url)
        
        # 6. Extract from iframe sources
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            full_url = urljoin(base_url, src)
            if self.is_same_domain(full_url) and full_url not in visited_urls:
                if self.is_document_link(full_url):
                    document_links.append(full_url)
                elif self.is_relevant_link(full_url):
                    page_links.append(full_url)
        
        # 7. Extract from object/embed tags
        for obj in soup.find_all(['object', 'embed'], data=True):
            data = obj.get('data')
            if data:
                full_url = urljoin(base_url, data)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    if self.is_document_link(full_url):
                        document_links.append(full_url)
                    elif self.is_relevant_link(full_url):
                        page_links.append(full_url)
        
        # 8. Extract from script tags (JavaScript variables)
        for script in soup.find_all('script'):
            if script.string:
                # Find document URLs in JavaScript
                js_urls = re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', script.string, re.IGNORECASE)
                for js_url in js_urls:
                    full_url = urljoin(base_url, js_url)
                    if self.is_same_domain(full_url) and full_url not in visited_urls:
                        document_links.append(full_url)
        
        # 9. Extract from meta tags (for PDF viewers)
        for meta in soup.find_all('meta', attrs={'name': 'pdf-url'}):
            content = meta.get('content')
            if content:
                full_url = urljoin(base_url, content)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    document_links.append(full_url)
        
        # 10. Extract from JSON-LD structured data
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                try:
                    # Look for URLs in JSON-LD content
                    json_urls = re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', script.string, re.IGNORECASE)
                    for json_url in json_urls:
                        full_url = urljoin(base_url, json_url)
                        if self.is_same_domain(full_url) and full_url not in visited_urls:
                            document_links.append(full_url)
                except:
                    continue
        
        # 11. Extract from common modern patterns
        # Look for elements with download attributes
        for element in soup.find_all(attrs={'download': True}):
            href = element.get('href')
            if href:
                full_url = urljoin(base_url, href)
                if self.is_same_domain(full_url) and full_url not in visited_urls:
                    if self.is_document_link(full_url):
                        document_links.append(full_url)
                    elif self.is_relevant_link(full_url):
                        page_links.append(full_url)
        
        # 12. Extract from form actions (for file upload/download forms)
        for form in soup.find_all('form', action=True):
            action = form['action']
            full_url = urljoin(base_url, action)
            if self.is_same_domain(full_url) and full_url not in visited_urls:
                if self.is_document_link(full_url):
                    document_links.append(full_url)
                elif self.is_relevant_link(full_url):
                    page_links.append(full_url)
        
        # Remove duplicates and limit the number of links to avoid overwhelming
        page_links = list(set(page_links))[:50]  # Limit to 50 most relevant page links
        document_links = list(set(document_links))
        
        logger.info(f"Found {len(page_links)} page links and {len(document_links)} document links on {base_url}")
        return page_links, document_links 