# CrawlChat Crawler System Documentation

## Overview

The CrawlChat crawler system is a comprehensive web scraping solution that supports multiple data types including HTML, PDF, images, and screenshots. It uses ScrapingBee as the primary scraping service with fallback mechanisms for different scenarios.

## Architecture

### Components

1. **Lambda Crawl Worker** (`lambda_crawl_worker.py`)
   - Processes crawl tasks from SQS queue
   - Runs in AWS Lambda environment
   - Handles task execution and error recovery

2. **Crawler Service** (`common/src/services/crawler_service.py`)
   - Manages crawl tasks and their lifecycle
   - Integrates with MongoDB for task storage
   - Handles S3 uploads and document processing

3. **Advanced Crawler** (`lambda-service/src/crawler/advanced_crawler.py`)
   - Core scraping logic using ScrapingBee
   - Supports multiple file types and formats
   - Implements retry and fallback mechanisms

4. **Storage Services**
   - `unified_storage_service.py`: Handles S3 uploads for crawled content
   - `storage_service.py`: Provides file access and management
   - `document_service.py`: Processes and manages documents

## ScrapingBee Configuration

### API Key Setup

```bash
# Set your ScrapingBee API key
export SCRAPINGBEE_API_KEY="your-api-key-here"
```

### Basic Usage

The crawler uses ScrapingBee with the following default configuration:

```python
# Default ScrapingBee parameters
{
    "render_js": True,           # Enable JavaScript rendering
    "premium_proxy": False,      # Use standard proxies initially
    "stealth_proxy": False,      # Use advanced proxies as fallback
    "block_resources": True,     # Block images/CSS for speed
    "timeout": 140000,           # 140 second timeout
    "wait": 2000,               # 2 second wait after page load
    "wait_browser": "domcontentloaded"
}
```

### Progressive Proxy Strategy

The crawler implements a progressive proxy strategy:

1. **Standard Mode** (5 credits per request)
   - `render_js: True`
   - `premium_proxy: False`
   - `stealth_proxy: False`

2. **Premium Proxy Mode** (25 credits per request)
   - `render_js: True`
   - `premium_proxy: True`
   - `stealth_proxy: False`

3. **Stealth Proxy Mode** (75 credits per request)
   - `render_js: True`
   - `premium_proxy: False`
   - `stealth_proxy: True`

### File Type Support

The crawler supports multiple file types:

#### HTML Content
- **Default**: Full HTML with JavaScript rendering
- **Fallback**: Static HTML without JavaScript
- **Processing**: HTML cleaning and text extraction

#### PDF Documents
- **Download**: Direct PDF download
- **Processing**: AWS Textract for text extraction
- **Storage**: S3 with metadata

#### Images
- **Types**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **Download**: Direct image download
- **Processing**: Optional OCR with Textract
- **Storage**: S3 with content type metadata

#### Screenshots
- **Capture**: Full page screenshots
- **Selector**: Specific element screenshots
- **Format**: PNG with metadata
- **Storage**: S3 with timestamp

### Advanced Configuration

#### JavaScript Scenarios

For interactive websites, use JavaScript scenarios:

```python
js_scenario = {
    "instructions": [
        {"wait": 2000},                    # Wait 2 seconds
        {"click": "#load-more-button"},    # Click load more
        {"wait_for": ".content-loaded"},   # Wait for content
        {"scroll_y": 1000},                # Scroll down
        {"wait": 1000}                     # Wait for load
    ]
}
```

#### Custom Headers

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}
```

#### Geolocation

```python
# Use proxies from specific countries
country_code = "us"  # United States
country_code = "in"  # India
country_code = "gb"  # United Kingdom
```

## Deployment and Configuration

### Environment Variables

```bash
# Required
SCRAPINGBEE_API_KEY=your-api-key
MONGODB_URI=your-mongodb-connection-string
S3_BUCKET=your-s3-bucket-name
AWS_REGION=your-aws-region

# Optional
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
OPENAI_API_KEY=your-openai-api-key
```

### Lambda Configuration

```yaml
# CloudFormation template (infra/crawlchat-crawl-worker.yml)
AWSTemplateFormatVersion: '2010-09-09'
Description: CrawlChat SQS-based Crawler Infrastructure

Parameters:
  LambdaImageUri:
    Type: String
    Description: ECR image URI for the Lambda worker

Resources:
  CrawlChatCrawlQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: crawlchat-crawl-tasks

  CrawlChatCrawlWorkerFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: crawlchat-crawl-worker
      PackageType: Image
      Timeout: 900
      MemorySize: 1024
      Environment:
        Variables:
          CRAWLCHAT_SQS_QUEUE: !Ref CrawlChatCrawlQueue
          AWS_REGION: !Ref AWS::Region
```

### IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            "Resource": "arn:aws:sqs:*:*:crawlchat-crawl-tasks"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket",
                "arn:aws:s3:::your-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

## Troubleshooting

### Common Issues

#### 1. "get_storage_service is not defined" Error

**Problem**: Missing import in crawler service
**Solution**: Ensure the import is added:

```python
from common.src.services.storage_service import get_storage_service
```

#### 2. HTML Content Instead of Rendered Page

**Problem**: JavaScript not being rendered properly
**Solution**: Check ScrapingBee configuration:

```python
# Ensure these parameters are set
{
    "render_js": True,
    "wait": 5000,  # Increase wait time
    "wait_browser": "networkidle2",
    "timeout": 140000
}
```

#### 3. Crawler Fails with 403/429 Errors

**Problem**: Website blocking requests
**Solution**: Use progressive proxy strategy:

```python
# Try standard mode first
if standard_mode_fails:
    # Switch to premium proxy
    params["premium_proxy"] = True
    
