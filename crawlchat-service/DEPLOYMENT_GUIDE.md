# 🚀 CrawlChat Service Deployment Guide

Complete deployment guide for the CrawlChat service with AWS Lambda and smart ScrapingBee integration.

## 📋 Overview

This guide covers deployment of:
- **Lambda API Service**: Main API endpoint with Textract integration
- **Crawler Service**: Advanced web crawler with smart ScrapingBee integration
- **Smart Cost Optimization**: 90% cost savings with intelligent JavaScript rendering control

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Upload   │───▶│  S3 (uploaded)   │───▶│  Lambda API     │
│   PDF/Image     │    │                  │    │  (Textract)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Chat       │◀───│  Vector Store    │◀───│  Processed      │
│   Response      │    │  (Embeddings)    │    │  Documents      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Service Structure

```
crawlchat-service/
├── README.md                    # This file
├── lambda-service/              # AWS Lambda API Service
│   ├── README.md               # Lambda service documentation
│   ├── main.py                 # Main Lambda application
│   ├── lambda_handler.py       # Lambda entry point
│   ├── Dockerfile              # Lambda container build
│   ├── requirements.txt        # Lambda dependencies
│   └── src/                    # Lambda source code
│       ├── api/                # API endpoints
│       ├── core/               # Core configuration
│       ├── services/           # Business logic
│       └── utils/              # Utilities
├── crawler-service/             # AWS Lambda Crawler Service
│   ├── README.md               # Crawler service documentation
│   ├── crawler_main.py         # Crawler service entry point
│   ├── main.py                 # Main Lambda application
│   ├── lambda_handler.py       # Lambda entry point
│   ├── Dockerfile              # Lambda container build
│   ├── requirements.txt        # Crawler dependencies
│   └── src/                    # Crawler source code
│       ├── crawler/            # Advanced crawler engine
│       ├── core/               # Core configuration
│       ├── models/             # Data models
│       ├── services/           # Business logic
│       └── utils/              # Utilities
└── common/                     # Shared code and dependencies
    ├── src/
    │   ├── api/               # FastAPI endpoints
    │   ├── core/              # Configuration and core utilities
    │   ├── models/            # Pydantic models
    │   ├── services/          # Business logic services
    │   └── utils/             # Utility functions
```

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Access to AWS services: Lambda, S3, IAM, CloudWatch
- ScrapingBee API key for smart web crawling

### Deployment Order

1. **Deploy Lambda Service** (via GitHub Actions or manual):
   ```bash
   cd lambda-service
   # Follow Lambda deployment instructions
   ```

2. **Deploy Crawler Service** (via GitHub Actions or manual):
   ```bash
   cd crawler-service
   # Follow Lambda deployment instructions
   ```

## 🔧 Service Components

### 1. Lambda Service (`lambda-service/`)
- **Purpose**: Main API endpoint for chat and document processing
- **Features**: 
  - AWS Textract OCR processing (with integrated PDF preprocessing)
  - Vector store integration
  - AI chat responses
  - Document management
- **Deployment**: AWS Lambda with container image

### 2. Crawler Service (`crawler-service/`)
- **Purpose**: High-performance web crawler with smart ScrapingBee integration
- **Features**:
  - Async web crawling with smart proxy support
  - Document detection and download
  - Intelligent link discovery
  - S3 storage integration
  - 90% cost savings with smart JavaScript rendering control
- **Deployment**: AWS Lambda with container image

## 📊 Monitoring

