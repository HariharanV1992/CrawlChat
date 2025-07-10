# ScrapingBee Parameters Documentation

This document describes all the ScrapingBee parameters that have been implemented in the CrawlChat crawler service.

## Overview

The CrawlChat crawler uses the official ScrapingBee Python client to provide advanced web scraping capabilities. All parameters are passed through to the ScrapingBee API to control the scraping behavior.

## Core Parameters

### Basic Crawling
- `url` (required): The target URL to crawl
- `render_js` (default: `False`): Whether to render JavaScript on the page
- `wait` (default: `0`): Time to wait after page load (in milliseconds)
- `wait_between` (default: `0`): Time to wait between requests (in milliseconds)

### Content Blocking
- `block_ads` (default: `False`): Block ad-related content
- `block_resources` (default: `False`): Block resource loading (images, CSS, etc.)

### File Downloads
- `download_file` (default: `False`): Download file content (images, PDFs, etc.) instead of HTML (recommended with render_js=False)

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com/document.pdf",
    render_js=False,
    download_file=True
)
```

**Benefits:**
- Download binary files (images, PDFs, documents, archives)
- Automatic file type detection from URL and content
- File size validation (2MB limit)
- Returns binary content for non-text files
- Proper content-type headers

**Supported File Types:**
- **Images**: JPEG, PNG, GIF, BMP, TIFF, WebP, SVG
- **Documents**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- **Text**: TXT, CSV, JSON, XML
- **Archives**: ZIP, RAR, 7Z, TAR, GZ

**File Size Limits:**
- Maximum file size: 2MB per request
- Automatic validation and error handling
- Returns 413 status code for oversized files

## Viewport and Display

### Window Dimensions
- `window_width` (default: `1920`): Browser viewport width in pixels
- `window_height` (default: `1080`): Browser viewport height in pixels

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=True,
    window_width=1366,
    window_height=768
)
```

**Benefits:**
- Control the viewport size for responsive websites
- Ensure consistent rendering across different screen sizes
- Useful for mobile-responsive testing

## Proxy Configuration

### Premium Proxy
- `premium_proxy` (default: `False`): Use premium proxies for better success rates

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    premium_proxy=True
)
```

**Benefits:**
- Higher success rates for difficult sites
- Better IP rotation
- Costs 25 credits per request

### Stealth Proxy
- `stealth_proxy` (default: `False`): Use stealth proxies for hardest-to-scrape sites
- **Requires:** `render_js=True`

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=True,
    stealth_proxy=True
)
```

**Benefits:**
- Highest success rates for anti-bot protected sites
- Advanced fingerprinting evasion
- Costs 75 credits per request

### Custom Proxy
- `own_proxy` (default: `None`): Use your own proxy server

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    own_proxy="http://username:password@proxy.example.com:8080"
)
```

**Format:** `protocol://username:password@host:port`

**Benefits:**
- Use your own proxy infrastructure
- No additional ScrapingBee costs
- Full control over proxy selection

## Geolocation

### Country Code
- `country_code` (default: `None`): Target country for geolocation

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    country_code="US"
)
```

**Supported Countries:**
- `US` - United States
- `GB` - United Kingdom
- `DE` - Germany
- `FR` - France
- `CA` - Canada
- And many more...

**Benefits:**
- Access country-specific content
- Bypass geo-restrictions
- Test localized versions of websites

## Header Forwarding

### Standard Header Forwarding
- `forward_headers` (default: `False`): Forward custom headers to target website

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    forward_headers=True
)
```

**Benefits:**
- Send custom headers like Accept-Language, User-Agent
- Python client automatically handles Spb- prefix
- Useful for language preferences and custom user agents

### Pure Header Forwarding
- `forward_headers_pure` (default: `False`): Forward headers without ScrapingBee's automatic headers
- **Requires:** `render_js=False`

**Usage Example:**
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=False,
    forward_headers=True,
    forward_headers_pure=True
)
```

**Benefits:**
- Send only your custom headers
- No automatic headers from ScrapingBee
- Useful for precise header control

## Parameter Constraints

### Required Combinations
1. `stealth_proxy=True` requires `render_js=True`
2. `forward_headers_pure=True` requires `render_js=False`
3. `download_file=True` works best with `render_js=False`

### Validation
The crawler automatically validates these constraints and throws `ValueError` if violated.

## Cost Implications

| Parameter | Cost Multiplier | Notes |
|-----------|----------------|-------|
| Basic request | 1 credit | Standard scraping |
| `premium_proxy=True` | 25 credits | Better success rates |
| `stealth_proxy=True` | 75 credits | Highest success rates |
| `render_js=True` | 1 credit | JavaScript rendering |
| `download_file=True` | 1 credit | File downloads |
| `own_proxy` | 1 credit | No additional cost |

## Best Practices

### For Simple Sites
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=False,
    wait=1000
)
```

### For JavaScript-Heavy Sites
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=True,
    wait=2000,
    window_width=1920,
    window_height=1080
)
```

### For Difficult Sites
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=True,
    premium_proxy=True,
    wait=3000,
    block_ads=True
)
```

### For Anti-Bot Protected Sites
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=True,
    stealth_proxy=True,
    wait=5000,
    country_code="US"
)
```

### For Language-Specific Content
```python
result = crawler.crawl_url(
    url="https://example.com",
    render_js=False,
    forward_headers=True,
    forward_headers_pure=True
)
```

### For File Downloads
```python
result = crawler.crawl_url(
    url="https://example.com/document.pdf",
    render_js=False,
    download_file=True
)
```

## Testing

Use the provided test scripts to verify parameter functionality:

- `test_viewport_dimensions.py` - Test window width/height
- `test_premium_proxy.py` - Test premium proxy
- `test_country_code.py` - Test geolocation
- `test_stealth_proxy.py` - Test stealth proxy
- `test_own_proxy.py` - Test custom proxy
- `test_forward_headers.py` - Test header forwarding
- `test_file_downloads.py` - Test file downloads

## Error Handling

The crawler includes comprehensive error handling:

- **Parameter validation**: Automatic constraint checking
- **API errors**: Proper error messages for 401, 429, etc.
- **Network errors**: Retry logic and timeout handling
- **Content validation**: Checks for valid responses
- **File size validation**: 2MB limit enforcement

## Integration

All parameters are available through:

1. **API Endpoints**: `/api/v1/crawler/crawl`
2. **Python Service**: `crawler_service.crawl_url()`
3. **Direct Crawler**: `AdvancedCrawler.crawl_url()`

## Monitoring

The crawler provides usage statistics:

```python
stats = crawler.get_usage_stats()
print(f"Requests: {stats['requests']}")
print(f"Successes: {stats['successes']}")
print(f"Failures: {stats['failures']}")
```

## Support

For issues with specific parameters:

1. Check the test scripts for working examples
2. Verify parameter constraints are met
3. Check ScrapingBee API documentation
4. Review error messages for specific guidance 