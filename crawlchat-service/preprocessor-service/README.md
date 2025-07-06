# CrawlChat PDF Preprocessor Service

ECS Fargate-based PDF preprocessing service that normalizes problematic PDFs for AWS Textract processing.

## 🏗️ Architecture

```
S3 Upload → S3 Event → SQS Queue → ECS Fargate Task → Normalized Output
    ↓           ↓           ↓           ↓              ↓
PDF/Image   Notification  Message   Processing    S3 Storage
```

## 📁 File Structure

```
preprocessor-service/
├── README.md                 # This file
├── preprocessing_service.py  # Main PDF processing logic
├── Dockerfile               # Container build instructions
├── requirements.txt         # Python dependencies
├── deploy.sh               # Deployment automation script
├── ecs-task-definition.json # ECS Fargate task definition
├── s3-notification.json    # S3 event notification config
├── sqs-policy.json         # SQS access policy
└── iam-policies.json       # IAM policies (reference)
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed and running
- Access to ECR, ECS, S3, SQS, and IAM services

### Deployment

1. **Navigate to the service directory:**
   ```bash
   cd preprocessor-service
   ```

2. **Make deployment script executable:**
   ```bash
   chmod +x deploy.sh
   ```

3. **Deploy the service:**
   ```bash
   ./deploy.sh
   ```

### Configuration

The deployment script automatically configures:
- **ECR Repository**: `pdf-preprocessor`
- **ECS Cluster**: `pdf-preprocessing-cluster`
- **ECS Service**: `pdf-preprocessor-service`
- **SQS Queue**: `pdf-preprocess-queue`
- **S3 Bucket**: `crawlchat-data`
- **CloudWatch Logs**: `/ecs/pdf-preprocessor`

## 🔧 How It Works

### 1. PDF Upload Trigger
When a PDF is uploaded to `s3://crawlchat-data/uploaded_documents/{user_id}/{filename}.pdf`:
- S3 sends an event to the SQS queue
- ECS Fargate task picks up the message

### 2. PDF Processing
The preprocessor:
- Downloads the PDF from S3
- Attempts to extract text using multiple libraries (PyPDF2, PDFMiner, PyMuPDF)
- If text extraction fails, converts PDF pages to PNG images
- Uploads normalized results to `s3://crawlchat-data/normalized-documents/{user_id}/`

### 3. Output
- **Text-based PDFs**: Uploaded as-is to normalized-documents
- **Image-based PDFs**: Converted to PNG images (one per page)
- **Processing metadata**: Logged to CloudWatch

## 📊 Monitoring

### ECS Service
- **Console**: [ECS Service](https://console.aws.amazon.com/ecs/home?region=ap-south-1#/clusters/pdf-preprocessing-cluster/services/pdf-preprocessor-service)
- **Metrics**: Task count, CPU/Memory usage, health status

### CloudWatch Logs
- **Log Group**: `/ecs/pdf-preprocessor`
- **Console**: [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups/log-group/ecs/pdf-preprocessor)

### SQS Queue
- **Console**: [SQS Queue](https://console.aws.amazon.com/sqs/home?region=ap-south-1#/queues/https%3A%2F%2Fsqs.ap-south-1.amazonaws.com%2F169164939839%2Fpdf-preprocess-queue)
- **Metrics**: Message count, processing time

## 🔍 Testing

### Manual Test
1. Upload a PDF to `s3://crawlchat-data/uploaded_documents/test-user/test.pdf`
2. Check ECS service logs for processing activity
3. Verify output in `s3://crawlchat-data/normalized-documents/test-user/`

### Expected Behavior
- **Valid PDFs**: Processed and normalized
- **Corrupted PDFs**: Error logged, message returned to queue
- **Large PDFs**: Processed with timeout protection

## 🛠️ Troubleshooting

### Common Issues

1. **ECS Task Not Starting**
   - Check IAM roles and permissions
   - Verify ECR image exists and is accessible
   - Check CloudWatch logs for startup errors

2. **SQS Messages Not Processing**
   - Verify S3 event notification is configured
   - Check SQS queue policy allows S3 access
   - Monitor ECS service desired count

3. **PDF Processing Failures**
   - Check CloudWatch logs for specific errors
   - Verify PDF is not corrupted or password-protected
   - Check S3 permissions for read/write access

### Log Analysis
```bash
# View recent logs
aws logs tail /ecs/pdf-preprocessor --follow

# Check specific error patterns
aws logs filter-log-events --log-group-name /ecs/pdf-preprocessor --filter-pattern "ERROR"
```

## 💰 Cost Optimization

### Current Setup
- **ECS Fargate**: Pay per vCPU-second and memory-second
- **S3**: Pay for storage and requests
- **SQS**: Pay per message (very low cost)

### Optimization Options
1. **Set desired count to 0** and use EventBridge to trigger tasks only when SQS has messages
2. **Use Spot instances** for non-critical processing
3. **Implement batch processing** for multiple PDFs

## 🔐 Security

### IAM Roles
- **Task Execution Role**: Pulls images from ECR, writes logs
- **Task Role**: Reads from S3, writes to S3, processes SQS messages

### Network Security
- **VPC**: Uses default VPC with public subnets
- **Security Groups**: Uses default security group
- **Encryption**: S3 objects encrypted at rest

## 📈 Scaling

### Automatic Scaling
- **ECS Service**: Can scale based on SQS queue depth
- **Fargate**: Automatically handles underlying infrastructure

### Manual Scaling
```bash
# Scale service
aws ecs update-service --cluster pdf-preprocessing-cluster --service pdf-preprocessor-service --desired-count 2

# Check current scaling
aws ecs describe-services --cluster pdf-preprocessing-cluster --services pdf-preprocessor-service
```

## 🔄 Updates

### Update Service
1. **Build new image:**
   ```bash
   docker build -t pdf-preprocessor .
   docker tag pdf-preprocessor:latest 169164939839.dkr.ecr.ap-south-1.amazonaws.com/pdf-preprocessor:latest
   docker push 169164939839.dkr.ecr.ap-south-1.amazonaws.com/pdf-preprocessor:latest
   ```

2. **Update ECS service:**
   ```bash
   aws ecs update-service --cluster pdf-preprocessing-cluster --service pdf-preprocessor-service --force-new-deployment
   ```

## 📞 Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify AWS service status
3. Review this README for troubleshooting steps

---

**CrawlChat PDF Preprocessor Service** - Production-ready, serverless, auto-scaling PDF processing pipeline. 