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
            # Core financial terms
            'stock', 'market', 'financial', 'investor', 'earnings', 'revenue',
            'profit', 'dividend', 'share', 'equity', 'trading', 'quote',
            'annual', 'quarterly', 'report', 'statement', 'filing', 'sec',
            'board', 'governance', 'corporate', 'news', 'announcement',
            'press', 'release', 'update', 'information', 'data', 'analysis',
            
            # Investment and trading terms
            'investment', 'portfolio', 'fund', 'mutual', 'etf', 'bond',
            'derivative', 'option', 'future', 'commodity', 'forex', 'currency',
            'crypto', 'bitcoin', 'blockchain', 'asset', 'wealth', 'capital',
            'return', 'yield', 'growth', 'value', 'momentum', 'volatility',
            
            # Company and business terms
            'company', 'corporation', 'business', 'enterprise', 'firm',
            'sector', 'industry', 'market', 'exchange', 'listing', 'ipo',
            'merger', 'acquisition', 'takeover', 'buyout', 'restructuring',
            
            # Financial metrics and ratios
            'pe', 'pb', 'roe', 'roa', 'debt', 'leverage', 'margin',
            'cashflow', 'ebitda', 'eps', 'book', 'value', 'price',
            'volume', 'marketcap', 'market-cap', 'market_cap',
            
            # Regulatory and compliance
            'regulation', 'compliance', 'audit', 'disclosure', 'transparency',
            'governance', 'policy', 'guideline', 'standard', 'requirement',
            
            # Research and analysis
            'research', 'analyst', 'rating', 'target', 'forecast', 'outlook',
            'projection', 'estimate', 'prediction', 'trend', 'pattern',
            'technical', 'fundamental', 'chart', 'graph', 'indicator',
            
            # Market data and feeds
            'price', 'quote', 'ticker', 'symbol', 'index', 'benchmark',
            'sector', 'industry', 'market', 'exchange', 'listing',
            
            # Content types
            'report', 'presentation', 'webinar', 'conference', 'call',
            'transcript', 'filing', 'document', 'prospectus', 'offering',
            'circular', 'notice', 'bulletin', 'newsletter', 'update',
            
            # News and media
            'news', 'breaking', 'latest', 'update', 'alert', 'flash',
            'headline', 'story', 'article', 'coverage', 'analysis',
            'commentary', 'opinion', 'editorial', 'feature', 'special',
            
            # Economics and macro
            'economics', 'economic', 'gdp', 'inflation', 'unemployment',
            'interest-rate', 'monetary', 'fiscal', 'policy', 'central-bank',
            'federal-reserve', 'fed', 'ecb', 'boj', 'boe', 'rbi',
            'recession', 'growth', 'recovery', 'stimulus', 'austerity',
            'trade', 'tariff', 'import', 'export', 'balance', 'deficit',
            'surplus', 'currency', 'exchange-rate', 'forex', 'commodity',
            'oil', 'gold', 'silver', 'copper', 'agriculture', 'energy',
            
            # Market sentiment and indicators
            'sentiment', 'confidence', 'survey', 'index', 'indicator',
            'vix', 'fear', 'greed', 'momentum', 'trend', 'pattern',
            'support', 'resistance', 'breakout', 'breakdown', 'consolidation',
            'volatility', 'risk', 'uncertainty', 'stability', 'instability'
        ]
        
        # Patterns to exclude (less relevant) - reduced list to be more permissive
        self.exclude_patterns = [
            'login', 'admin', 'private', 'internal', 'test', 'dev',
            'temp', 'cache', 'session', 'cookie', 'tracking', 'advertisement',
            'ad', 'banner', 'social', 'facebook', 'twitter', 'linkedin',
            'youtube', 'instagram', 'subscribe', 'newsletter'
        ]
    
    def is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self.domain
    
    def is_document_link(self, url: str) -> bool:
        """Check if URL points to a document."""
        url_lower = url.lower()
        
        # Check for document extensions (more comprehensive check)
        has_extension = any(ext in url_lower for ext in self.document_extensions)
        
        # Also check for PDF-specific patterns that might not have .pdf extension
        pdf_patterns = [
            '/pdf/', '/document/', '/file/', '/download/',
            'pdf', 'document', 'report', 'filing', 'statement'
        ]
        has_pdf_pattern = any(pattern in url_lower for pattern in pdf_patterns)
        
        # If it has an extension or PDF-like patterns, proceed with further checks
        if not (has_extension or has_pdf_pattern):
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
        
        # Include financial-specific document patterns
        financial_doc_patterns = [
            'annual-report', 'quarterly-report', 'earnings-report', 'financial-report',
            'sec-filing', '10-k', '10-q', '8-k', 'proxy', 'prospectus',
            'financial-statement', 'balance-sheet', 'income-statement', 'cash-flow',
            'investor-presentation', 'analyst-presentation', 'conference-call',
            'press-release', 'announcement', 'disclosure', 'filing', 'report',
            
            # News and economics document patterns
            'news', 'article', 'story', 'headline', 'breaking', 'latest',
            'economics', 'economic', 'macro', 'policy', 'analysis',
            'commentary', 'opinion', 'editorial', 'feature', 'special',
            'market-update', 'trading-update', 'market-analysis', 'economic-report',
            'gdp-report', 'inflation-data', 'employment-report', 'fed-meeting',
            'central-bank', 'monetary-policy', 'fiscal-policy', 'trade-data'
        ]
        
        # If URL contains financial document patterns, consider it a document
        if any(pattern in url_lower for pattern in financial_doc_patterns):
            return True
        
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
        
        # Be more permissive - include most links that aren't explicitly excluded
        # This helps find more child pages to crawl
        return True
    
    def extract_links(self, soup: BeautifulSoup, base_url: str, visited_urls: set) -> Tuple[List[str], List[str]]:
        """Extract both page links and document links from HTML content."""
        page_links = []
        document_links = []
        
        logger.info(f"Extracting links from {base_url}")
        
        # 1. Extract from <a> tags (standard links)
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)
            
            # Clean and validate URL
            full_url = self._clean_url(full_url)
            if not full_url:
                continue
                
            if self.is_same_domain(full_url) and full_url not in visited_urls:
                if self.is_document_link(full_url):
                    document_links.append(full_url)
                elif self.is_relevant_link(full_url, link_text):
                    page_links.append(full_url)
        
        # 2. Extract from buttons with onclick handlers
        for button in soup.find_all(['button', 'div', 'span'], onclick=True):
            onclick = button.get('onclick', '')
            extracted_urls = self._extract_urls_from_javascript(onclick, base_url)
            
            for url in extracted_urls:
                url = self._clean_url(url)
                if url and self.is_same_domain(url) and url not in visited_urls:
                    if self.is_document_link(url):
                        document_links.append(url)
                    elif self.is_relevant_link(url):
                        page_links.append(url)
        
        # 3. Extract from data attributes and other sources
        for element in soup.find_all(attrs={'data-url': True}):
            url = element.get('data-url')
            url = self._clean_url(urljoin(base_url, url))
            if url and self.is_same_domain(url) and url not in visited_urls:
                if self.is_document_link(url):
                    document_links.append(url)
                elif self.is_relevant_link(url):
                    page_links.append(url)
        
        # 4. Extract from script tags that might contain URLs
        for script in soup.find_all('script'):
            if script.string:
                extracted_urls = self._extract_urls_from_javascript(script.string, base_url)
                for url in extracted_urls:
                    url = self._clean_url(url)
                    if url and self.is_same_domain(url) and url not in visited_urls:
                        if self.is_document_link(url):
                            document_links.append(url)
                        elif self.is_relevant_link(url):
                            page_links.append(url)
        
        # Remove duplicates and sort by relevance
        page_links = list(set(page_links))
        document_links = list(set(document_links))
        
        # Prioritize PDF documents
        pdf_links = [url for url in document_links if url.lower().endswith('.pdf')]
        other_doc_links = [url for url in document_links if not url.lower().endswith('.pdf')]
        document_links = pdf_links + other_doc_links
        
        # Log summary
        logger.info(f"Link extraction summary for {base_url}:")
        logger.info(f"  - Page links found: {len(page_links)}")
        logger.info(f"  - Document links found: {len(document_links)}")
        logger.info(f"  - Sample page links: {page_links[:3]}")
        logger.info(f"  - Sample document links: {document_links[:3]}")
        
        # Log PDF links specifically
        pdf_links = [url for url in document_links if url.lower().endswith('.pdf')]
        if pdf_links:
            logger.info(f"  - PDF links found: {pdf_links}")
        
        return page_links, document_links
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL, removing malformed parts."""
        if not url:
            return None
            
        # Remove common malformed parts
        url = url.strip()
        
        # Remove JavaScript code that might be appended
        if ');' in url:
            url = url.split(');')[0]
        
        # Remove any trailing JavaScript
        if 'javascript:' in url.lower():
            return None
            
        # Remove any trailing HTML entities or malformed parts
        if '&amp;' in url:
            url = url.split('&amp;')[0]
        
        # Ensure URL starts with http/https
        if not url.startswith(('http://', 'https://')):
            return None
            
        # Remove any query parameters that might be malformed
        if '?' in url:
            base_url, query = url.split('?', 1)
            # Keep only valid query parameters
            valid_params = []
            for param in query.split('&'):
                if '=' in param and not param.startswith('javascript'):
                    valid_params.append(param)
            if valid_params:
                url = base_url + '?' + '&'.join(valid_params)
            else:
                url = base_url
        
        # Remove any trailing slashes from non-directory URLs
        if url.endswith('/') and not url.endswith('.pdf'):
            url = url.rstrip('/')
        
        return url
    
    def _extract_urls_from_javascript(self, onclick_code: str, base_url: str) -> List[str]:
        """Extract URLs from onclick handlers and other JavaScript code."""
        urls = []
        # Look for URLs in onclick handlers (including PDF patterns)
        urls.extend(re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', onclick_code, re.IGNORECASE))
        # Also look for PDF patterns without extensions
        urls.extend(re.findall(r'["\']([^"\']*(?:pdf|document|report|filing|statement)[^"\']*)["\']', onclick_code, re.IGNORECASE))
        # Look for URLs in data attributes
        urls.extend(re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', onclick_code, re.IGNORECASE))
        # Also look for PDF patterns without extensions
        urls.extend(re.findall(r'["\']([^"\']*(?:pdf|document|report|filing|statement)[^"\']*)["\']', onclick_code, re.IGNORECASE))
        # Look for URLs in meta tags
        urls.extend(re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', onclick_code, re.IGNORECASE))
        # Also look for PDF patterns without extensions
        urls.extend(re.findall(r'["\']([^"\']*(?:pdf|document|report|filing|statement)[^"\']*)["\']', onclick_code, re.IGNORECASE))
        # Look for URLs in JSON-LD structured data
        urls.extend(re.findall(r'["\']([^"\']*\.(?:pdf|doc|docx|xlsx|xls|ppt|pptx|csv|json))["\']', onclick_code, re.IGNORECASE))
        # Also look for PDF patterns without extensions
        urls.extend(re.findall(r'["\']([^"\']*(?:pdf|document|report|filing|statement)[^"\']*)["\']', onclick_code, re.IGNORECASE))
        
        # Normalize URLs and remove duplicates
        normalized_urls = list(set([urljoin(base_url, u) for u in urls]))
        return normalized_urls 