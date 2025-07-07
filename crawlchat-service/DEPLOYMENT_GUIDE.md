# CrawlChat Complete Deployment Guide

## 🏗️ Architecture Overview

CrawlChat consists of **3 main services** that work together to provide a complete document processing and AI chat solution:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Upload   │───▶│  S3 (uploaded)   │───▶│  SQS Queue      │
│   PDF/Image     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Chat       │◀───│  Lambda API      │◀───│  ECS Fargate    │
│   Response      │    │  (Main Service)  │    │  (Preprocessor) │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Lambda Crawler │    │  Vector Store    │
│  (Web Crawling) │    │  (Document DB)   │
└─────────────────┘    └──────────────────┘
```

## 📋 Service Details

### 1. **Lambda API Service** (`lambda-service/`)
- **Purpose**: Main API endpoint for crawlchat.site
- **Deployment**: AWS Lambda (serverless)
- **Function Name**: `crawlchat-api-function`
- **ECR Repository**: `crawlchat-api`
- **What it does**:
  - Handles all HTTP requests from the website
  - Processes documents with AWS Textract OCR
  - Manages AI chat responses using OpenAI
  - Integrates with vector store for document search
  - Handles user authentication and sessions
  - **Single Lambda function** that serves as the main API

### 2. **Lambda Crawler Service** (`crawler-service/`)
- **Purpose**: Web crawling for document extraction
- **Deployment**: AWS Lambda (serverless)
- **Function Name**: `crawlchat-crawler-function`
- **ECR Repository**: `crawlchat-crawler`
- **What it does**:
  - Crawls websites to find and download documents
  - Extracts text content from web pages
  - Stores crawled data in S3
  - Integrates with the main API for processing
  - Runs on-demand when users request web crawling

### 3. **ECS Preprocessor Service** (`preprocessor-service/`)
- **Purpose**: PDF preprocessing and normalization
- **Deployment**: ECS Fargate (containerized)
- **ECR Repository**: `crawlchat-preprocessor`
- **What it does**:
  - Converts PDFs to images for OCR processing
  - Extracts text from PDFs using multiple methods
  - Normalizes documents for consistent processing
  - Runs as background tasks triggered by S3 events
  - Handles complex PDF processing that Lambda can't handle

## 🚀 Deployment Process

### Automatic Deployment (GitHub Actions)

The GitHub Actions workflow (`deploy.yml`) automatically deploys all three services:

1. **Triggers**: Push to `main` branch or manual trigger
2. **Builds**: All three Docker images
3. **Pushes**: Images to ECR repositories
4. **Updates**: Lambda functions with new images

### Manual Deployment Steps

If you need to deploy manually:

#### 1. Deploy Lambda API Service
```bash
cd crawlchat-service
docker build -f lambda-service/Dockerfile -t crawlchat-api .
docker tag crawlchat-api:latest $ECR_REGISTRY/crawlchat-api:latest
docker push $ECR_REGISTRY/crawlchat-api:latest

aws lambda update-function-code \
  --function-name crawlchat-api-function \
  --image-uri $ECR_REGISTRY/crawlchat-api:latest \
  --region ap-south-1
```

#### 2. Deploy Crawler Service
```bash
cd crawlchat-service
docker build -f crawler-service/Dockerfile -t crawlchat-crawler .
docker tag crawlchat-crawler:latest $ECR_REGISTRY/crawlchat-crawler:latest
docker push $ECR_REGISTRY/crawlchat-crawler:latest

aws lambda update-function-code \
  --function-name crawlchat-crawler-function \
  --image-uri $ECR_REGISTRY/crawlchat-crawler:latest \
  --region ap-south-1
```

#### 3. Deploy Preprocessor Service
```bash
cd crawlchat-service
docker build -f preprocessor-service/Dockerfile -t crawlchat-preprocessor .
docker tag crawlchat-preprocessor:latest $ECR_REGISTRY/crawlchat-preprocessor:latest
docker push $ECR_REGISTRY/crawlchat-preprocessor:latest

# Deploy to ECS (requires ECS cluster and service setup)
aws ecs update-service \
  --cluster pdf-preprocessing-cluster \
  --service pdf-preprocessor-service \
  --force-new-deployment \
  --region ap-south-1
