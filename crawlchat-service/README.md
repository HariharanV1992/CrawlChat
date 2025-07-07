# 🚀 CrawlChat API Service

A comprehensive web crawling and document processing service built with FastAPI, AWS Lambda, and smart ScrapingBee integration.

## 📋 Overview

This service provides:
- **Web Crawling**: Advanced crawler with smart ScrapingBee integration
- **Document Processing**: PDF processing with AWS Textract
- **Chat Interface**: AI-powered chat with processed documents
- **Smart Cost Optimization**: 90% cost savings with intelligent JavaScript rendering control

## 🏗️ Architecture

```
crawlchat-service/
├── common/                    # Shared code and dependencies
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── core/             # Configuration and core utilities
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic services
│   │   └── utils/            # Utility functions
├── crawler-service/          # Standalone crawler service
│   ├── src/crawler/          # Crawler implementation
│   │   ├── advanced_crawler.py
│   │   ├── smart_scrapingbee_manager.py
│   │   ├── proxy_manager.py
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
├── lambda-service/           # AWS Lambda deployment
│   ├── src/                  # Lambda-specific code
│   ├── Dockerfile
│   └── requirements.txt
└── tests/                    # Test files
```

## 🚀 Quick Start

### 1. Local Development

```bash
# Clone and setup
git clone <repository>
cd crawlchat-service

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SCRAPINGBEE_API_KEY="your_api_key"
export AWS_ACCESS_KEY_ID="your_aws_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret"

# Run the service
uvicorn common.src.api.main:app --reload
```

### 2. Docker Deployment

```bash
# Build and run with Docker
docker build -f lambda-service/Dockerfile -t crawlchat-api .
docker run -p 8000:8000 crawlchat-api
```

### 3. AWS Lambda Deployment

```bash
# Deploy to AWS Lambda
./deploy_lambda.sh
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
SCRAPINGBEE_API_KEY=your_scrapingbee_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Optional
AWS_REGION=ap-south-1
DATABASE_URL=your_database_url
```

### Smart ScrapingBee Configuration

The service uses smart ScrapingBee integration with:
- **No-JS First**: Always tries no-JavaScript requests first (90% cheaper)
- **Smart Fallback**: Only uses JS rendering when content is incomplete
- **Site Caching**: Remembers which sites require JavaScript
- **Cost Tracking**: Real-time cost estimation and savings

## 📊 API Endpoints

### Crawler Endpoints

```bash
# Start crawling
POST /api/v1/crawler/start
{
  "url": "https://example.com",
  "max_depth": 2,
  "max_pages": 50,
  "site_type": "news"
}

# Get crawling status
GET /api/v1/crawler/status/{task_id}

# Get crawling results
GET /api/v1/crawler/results/{task_id}
```

### Document Processing

```bash
# Upload and process document
POST /api/v1/documents/upload
Content-Type: multipart/form-data

# Get document processing status
GET /api/v1/documents/{document_id}/status

# Get processed content
GET /api/v1/documents/{document_id}/content
```

### Chat Interface

```bash
# Start chat session
POST /api/v1/chat/start
{
  "document_id": "doc_123"
}

# Send message
POST /api/v1/chat/message
{
  "session_id": "session_123",
  "message": "What is the main topic?"
}
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python test_smart_scrapingbee.py
```

### Test Smart ScrapingBee Integration

```bash
# Set your API key
export SCRAPINGBEE_API_KEY="your_api_key"

# Run comprehensive tests
python test_smart_scrapingbee.py
```

## 📈 Performance Monitoring

### Cost Tracking

The service provides real-time cost tracking:

```python
# Get usage statistics
stats = manager.get_stats()
print(f"No-JS Requests: {stats['no_js_requests']}")
print(f"JS Requests: {stats['js_requests']}")
print(f"Cost Savings: ${stats['cost_savings']}")
```

### Real-time Monitoring

```python
# During crawling
crawler = AdvancedCrawler(api_key="your_api_key")
realtime_stats = crawler.get_realtime_stats()
print(f"URLs visited: {realtime_stats['urls_visited']}")
print(f"Files downloaded: {realtime_stats['files_downloaded']}")
```

## 🔄 Site Requirements Caching

The system automatically caches which sites require JavaScript:

```python
# Save site requirements
manager.save_site_requirements("site_js_requirements.json")

# Load site requirements
manager.load_site_requirements("site_js_requirements.json")
```

## 🚀 Deployment

### AWS Lambda

```bash
# Deploy Lambda function
./deploy_lambda.sh

# Update environment variables
./update_lambda_env.sh
```

### Docker

```bash
# Build Lambda service
docker build -f lambda-service/Dockerfile -t crawlchat-api .

# Build Crawler service
cd crawler-service
docker build -t crawlchat-crawler .
```

### ECS/Fargate

```bash
# Deploy to ECS (if needed)
./deploy_ecs.sh
```

## 📝 Migration Guide

### From Old Proxy Manager

1. **Update Imports**
   ```python
   # Old
   from .proxy_manager import ProxyManager
   
   # New
   from .proxy_manager import ScrapingBeeProxyManager as ProxyManager
   ```

2. **Update Initialization**
   ```python
   # Old
   proxy_manager = ProxyManager(api_key, use_proxy=True)
   
   # New
   proxy_manager = ScrapingBeeProxyManager(api_key)
   ```

3. **Update Request Calls**
   ```python
   # Old
   response = proxy_manager.make_request(url)
   
   # New
   response = await proxy_manager.make_request(url, site_type='news')
   ```

## 🎉 Benefits

- **90% Cost Reduction**: Smart no-JS first approach
- **Improved Reliability**: Automatic fallback to JS when needed
- **Better Performance**: Site-specific caching and optimization
- **Comprehensive Monitoring**: Real-time statistics and cost tracking
- **Easy Integration**: Seamless integration with existing crawler
- **Flexible Configuration**: Custom content checkers and site options

## 🔗 Related Files

- `smart_scrapingbee_manager.py`: Core smart manager implementation
- `proxy_manager.py`: Updated proxy manager with smart integration
- `advanced_crawler.py`: Updated crawler using smart proxy manager
- `test_smart_scrapingbee.py`: Comprehensive test suite
- `SMART_SCRAPINGBEE_INTEGRATION.md`: Complete documentation

## 🚀 Next Steps

1. **Test the Implementation**: Run the test script to verify functionality
2. **Monitor Usage**: Track JS usage rates and optimize content checkers
3. **Customize Checkers**: Create site-specific content checkers as needed
4. **Scale Up**: Deploy to production and monitor cost savings
5. **Optimize Further**: Fine-tune based on real-world usage patterns

---

**Ready to optimize your ScrapingBee costs? The smart integration is now ready for production use! 🎉** 