if premium_proxy_fails:
    # Switch to stealth proxy
    params["stealth_proxy"] = True
    params["premium_proxy"] = False
```

#### 4. Lambda Timeout Issues

**Problem**: Crawl tasks taking too long
**Solution**: Optimize configuration:

```python
# Reduce scope
max_pages = 50
max_documents = 25
timeout = 60000  # 60 seconds

# Use faster settings
block_resources = True
render_js = False  # For static content
```

### Debugging

#### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add to crawler service
logger.debug(f"ScrapingBee response: {response.status_code}")
logger.debug(f"Response headers: {response.headers}")
```

#### Check ScrapingBee Credits

```python
import requests

def check_credits(api_key):
    response = requests.get(
        "https://app.scrapingbee.com/api/v1/usage",
        params={"api_key": api_key}
    )
    return response.json()

# Usage
credits = check_credits("your-api-key")
print(f"Used: {credits['used_api_credit']}")
print(f"Max: {credits['max_api_credit']}")
```

#### Monitor SQS Queue

```bash
# Check queue depth
aws sqs get-queue-attributes \
    --queue-url https://sqs.region.amazonaws.com/account/crawlchat-crawl-tasks \
    --attribute-names All

# Check dead letter queue
aws sqs get-queue-attributes \
    --queue-url https://sqs.region.amazonaws.com/account/crawlchat-crawl-tasks-dlq \
    --attribute-names All
```

## Best Practices

### 1. Rate Limiting

```python
# Implement delays between requests
import asyncio

async def crawl_with_delay(urls, delay=2.0):
    for url in urls:
        await crawl_url(url)
        await asyncio.sleep(delay)
```

### 2. Error Handling

```python
# Implement retry logic
async def crawl_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await crawl_url(url)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Resource Management

```python
# Clean up temporary files
import tempfile
import shutil

async def process_with_cleanup():
    temp_dir = tempfile.mkdtemp()
    try:
        # Process files
        await process_files(temp_dir)
    finally:
        shutil.rmtree(temp_dir)
```

### 4. Monitoring

```python
# Track crawl metrics
class CrawlMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.pages_crawled = 0
        self.documents_downloaded = 0
        self.errors = []
    
    def log_completion(self):
        duration = time.time() - self.start_time
        logger.info(f"Crawl completed: {self.pages_crawled} pages, "
                   f"{self.documents_downloaded} documents in {duration:.2f}s")
```

## API Reference

### Crawl Request

```python
class CrawlRequest:
    url: str
    max_documents: int = 50
    max_pages: int = 100
    max_workers: int = 10
    delay: float = 1.0
    total_timeout: int = 300
    page_timeout: int = 30
    request_timeout: int = 30
    use_proxy: bool = True
    proxy_api_key: Optional[str] = None
    render: bool = True
    retry: int = 3
```

### Crawl Response

```python
class CrawlResponse:
    task_id: str
    status: str
    message: str
    url: str
    max_documents: int
    created_at: datetime
```

### Crawl Status

```python
class CrawlStatus:
    task_id: str
    status: str
    progress: Dict[str, Any]
    documents_downloaded: int
    pages_crawled: int
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_crawl_task_creation():
    with patch('common.src.services.crawler_service.get_advanced_crawler') as mock_crawler:
        mock_crawler.return_value = Mock()
        
        service = CrawlerService()
        request = CrawlRequest(url="https://example.com")
        
        response = await service.create_crawl_task(request, "user123")
        
        assert response.task_id is not None
        assert response.status == "pending"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_crawl_workflow():
    # Test complete crawl workflow
    service = CrawlerService()
    
    # Create task
    request = CrawlRequest(url="https://example.com", max_pages=5)
    response = await service.create_crawl_task(request, "user123")
    
    # Start crawl
    status = await service.start_crawl_task(response.task_id, "user123")
    
    # Wait for completion
    while status.status == "running":
        await asyncio.sleep(1)
        status = await service.get_crawl_status(response.task_id)
    
    assert status.status == "completed"
    assert status.pages_crawled > 0
```

## Performance Optimization

### 1. Lambda Cold Start

- Use container images for faster startup
- Implement lazy loading for heavy modules
- Use connection pooling for databases

### 2. Memory Usage

- Process files in chunks
- Clean up temporary files immediately
- Use streaming for large files

### 3. Network Optimization

- Use connection pooling for HTTP requests
- Implement request caching where appropriate
- Use compression for large responses

### 4. Cost Optimization

- Monitor ScrapingBee credit usage
- Use appropriate proxy levels
- Implement intelligent retry logic

## Security Considerations

### 1. API Key Management

- Use AWS Secrets Manager for API keys
- Rotate keys regularly
- Monitor key usage

### 2. Data Privacy

- Implement data retention policies
- Encrypt sensitive data
- Follow GDPR compliance

### 3. Access Control

- Implement proper IAM roles
- Use least privilege principle
- Monitor access logs

## Support and Maintenance

### Monitoring

- Set up CloudWatch alarms for Lambda errors
- Monitor SQS queue depth
- Track ScrapingBee credit usage

### Maintenance

- Regular dependency updates
- Security patches
- Performance monitoring

### Support Channels

- GitHub Issues for bug reports
- Documentation updates
- Team communication channels

---

**Last Updated**: January 2025
**Version**: 1.0
**Maintainer**: CrawlChat Development Team 