```

## 🌐 How crawlchat.site Works

### User Experience Flow

1. **User visits** `crawlchat.site`
2. **Uploads documents** (PDFs, images, text files)
3. **Chats with AI** about the uploaded documents
4. **Gets intelligent responses** based on document content
5. **Optionally requests web crawling** for additional content

### Technical Flow

```
1. User Upload → S3 → SQS → ECS Preprocessor → Normalized S3
2. User Chat → Lambda API → Vector Store Search → OpenAI → Response
3. User Crawl Request → Lambda Crawler → Web Crawling → S3 → Processing
```

### Service Communication

- **Lambda API** is the **main entry point** for all user interactions
- **Crawler Service** runs **on-demand** when users request web crawling
- **Preprocessor Service** runs **automatically** when documents are uploaded
- **All services** share the same S3 bucket and vector store

## 🔧 Configuration Requirements

### Environment Variables

#### Lambda API Service
```bash
OPENAI_API_KEY=your_openai_key
TEXTRACT_REGION=ap-south-1
S3_BUCKET=crawlchat-data
MONGODB_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
```

#### Crawler Service
```bash
OPENAI_API_KEY=your_openai_key
S3_BUCKET=crawlchat-data
MONGODB_URI=your_mongodb_uri
CRAWLER_MAX_WORKERS=10
```

#### Preprocessor Service
```bash
S3_BUCKET=crawlchat-data
SQS_QUEUE_URL=your_sqs_queue_url
AWS_REGION=ap-south-1
```

### AWS Services Required

1. **Lambda Functions**: 2 functions (API + Crawler)
2. **ECS Cluster**: For preprocessor service
3. **S3 Bucket**: For document storage
4. **SQS Queue**: For preprocessor triggers
5. **ECR Repositories**: 3 repositories for images
6. **IAM Roles**: Proper permissions for all services

## 📊 Monitoring and Logs

### CloudWatch Log Groups
- **Lambda API**: `/aws/lambda/crawlchat-api-function`
- **Lambda Crawler**: `/aws/lambda/crawlchat-crawler-function`
- **ECS Preprocessor**: `/ecs/pdf-preprocessor`

### Key Metrics to Monitor
- Lambda invocation count and duration
- ECS task count and CPU/memory usage
- S3 object count and size
- SQS queue depth
- API Gateway request count and latency

## 🧪 Testing

### Test API Endpoints
```bash
# Test document upload
curl -X POST "https://your-api-gateway-url/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"

# Test chat
curl -X POST "https://your-api-gateway-url/api/v1/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this document about?"}'

# Test crawler
curl -X POST "https://your-api-gateway-url/api/v1/crawler/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 5}'
```

### Test Preprocessing
```bash
# Upload test PDF to S3
aws s3 cp test.pdf s3://crawlchat-data/uploaded_documents/test-user/test.pdf

# Check ECS logs for processing
aws logs tail /ecs/pdf-preprocessor --follow
```

## 🔄 Updates and Maintenance

### Code Updates
1. **Push to main branch** - triggers automatic deployment
2. **Monitor GitHub Actions** - ensure all builds succeed
3. **Test endpoints** - verify functionality after deployment

### Environment Variable Updates
- **Lambda**: Update via AWS Console or CLI
- **ECS**: Update task definition and redeploy

### Scaling
- **Lambda**: Automatic scaling based on requests
- **ECS**: Manual scaling or auto-scaling based on SQS queue depth

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

3. **Crawler Issues**
   - Check Lambda logs for crawler function
   - Verify web scraping permissions
   - Review target website accessibility

### Debug Commands
```bash
# Check Lambda function status
aws lambda get-function --function-name crawlchat-api-function

# Check ECS service status
aws ecs describe-services --cluster pdf-preprocessing-cluster --services pdf-preprocessor-service

# Check SQS queue status
aws sqs get-queue-attributes --queue-url YOUR_SQS_URL --attribute-names All

# Monitor logs
aws logs tail /aws/lambda/crawlchat-api-function --follow
```

## 📈 Cost Optimization

### Lambda Optimization
- Use provisioned concurrency for consistent performance
- Optimize memory allocation
- Set appropriate timeouts

### ECS Optimization
- Use Spot instances for non-critical processing
- Scale down when not in use
- Optimize container resource allocation

### S3 Optimization
- Use lifecycle policies for old documents
- Compress large files
- Use appropriate storage classes

## 🎯 Next Steps

1. **Deploy all services** using the updated GitHub Actions workflow
2. **Set up API Gateway** to route traffic to your Lambda API
3. **Configure CloudFront** for the frontend
4. **Set up monitoring** and alerting
5. **Test the complete flow** end-to-end
6. **Optimize performance** based on usage patterns

---

**CrawlChat** - Complete document processing and AI chat solution with serverless architecture. 