### Lambda Service
- **CloudWatch Logs**: `/aws/lambda/crawlchat-api-function`
- **Metrics**: Invocation count, duration, errors
- **Console**: [Lambda Console](https://console.aws.amazon.com/lambda/home?region=ap-south-1#/functions/crawlchat-api-function)

### Crawler Service
- **CloudWatch Logs**: `/aws/lambda/crawlchat-crawler-function`
- **Metrics**: Invocation count, duration, errors
- **Console**: [Lambda Console](https://console.aws.amazon.com/lambda/home?region=ap-south-1#/functions/crawlchat-crawler-function)

## 🔄 Data Flow

### Document Processing Pipeline
1. **Upload**: User uploads PDF to S3 `crawlchat-data/uploaded_documents/{user_id}/`
2. **Processing**: Lambda processes with integrated Textract (includes PDF preprocessing)
3. **Storage**: Processed document stored in `crawlchat-data/processed-documents/{user_id}/`
4. **Vector Store**: Document embeddings stored for AI chat
5. **Response**: AI chat responses based on document content

### Crawler Pipeline
1. **Request**: User requests web crawling
2. **Smart Crawler**: Lambda crawler service with smart ScrapingBee integration
3. **Discovery**: Advanced crawler discovers documents and links
4. **Download**: Documents downloaded and stored in S3
5. **Processing**: Documents processed with Textract and vector store
6. **Response**: AI chat responses based on crawled content

### Chat Pipeline
1. **Query**: User sends chat message
2. **Search**: Vector store searches document embeddings
3. **Context**: Relevant document chunks retrieved
4. **Response**: AI generates response with document context

## 🛠️ Configuration

### Environment Variables

#### Lambda Service
- `OPENAI_API_KEY`: OpenAI API key for AI responses
- `TEXTRACT_REGION`: AWS Textract region (ap-south-1)
- `S3_BUCKET`: S3 bucket name (crawlchat-data)

#### Crawler Service
- `OPENAI_API_KEY`: OpenAI API key for content analysis
- `S3_BUCKET`: S3 bucket name (crawlchat-data)
- `MONGODB_URI`: MongoDB connection string
- `CRAWLER_MAX_WORKERS`: Maximum concurrent crawler workers
- `SCRAPINGBEE_API_KEY`: ScrapingBee API key for smart web crawling

## 🔍 Testing

### Test Lambda
```bash
cd lambda-service
# Test with sample event
python -c "import lambda_handler; print(lambda_handler.lambda_handler({}, {}))"
```

### Test Crawler
```bash
cd crawler-service
# Test crawler service
python crawler_main.py

# Test with specific URL
python -c "
import asyncio
from src.crawler.advanced_crawler import AdvancedCrawler

async def test_crawl():
    crawler = AdvancedCrawler(api_key='your_scrapingbee_key')
    results = await crawler.crawl('https://example.com')
    print(f'Crawled {len(results)} pages')

asyncio.run(test_crawl())
"
```

### Test Smart ScrapingBee Integration
```bash
# Set your API key
export SCRAPINGBEE_API_KEY="your_api_key"

# Run comprehensive tests
python test_smart_scrapingbee.py
```

## 💰 Cost Optimization

### Lambda Service
- **Cold Start**: Use provisioned concurrency for consistent performance
- **Memory**: Optimize memory allocation for cost/performance balance
- **Timeout**: Set appropriate timeouts to avoid unnecessary charges

### Smart ScrapingBee Integration
- **No-JS First**: Always tries no-JavaScript requests first (90% cheaper)
- **Smart Fallback**: Only uses JS rendering when content is incomplete
- **Site Caching**: Remembers which sites require JavaScript
- **Cost Tracking**: Real-time cost estimation and savings

## 🔐 Security

### IAM Roles
- **Lambda Role**: Textract, S3, Vector store access
- **Crawler Role**: S3 read/write, ScrapingBee API access

### Data Protection
- **S3 Encryption**: Objects encrypted at rest
- **VPC**: Services run in secure VPC
- **API Keys**: Stored as environment variables

## 📈 Scaling

### Lambda Service
- **Automatic**: Scales based on request volume
- **Concurrency**: Configurable concurrent executions
- **Memory**: Adjustable memory allocation

### Crawler Service
- **Automatic**: Scales based on request volume
- **Smart Proxy**: Efficient ScrapingBee usage with cost optimization
- **Async Processing**: Concurrent crawling with rate limiting

## 🔄 Updates

### Update Lambda Service
```bash
cd lambda-service
# Build and push new image
docker build -t crawlchat-lambda .
docker tag crawlchat-lambda:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
```

### Update Crawler Service
```bash
cd crawler-service
# Build and push new image
docker build -t crawlchat-crawler .
docker tag crawlchat-crawler:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-crawler:latest
docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-crawler:latest
```

## 🚨 Troubleshooting

### Common Issues

1. **Lambda Timeouts**
   - Check Textract processing time
   - Verify vector store connectivity
   - Review memory allocation

2. **Crawler Failures**
   - Check ScrapingBee API key and quota
   - Verify S3 permissions
   - Review crawler configuration

3. **Smart ScrapingBee Issues**
   - Check API key validity
   - Monitor cost usage
   - Review content checkers

### Log Analysis
```bash
# Lambda logs
aws logs tail /aws/lambda/crawlchat-api-function --follow

# Crawler logs
aws logs tail /aws/lambda/crawlchat-crawler-function --follow

# Smart ScrapingBee stats
python -c "
from crawler_service.src.crawler.smart_scrapingbee_manager import SmartScrapingBeeManager
manager = SmartScrapingBeeManager('your_api_key')
print('Stats:', manager.get_stats())
print('Cost:', manager.get_cost_estimate())
"
```

## 📞 Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify AWS service status
3. Review service-specific README files
4. Check deployment scripts for configuration
5. Monitor ScrapingBee usage and costs

---

**CrawlChat Service** - Complete document processing and AI chat solution with smart ScrapingBee integration and serverless architecture. 