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

## Recent Fixes

### ✅ Fixed: get_storage_service Import Error

**Issue**: Lambda crawler worker was failing with `name 'get_storage_service' is not defined` error.

**Solution**: Added missing import in `common/src/services/crawler_service.py`:

```python
from common.src.services.storage_service import get_storage_service
```

**Status**: ✅ Fixed and tested

### ✅ Improved: ScrapingBee Configuration

**Enhancement**: Implemented progressive proxy strategy for better success rates:

1. **Standard Mode** (5 credits): Basic JavaScript rendering
2. **Premium Proxy** (25 credits): For difficult sites
3. **Stealth Proxy** (75 credits): For heavily protected sites

## Prerequisites

### Required Services

1. **AWS Account** with appropriate permissions
2. **MongoDB Atlas** or self-hosted MongoDB
3. **ScrapingBee API Key** for web scraping
4. **OpenAI API Key** for AI features (optional)

### Required Tools

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Docker
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER

# Install AWS CDK (optional)
npm install -g aws-cdk
```

## Environment Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Required
SCRAPINGBEE_API_KEY=your-scrapingbee-api-key
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/crawlchat
S3_BUCKET=your-crawlchat-bucket
AWS_REGION=us-east-1

# Optional
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 2. AWS Configuration

```bash
# Configure AWS CLI
aws configure

# Set default region
aws configure set default.region us-east-1
```

### 3. S3 Bucket Setup

```bash
# Create S3 bucket
aws s3 mb s3://your-crawlchat-bucket

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket your-crawlchat-bucket \
    --versioning-configuration Status=Enabled

# Configure lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
    --bucket your-crawlchat-bucket \
    --lifecycle-configuration file://lifecycle-policy.json
```

## Deployment Options

### Option 1: Lambda Container Deployment (Recommended)

#### 1. Build Docker Image

```bash
# Build the Lambda container image
cd lambda-service
docker build -t crawlchat-crawl-worker .

# Tag for ECR
docker tag crawlchat-crawl-worker:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-crawl-worker:latest
```

#### 2. Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
docker login --username AWS --password-stdin \
123456789012.dkr.ecr.us-east-1.amazonaws.com

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-crawl-worker:latest
```

#### 3. Deploy Infrastructure

```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file infra/crawlchat-crawl-worker.yml \
    --stack-name crawlchat-crawler \
    --parameter-overrides \
        LambdaImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-crawl-worker:latest \
    --capabilities CAPABILITY_NAMED_IAM
```

### Option 2: ECS Deployment

#### 1. Build and Push Image

```bash
# Build image
docker build -t crawlchat-service .

# Tag and push
docker tag crawlchat-service:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-service:latest

docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-service:latest
```

#### 2. Deploy ECS Service

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name crawlchat-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster crawlchat-cluster \
    --service-name crawlchat-service \
    --task-definition crawlchat-task:1 \
    --desired-count 1
```

## Configuration

### 1. ScrapingBee Setup

#### API Key Configuration

```bash
# Set environment variable
export SCRAPINGBEE_API_KEY="your-api-key"

# Or add to AWS Systems Manager Parameter Store
aws ssm put-parameter \
    --name "/crawlchat/scrapingbee-api-key" \
    --value "your-api-key" \
    --type "SecureString"
```

#### Progressive Proxy Strategy

The crawler now uses a progressive proxy strategy:

```python
# Configuration in crawler_service.py
def get_scrapingbee_params(use_premium=False, use_stealth=False):
    params = {
        "render_js": True,
        "timeout": 140000,
        "wait": 2000,
        "block_resources": True
    }
    
    if use_stealth:
        params["stealth_proxy"] = True
        params["premium_proxy"] = False
    elif use_premium:
        params["premium_proxy"] = True
        params["stealth_proxy"] = False
    
    return params
```

### 2. MongoDB Configuration

#### Connection String

```python
# In config.py
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/crawlchat")

# For MongoDB Atlas
MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/crawlchat?retryWrites=true&w=majority"
```

#### Database Setup

```javascript
// Create indexes for better performance
db.tasks.createIndex({ "task_id": 1 }, { unique: true })
db.tasks.createIndex({ "user_id": 1 })
db.tasks.createIndex({ "status": 1 })
db.tasks.createIndex({ "created_at": -1 })

db.documents.createIndex({ "document_id": 1 }, { unique: true })
db.documents.createIndex({ "user_id": 1 })
db.documents.createIndex({ "task_id": 1 })
```

### 3. S3 Configuration

#### Bucket Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCrawlChatAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/crawlchat-crawl-worker-role"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-crawlchat-bucket",
                "arn:aws:s3:::your-crawlchat-bucket/*"
            ]
        }
    ]
}
```

#### CORS Configuration

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Testing

### 1. Run Test Suite

