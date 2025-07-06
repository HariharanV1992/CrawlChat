# CrawlChat Crawler Service

High-performance web crawler service for document extraction and processing with advanced features.

## 🏗️ Architecture

```
User Request → API Gateway → Lambda Function → Crawler Service
                                    ↓
                            Advanced Crawler Engine
                                    ↓
                            Document Processing → S3 Storage
```

## 📁 File Structure

```
crawler-service/
├── README.md           # This file
├── crawler_main.py     # Crawler service entry point
├── main.py            # Main Lambda application
├── lambda_handler.py  # Lambda entry point
├── Dockerfile         # Container build instructions
├── requirements.txt   # Python dependencies
└── src/               # Source code
    ├── crawler/       # Advanced crawler engine
    │   ├── advanced_crawler.py    # Main crawler logic
    │   ├── file_downloader.py     # File download handling
    │   ├── link_extractor.py      # Link extraction logic
    │   ├── proxy_manager.py       # Proxy management
    │   ├── settings_manager.py    # Settings management
    │   └── utils.py               # Crawler utilities
    ├── core/          # Core configuration
    ├── models/        # Data models
    ├── services/      # Business logic
    │   └── crawler_service.py     # Crawler service
    └── utils/         # Utilities
```

## 🚀 Features

### Advanced Crawler Engine
- **Async Processing**: High-performance async web crawling
- **Proxy Support**: Intelligent proxy rotation and management
- **Document Detection**: Automatic detection of PDFs, images, and documents
- **Rate Limiting**: Configurable delays and request limits
- **Error Handling**: Robust error recovery and retry mechanisms
- **File Download**: Automatic download and S3 storage of documents

### Crawler Capabilities
- **Multi-threaded**: Concurrent processing of multiple URLs
- **Intelligent Parsing**: Smart content extraction and filtering
- **Link Discovery**: Automatic discovery of relevant links
- **Content Analysis**: Document type detection and validation
- **Storage Integration**: Direct S3 upload of crawled documents

## 🔧 Configuration

### Environment Variables
- `S3_BUCKET`: S3 bucket for document storage
- `MONGODB_URI`: MongoDB connection string
- `OPENAI_API_KEY`: OpenAI API key for content analysis
- `CRAWLER_MAX_WORKERS`: Maximum concurrent crawler workers
- `CRAWLER_DELAY`: Delay between requests (seconds)

### Crawler Settings
```python
crawl_config = CrawlConfig(
    max_workers=10,
    delay=1.0,
    timeout=30,
    max_pages=100,
    allowed_domains=["example.com"],
    file_types=[".pdf", ".doc", ".docx", ".txt"]
)
```

## 📊 Monitoring

### CloudWatch Logs
- **Log Group**: `/aws/lambda/crawlchat-crawler-function`
- **Console**: [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups/log-group/aws/lambda/crawlchat-crawler-function)

### Crawler Metrics
- **Active Tasks**: Number of running crawl tasks
- **Documents Processed**: Count of successfully processed documents
- **Error Rate**: Percentage of failed crawl attempts
- **Processing Time**: Average time per document

## 🔍 Testing

### Local Testing
```bash
# Test crawler service
python crawler_main.py

# Test with specific URL
python -c "
import asyncio
from src.crawler.advanced_crawler import AdvancedCrawler
from src.crawler.advanced_crawler import CrawlConfig

async def test_crawl():
    crawler = AdvancedCrawler()
    config = CrawlConfig(max_pages=5, delay=1.0)
    results = await crawler.crawl('https://example.com', config)
    print(f'Crawled {len(results)} pages')

asyncio.run(test_crawl())
"
```

### API Testing
```bash
# Create crawl task
curl -X POST https://your-api-gateway-url/crawler/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://example.com",
    "max_pages": 10,
    "user_id": "test-user"
  }'

# Check task status
curl -X GET https://your-api-gateway-url/crawler/tasks/{task_id}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Crawler Timeouts**
   - Increase timeout settings
   - Check network connectivity
   - Review target website response times

2. **Memory Issues**
   - Reduce max_workers
   - Implement pagination
   - Monitor memory usage

3. **Rate Limiting**
   - Increase delay between requests
   - Use proxy rotation
   - Respect robots.txt

### Log Analysis
```bash
# View crawler logs
aws logs tail /aws/lambda/crawlchat-crawler-function --follow

# Search for crawler errors
aws logs filter-log-events --log-group-name /aws/lambda/crawlchat-crawler-function --filter-pattern "ERROR"
```

## 💰 Cost Optimization

### Optimization Strategies
1. **Batch Processing**: Process multiple URLs in single task
2. **Smart Filtering**: Filter irrelevant content early
3. **Caching**: Cache previously crawled content
4. **Resource Limits**: Set appropriate memory and timeout limits

### Cost Monitoring
- **Lambda Invocations**: Monitor function calls
- **S3 Storage**: Track document storage costs
- **Network Transfer**: Monitor data transfer costs

## 🔐 Security

### IAM Permissions
- **S3**: Read/write access to crawlchat-data bucket
- **MongoDB**: Database access for task management
- **CloudWatch**: Logging and monitoring

### Security Features
- **Input Validation**: Validate all user inputs
- **Rate Limiting**: Prevent abuse and overloading
- **Content Filtering**: Filter malicious content
- **Secure Storage**: Encrypted document storage

## 📈 Scaling

### Automatic Scaling
- **Lambda**: Scales based on request volume
- **Concurrent Tasks**: Multiple crawl tasks can run simultaneously
- **Resource Allocation**: Adjustable memory and timeout

### Manual Scaling
```bash
# Update memory allocation
aws lambda update-function-configuration --function-name crawlchat-crawler-function --memory-size 2048

# Update timeout
aws lambda update-function-configuration --function-name crawlchat-crawler-function --timeout 60
```

## 🔄 Updates

### Code Updates
1. **Build new image**
2. **Push to ECR**
3. **Update Lambda function**

### Configuration Updates
```bash
# Update environment variables
aws lambda update-function-configuration --function-name crawlchat-crawler-function --environment Variables='{"CRAWLER_MAX_WORKERS":"20"}'
```

## 📞 Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify crawler configuration
3. Review target website accessibility
4. Check network and proxy settings

---

**CrawlChat Crawler Service** - High-performance web crawler for document extraction and processing. 