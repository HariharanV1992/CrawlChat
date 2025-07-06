# CrawlChat Service

A complete, production-ready PDF processing and AI chat service with AWS Lambda and ECS Fargate components.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Upload   │───▶│  S3 (uploaded)   │───▶│  SQS Queue      │
│   PDF/Image     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Chat       │◀───│  Lambda Function │◀───│  ECS Fargate    │
│   Response      │    │  (Textract +     │    │  (PDF Preproc)  │
│                 │    │   Vector Store)  │    │                 │
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
└── preprocessor-service/        # ECS Fargate PDF Preprocessor
    ├── README.md               # Preprocessor documentation
    ├── preprocessing_service.py # PDF processing logic
    ├── Dockerfile              # Preprocessor container build
    ├── requirements.txt        # Preprocessor dependencies
    ├── deploy.sh               # Deployment script
    ├── ecs-task-definition.json # ECS task definition
    ├── s3-notification.json    # S3 event configuration
    ├── sqs-policy.json         # SQS access policy
    └── iam-policies.json       # IAM policies
```

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Access to AWS services: Lambda, ECS, S3, SQS, IAM, CloudWatch

### Deployment Order

1. **Deploy Preprocessor Service** (ECS Fargate):
   ```bash
   cd preprocessor-service
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Deploy Lambda Service** (via GitHub Actions or manual):
   ```bash
   cd lambda-service
   # Follow Lambda deployment instructions
   ```

3. **Deploy Crawler Service** (via GitHub Actions or manual):
   ```bash
   cd crawler-service
   # Follow Lambda deployment instructions
   ```

## 🔧 Service Components

### 1. Lambda Service (`lambda-service/`)
- **Purpose**: Main API endpoint for chat and document processing
- **Features**: 
  - AWS Textract OCR processing
  - Vector store integration
  - AI chat responses
  - Document management
- **Deployment**: AWS Lambda with container image

### 2. Crawler Service (`crawler-service/`)
- **Purpose**: High-performance web crawler for document extraction
- **Features**:
  - Async web crawling with proxy support
  - Document detection and download
  - Intelligent link discovery
  - S3 storage integration
- **Deployment**: AWS Lambda with container image

### 3. Preprocessor Service (`preprocessor-service/`)
- **Purpose**: PDF normalization and preprocessing
- **Features**:
  - PDF text extraction with multiple fallbacks
  - PDF-to-image conversion for problematic PDFs
  - S3 event-driven processing
  - Auto-scaling ECS Fargate tasks
- **Deployment**: ECS Fargate with SQS integration

## 📊 Monitoring