```bash
# Test the crawler fix
python3 test_crawler_fix.py

# Test service health
python3 service_health_check.py

# Test imports
python3 tests/test_imports.py
```

### 2. Manual Testing

```bash
# Test crawler service
curl -X POST http://localhost:8000/api/v1/crawler/create \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://example.com",
        "max_pages": 5,
        "max_documents": 10
    }'

# Check task status
curl http://localhost:8000/api/v1/crawler/status/{task_id}
```

### 3. Lambda Testing

```bash
# Test Lambda function locally
docker run -p 9000:8080 crawlchat-crawl-worker

# Invoke Lambda
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -d '{
        "Records": [{
            "body": "{\"task_id\": \"test-task\", \"user_id\": \"test-user\"}"
        }]
    }'
```

## Monitoring

### 1. CloudWatch Alarms

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
    --alarm-name "CrawlChat-Lambda-Errors" \
    --alarm-description "Lambda function errors" \
    --metric-name "Errors" \
    --namespace "AWS/Lambda" \
    --statistic "Sum" \
    --period 300 \
    --threshold 1 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 1 \
    --alarm-actions "arn:aws:sns:us-east-1:123456789012:crawlchat-alerts"
```

### 2. SQS Monitoring

```bash
# Monitor queue depth
aws cloudwatch put-metric-alarm \
    --alarm-name "CrawlChat-SQS-Queue-Depth" \
    --alarm-description "SQS queue depth" \
    --metric-name "ApproximateNumberOfVisibleMessages" \
    --namespace "AWS/SQS" \
    --statistic "Average" \
    --period 300 \
    --threshold 100 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 2
```

### 3. ScrapingBee Monitoring

```python
# Monitor API credits
import requests

def check_scrapingbee_credits():
    response = requests.get(
        "https://app.scrapingbee.com/api/v1/usage",
        params={"api_key": os.getenv("SCRAPINGBEE_API_KEY")}
    )
    return response.json()

# Set up monitoring
credits = check_scrapingbee_credits()
if credits['used_api_credit'] > credits['max_api_credit'] * 0.8:
    # Send alert
    pass
```

## Troubleshooting

### Common Issues

#### 1. Lambda Timeout

**Problem**: Crawl tasks taking too long
**Solution**: 
- Increase Lambda timeout to 900 seconds
- Reduce `max_pages` and `max_documents`
- Use `block_resources=True` for faster scraping

#### 2. Memory Issues

**Problem**: Lambda running out of memory
**Solution**:
- Increase Lambda memory to 1024MB or higher
- Process files in smaller chunks
- Clean up temporary files immediately

#### 3. ScrapingBee Errors

**Problem**: 403/429 errors from websites
**Solution**:
- Use progressive proxy strategy
- Implement retry logic with exponential backoff
- Check API key validity and credits

#### 4. S3 Upload Failures

**Problem**: Files not uploading to S3
**Solution**:
- Check IAM permissions
- Verify S3 bucket exists and is accessible
- Check network connectivity

### Debug Commands

```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/crawlchat"

# Get recent log events
aws logs get-log-events \
    --log-group-name "/aws/lambda/crawlchat-crawl-worker" \
    --log-stream-name "latest"

# Check SQS queue
aws sqs get-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/crawlchat-crawl-tasks \
    --attribute-names All

# Test MongoDB connection
python3 -c "
import asyncio
from common.src.core.database import mongodb
async def test():
    await mongodb.connect()
    print('Connected successfully')
asyncio.run(test())
"
```

## Security

### 1. IAM Best Practices

- Use least privilege principle
- Rotate access keys regularly
- Use IAM roles instead of access keys when possible

### 2. API Key Security

- Store API keys in AWS Secrets Manager
- Use environment variables in Lambda
- Never commit API keys to version control

### 3. Network Security

- Use VPC for Lambda functions if needed
- Configure security groups appropriately
- Use HTTPS for all external communications

## Cost Optimization

### 1. Lambda Optimization

- Use provisioned concurrency for consistent workloads
- Optimize memory allocation
- Use container images for faster cold starts

### 2. ScrapingBee Optimization

- Monitor credit usage
- Use appropriate proxy levels
- Implement intelligent retry logic

### 3. S3 Optimization

- Use lifecycle policies for old data
- Compress files before upload
- Use appropriate storage classes

## Maintenance

### 1. Regular Updates

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Docker images
docker pull crawlchat-crawl-worker:latest

# Update Lambda function
aws lambda update-function-code \
    --function-name crawlchat-crawl-worker \
    --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/crawlchat-crawl-worker:latest
```

### 2. Backup Strategy

- Regular MongoDB backups
- S3 versioning enabled
- Cross-region replication for critical data

### 3. Monitoring and Alerting

- Set up comprehensive monitoring
- Configure alerts for critical issues
- Regular health checks

---

**Last Updated**: January 2025
**Version**: 2.0
**Maintainer**: CrawlChat Development Team 