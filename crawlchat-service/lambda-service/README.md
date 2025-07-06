# CrawlChat Lambda Service

AWS Lambda-based API service for PDF processing, AI chat, and vector store integration.

## 🏗️ Architecture

```
User Request → API Gateway → Lambda Function → AWS Services
                                    ↓
                            Textract + Vector Store + OpenAI
```

## 📁 File Structure

```
lambda-service/
├── README.md           # This file
├── main.py            # Main Lambda application
├── lambda_handler.py  # Lambda entry point
├── Dockerfile         # Lambda container build
├── requirements.txt   # Lambda dependencies
└── src/               # Source code
    ├── api/           # API endpoints
    ├── core/          # Core configuration
    ├── services/      # Business logic
    └── utils/         # Utilities
```

## 🚀 Deployment

### Prerequisites
- AWS CLI configured
- Docker installed
- Access to ECR, Lambda, API Gateway services

### Manual Deployment

1. **Build Docker Image:**
   ```bash
   docker build -t crawlchat-lambda .
   ```

2. **Tag and Push to ECR:**
   ```bash
   aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 169164939839.dkr.ecr.ap-south-1.amazonaws.com
   docker tag crawlchat-lambda:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
   docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
   ```

3. **Update Lambda Function:**
   ```bash
   aws lambda update-function-code --function-name crawlchat-api-function --image-uri 169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-lambda:latest
   ```

### GitHub Actions Deployment
The Lambda service is automatically deployed via GitHub Actions when changes are pushed to the main branch.

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for AI responses
- `TEXTRACT_REGION`: AWS Textract region (ap-south-1)
- `S3_BUCKET`: S3 bucket name (crawlchat-data)
- `VECTOR_STORE_URL`: Vector store connection string
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### Lambda Settings
- **Runtime**: Container image
- **Memory**: 1024 MB (adjustable)
- **Timeout**: 30 seconds
- **Architecture**: x86_64

## 📊 Monitoring

### CloudWatch Logs
- **Log Group**: `/aws/lambda/crawlchat-api-function`
- **Console**: [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups/log-group/aws/lambda/crawlchat-api-function)

### Lambda Metrics
- **Console**: [Lambda Console](https://console.aws.amazon.com/lambda/home?region=ap-south-1#/functions/crawlchat-api-function)
- **Metrics**: Invocation count, duration, errors, throttles

## 🔍 Testing

### Local Testing
```bash
# Test lambda handler
python -c "import lambda_handler; print(lambda_handler.lambda_handler({}, {}))"

# Test with sample event
python -c "import lambda_handler; import json; event=json.load(open('test_event.json')); print(lambda_handler.lambda_handler(event, {}))"
```

### API Testing
```bash
# Test chat endpoint
curl -X POST https://your-api-gateway-url/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test-user"}'
```

## 🛠️ Troubleshooting

### Common Issues

1. **Cold Start Delays**
   - Use provisioned concurrency
   - Optimize container size
   - Review dependency loading

2. **Memory Issues**
   - Increase memory allocation
   - Optimize code for memory usage
   - Review large file processing

3. **Timeout Errors**
   - Increase timeout setting
   - Optimize Textract processing
   - Review external API calls

### Log Analysis
```bash
# View recent logs
aws logs tail /aws/lambda/crawlchat-api-function --follow

# Search for errors
aws logs filter-log-events --log-group-name /aws/lambda/crawlchat-api-function --filter-pattern "ERROR"
```

## 💰 Cost Optimization

### Optimization Strategies
1. **Memory Tuning**: Find optimal memory allocation
2. **Provisioned Concurrency**: For consistent performance
3. **Reserved Concurrency**: Control concurrent executions
4. **Code Optimization**: Reduce execution time

### Cost Monitoring
- **AWS Cost Explorer**: Monitor Lambda costs
- **CloudWatch Metrics**: Track resource usage
- **Billing Alerts**: Set up cost notifications

## 🔐 Security

### IAM Permissions
- **Textract**: Document analysis
- **S3**: Read/write access to crawlchat-data bucket
- **Vector Store**: Database access
- **CloudWatch**: Logging

### Data Protection
- **Encryption**: Data encrypted in transit and at rest
- **API Keys**: Stored as environment variables
- **VPC**: Runs in secure VPC configuration

## 📈 Scaling

### Automatic Scaling
- **Concurrent Executions**: Scales based on request volume
- **Memory Allocation**: Adjustable per function
- **Timeout**: Configurable per function

### Manual Scaling
```bash
# Update memory allocation
aws lambda update-function-configuration --function-name crawlchat-api-function --memory-size 2048

# Update timeout
aws lambda update-function-configuration --function-name crawlchat-api-function --timeout 60
```

## 🔄 Updates

### Code Updates
1. **Build new image**
2. **Push to ECR**
3. **Update Lambda function**

### Configuration Updates
```bash
# Update environment variables
aws lambda update-function-configuration --function-name crawlchat-api-function --environment Variables='{"KEY":"VALUE"}'

# Update timeout
aws lambda update-function-configuration --function-name crawlchat-api-function --timeout 30
```

---

**CrawlChat Lambda Service** - Serverless API for PDF processing and AI chat. 