### Lambda Service
- **CloudWatch Logs**: `/aws/lambda/crawlchat-api-function`
- **Metrics**: Invocation count, duration, errors
- **Console**: [Lambda Console](https://console.aws.amazon.com/lambda/home?region=ap-south-1#/functions/crawlchat-api-function)

### Crawler Service
- **CloudWatch Logs**: `/aws/lambda/crawlchat-crawler-function`
- **Metrics**: Invocation count, duration, errors
- **Console**: [Lambda Console](https://console.aws.amazon.com/lambda/home?region=ap-south-1#/functions/crawlchat-crawler-function)

### Preprocessor Service
- **CloudWatch Logs**: `/ecs/pdf-preprocessor`
- **ECS Service**: [ECS Console](https://console.aws.amazon.com/ecs/home?region=ap-south-1#/clusters/pdf-preprocessing-cluster/services/pdf-preprocessor-service)
- **SQS Queue**: [SQS Console](https://console.aws.amazon.com/sqs/home?region=ap-south-1#/queues/https%3A%2F%2Fsqs.ap-south-1.amazonaws.com%2F169164939839%2Fpdf-preprocess-queue)

## 🔄 Data Flow

### Document Processing Pipeline
1. **Upload**: User uploads PDF to S3 `crawlchat-data/uploaded_documents/{user_id}/`
2. **Trigger**: S3 event → SQS → ECS Fargate task
3. **Preprocessing**: PDF converted to normalized format
4. **Storage**: Normalized document stored in `crawlchat-data/normalized-documents/{user_id}/`
5. **Processing**: Lambda processes with Textract and vector store
6. **Response**: AI chat responses based on document content

### Crawler Pipeline
1. **Request**: User requests web crawling
2. **Crawler**: Lambda crawler service processes URLs
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

#### Preprocessor Service
- `S3_BUCKET`: S3 bucket name (crawlchat-data)
- `SQS_QUEUE_URL`: SQS queue URL
- `AWS_REGION`: AWS region (ap-south-1)

## 🔍 Testing

### Test Preprocessor
```bash
cd preprocessor-service
# Upload test PDF to S3
aws s3 cp test.pdf s3://crawlchat-data/uploaded_documents/test-user/test.pdf
# Check ECS logs for processing
```

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
from src.crawler.advanced_crawler import CrawlConfig

async def test_crawl():
    crawler = AdvancedCrawler()
    config = CrawlConfig(max_pages=5, delay=1.0)
    results = await crawler.crawl('https://example.com', config)
    print(f'Crawled {len(results)} pages')

asyncio.run(test_crawl())
"
```

## 💰 Cost Optimization

### Lambda Service
- **Cold Start**: Use provisioned concurrency for consistent performance
- **Memory**: Optimize memory allocation for cost/performance balance
- **Timeout**: Set appropriate timeouts to avoid unnecessary charges

### Preprocessor Service
- **Scaling**: Set desired count to 0 when not in use
- **Spot Instances**: Use Spot for non-critical processing
- **Batch Processing**: Process multiple PDFs in single task

## 🔐 Security

### IAM Roles
- **Lambda Role**: Textract, S3, Vector store access
- **ECS Task Role**: S3 read/write, SQS access
- **ECS Execution Role**: ECR pull, CloudWatch logs

### Data Protection
- **S3 Encryption**: Objects encrypted at rest
- **VPC**: Services run in secure VPC
- **API Keys**: Stored as environment variables

## 📈 Scaling

### Lambda Service
- **Automatic**: Scales based on request volume
- **Concurrency**: Configurable concurrent executions
- **Memory**: Adjustable memory allocation

### Preprocessor Service
- **ECS Scaling**: Based on SQS queue depth
- **Fargate**: Automatic infrastructure scaling
- **Manual**: Adjust desired task count

## 🔄 Updates

### Update Lambda Service
```bash
cd lambda-service
# Build and push new image
docker build -t crawlchat-lambda .
docker tag crawlchat-lambda:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
```

### Update Preprocessor Service
```bash
cd preprocessor-service
# Build and push new image
docker build -t pdf-preprocessor .
docker tag pdf-preprocessor:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/pdf-preprocessor:latest
docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/pdf-preprocessor:latest
# Force new deployment
aws ecs update-service --cluster pdf-preprocessing-cluster --service pdf-preprocessor-service --force-new-deployment
```

## 🚨 Troubleshooting

### Common Issues

1. **Lambda Timeouts**
   - Check Textract processing time
   - Verify vector store connectivity
   - Review memory allocation

2. **Preprocessor Failures**
   - Check ECS task logs
   - Verify S3 permissions
   - Review PDF format compatibility

3. **S3 Event Issues**
   - Verify S3 notification configuration
   - Check SQS queue policy
   - Monitor ECS service status

### Log Analysis
```bash
# Lambda logs
aws logs tail /aws/lambda/crawlchat-api-function --follow

# Preprocessor logs
aws logs tail /ecs/pdf-preprocessor --follow

# SQS queue status
aws sqs get-queue-attributes --queue-url https://sqs.ap-south-1.amazonaws.com/169164939839/pdf-preprocess-queue --attribute-names All
```

## 📞 Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify AWS service status
3. Review service-specific README files
4. Check deployment scripts for configuration

---

**CrawlChat Service** - Complete PDF processing and AI chat solution with serverless architecture. 