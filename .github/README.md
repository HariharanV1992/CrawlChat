# CrawlChat Deployment Automation

This directory contains GitHub Actions workflows for automated deployment of the complete CrawlChat service to AWS.

## 🚀 Available Workflows

### 1. **Deploy Complete Service** (`deploy-complete.yml`)
**Triggers:** Push to `main` branch or manual dispatch
**Purpose:** Full deployment including infrastructure, Lambda functions, and environment setup

**Features:**
- ✅ Validates CloudFormation templates
- ✅ Builds and pushes Docker images to ECR
- ✅ Deploys complete infrastructure stack
- ✅ Updates Lambda functions with new images
- ✅ Configures environment variables
- ✅ Runs comprehensive tests
- ✅ Provides deployment summary

**Manual Inputs:**
- `deploy_infrastructure`: Deploy/Update Infrastructure (default: true)
- `deploy_lambda`: Deploy Lambda Functions (default: true)
- `deploy_ui`: Deploy UI (default: false)

### 2. **Deploy Infrastructure Only** (`deploy-infrastructure.yml`)
**Triggers:** Push to `infra/**` paths or manual dispatch
**Purpose:** Deploy/update only the AWS infrastructure

**Features:**
- ✅ Validates CloudFormation templates
- ✅ Creates/updates S3 bucket with lifecycle policies
- ✅ Deploys CloudFormation stack
- ✅ Shows deployment outputs

**Manual Inputs:**
- `stack_name`: CloudFormation Stack Name (default: crawlchat-complete-stack)
- `template_file`: Template file to deploy (default: infra/crawlchat-complete-infrastructure.yml)

### 3. **Deploy Lambda Functions Only** (`deploy-lambda-only.yml`)
**Triggers:** Push to Lambda service paths or manual dispatch
**Purpose:** Deploy only Lambda functions without infrastructure changes

**Features:**
- ✅ Builds and pushes Docker images
- ✅ Updates Lambda functions
- ✅ Tests updated functions
- ✅ Supports selective function deployment

**Manual Inputs:**
- `function_name`: Lambda Function Name (leave empty for all)
- `force_rebuild`: Force rebuild Docker images (default: false)

### 4. **Test and Validate Deployment** (`test-and-validate.yml`)
**Triggers:** Push to test paths, manual dispatch, or scheduled (every 6 hours)
**Purpose:** Validate deployment health without making changes

**Features:**
- ✅ Validates infrastructure status
- ✅ Tests API endpoints
- ✅ Tests crawler functionality
- ✅ Checks S3 caching
- ✅ Generates comprehensive reports

**Manual Inputs:**
- `test_type`: Type of tests to run (all, api, crawler, infrastructure)

## 🔧 Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

### AWS Credentials
```bash
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### API Keys
```bash
SCRAPINGBEE_API_KEY=your-scrapingbee-api-key
OPENAI_API_KEY=your-openai-api-key
PROXY_API_KEY=your-proxy-api-key
```

### Database & Configuration
```bash
MONGODB_URI=your-mongodb-connection-string
SECRET_KEY=your-jwt-secret-key
CERTIFICATE_ARN=arn:aws:acm:region:account:certificate/certificate-id
```

## 📋 Deployment Process

### Initial Setup (First Time)
1. **Set up GitHub Secrets** with all required credentials
2. **Run Infrastructure Deployment** manually:
   ```bash
   # Go to Actions → Deploy Infrastructure Only → Run workflow
   ```
3. **Deploy Complete Service**:
   ```bash
   # Go to Actions → Deploy Complete Service → Run workflow
   ```

### Regular Deployments
- **Automatic**: Push to `main` branch triggers complete deployment
- **Selective**: Use specific workflows for targeted updates
- **Testing**: Scheduled validation runs every 6 hours

## 🏗️ Infrastructure Components

### CloudFormation Stack (`crawlchat-complete-stack`)
- **API Gateway**: REST API with custom domain
- **Lambda Functions**: API and Crawler functions
- **IAM Roles**: Proper permissions for all services
- **S3 Bucket**: Data storage with lifecycle policies
- **Route53**: DNS configuration (if hosted zone exists)

### Lambda Functions
- **`crawlchat-api-function`**: Main API with FastAPI
- **`crawlchat-crawler-function`**: Dedicated crawler worker

### ECR Repositories
- **`crawlchat-api-function`**: API Lambda container images
- **`crawlchat-crawler-function`**: Crawler Lambda container images

## 🔍 Monitoring & Validation

### Automated Tests
- **Infrastructure Health**: CloudFormation stack status
- **Lambda Functions**: Function state and configuration
- **API Endpoints**: Health checks and basic functionality
- **S3 Integration**: Bucket access and caching
- **Crawler Functionality**: Basic crawling tests

### Manual Testing
```bash
# Test API health
curl https://api.crawlchat.site/health

# Test crawler
curl -X POST https://api.crawlchat.site/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 🚨 Troubleshooting

### Common Issues

1. **CloudFormation Stack Fails**
   - Check IAM permissions
   - Verify template syntax
   - Review CloudWatch logs

2. **Lambda Function Errors**
   - Check environment variables
   - Verify ECR image exists
   - Review function logs

3. **S3 Access Issues**
   - Verify bucket permissions
   - Check IAM role policies
   - Ensure bucket exists

### Debug Commands
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name crawlchat-complete-stack

# Check Lambda function
aws lambda get-function --function-name crawlchat-api-function

# Check S3 bucket
aws s3 ls s3://crawlchat-data/

# View CloudWatch logs
aws logs tail /aws/lambda/crawlchat-api-function --follow
```

## 📊 Cost Optimization

### S3 Caching Benefits
- **Persistent Cache**: Survives Lambda cold starts
- **Shared Access**: Multiple functions share cache
- **Cost Effective**: Minimal S3 storage costs
- **Automatic Cleanup**: Lifecycle policies remove old versions

### Lambda Optimization
- **Container Images**: Faster cold starts
- **Memory Allocation**: Optimized for performance
- **Timeout Settings**: Balanced for cost/performance

## 🔄 Workflow Dependencies

```
deploy-complete.yml
├── validate (template validation)
├── build-and-push (Docker images)
├── deploy-infrastructure (CloudFormation)
├── deploy-lambda-functions (Lambda updates)
└── test-deployment (validation tests)

deploy-infrastructure.yml
└── deploy (infrastructure only)

deploy-lambda-only.yml
└── build-and-deploy (Lambda only)

test-and-validate.yml
├── validate-infrastructure
├── test-api
├── test-crawler
└── generate-report
```

## 📈 Best Practices

1. **Use Selective Deployments**: Deploy only what changed
2. **Monitor Costs**: Check AWS billing regularly
3. **Test Before Deploy**: Use validation workflows
4. **Keep Secrets Updated**: Rotate API keys regularly
5. **Monitor Logs**: Check CloudWatch for issues
6. **Backup Data**: S3 versioning provides data protection

## 🆘 Support

For deployment issues:
1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Validate AWS credentials
4. Test individual components
5. Use troubleshooting commands above 