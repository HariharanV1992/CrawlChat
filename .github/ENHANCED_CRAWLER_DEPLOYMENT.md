# Enhanced Crawler Deployment Guide

## Overview

This guide explains how to deploy the enhanced crawler functionality with `max_doc_count` support to AWS Lambda using GitHub Actions.

## 🚀 Quick Deployment

### 1. Automatic Deployment (Recommended)

The enhanced crawler will be automatically deployed when you push to the `main` branch:

```bash
git add .
git commit -m "Add enhanced crawler with max_doc_count support"
git push origin main
```

### 2. Manual Deployment

You can also trigger deployment manually:

1. Go to **Actions** tab in GitHub
2. Select **"Deploy Complete CrawlChat Service"**
3. Click **"Run workflow"**
4. Configure options:
   - ✅ Deploy Infrastructure
   - ✅ Deploy Lambda Functions
   - ❌ Deploy UI (optional)

## 📁 File Structure

```
crawlchat-service/
├── lambda-service/           # Main API Lambda
│   ├── Dockerfile
│   ├── lambda_handler.py
│   ├── main.py
│   └── src/crawler/
│       └── enhanced_crawler_service.py  # ✅ Enhanced crawler
├── crawler-service/          # Dedicated Crawler Lambda
│   ├── Dockerfile
│   ├── lambda_handler.py
│   ├── requirements.txt
│   └── src/crawler/
│       └── enhanced_crawler_service.py  # ✅ Enhanced crawler
└── crawlchat-crawler/        # Source crawler modules
    └── src/crawler/
        ├── advanced_crawler.py
        ├── link_extractor.py
        └── ...
```

## 🔧 Configuration

### Environment Variables

The following environment variables are automatically configured:

```yaml
SCRAPINGBEE_API_KEY: "{{resolve:secretsmanager:crawlchat/scrapingbee-api-key:SecretString:api_key}}"
MONGODB_URI: "{{resolve:secretsmanager:crawlchat/mongodb-uri:SecretString:uri}}"
OPENAI_API_KEY: "{{resolve:secretsmanager:crawlchat/openai-api-key:SecretString:api_key}}"
SECRET_KEY: "{{resolve:secretsmanager:crawlchat/secret-key:SecretString:key}}"
```

### Lambda Configuration

- **Memory**: 1024 MB
- **Timeout**: 900 seconds (15 minutes)
- **Architecture**: x86_64
- **Runtime**: Python 3.10

## 🧪 Testing

### Pre-deployment Testing

Run the enhanced crawler test workflow:

1. Go to **Actions** → **"Test Enhanced Crawler"**
2. Click **"Run workflow"**

This will test:
- ✅ Enhanced crawler service imports
- ✅ Lambda handler functionality
- ✅ Docker builds
- ✅ File validation

### Post-deployment Testing

After deployment, test the enhanced crawler:

```bash
# Test single page crawl
aws lambda invoke \
  --function-name crawlchat-crawler-function \
  --payload '{"url": "https://example.com", "max_doc_count": 1}' \
  --region ap-south-1 \
  response.json

# Test multi-page crawl
aws lambda invoke \
  --function-name crawlchat-crawler-function \
  --payload '{"url": "https://www.irs.gov/forms-pubs", "max_doc_count": 3}' \
  --region ap-south-1 \
  response2.json
```

## 📊 Enhanced Crawler Features

### 1. Max Document Count Support

```json
{
  "url": "https://example.com",
  "max_doc_count": 3
}
```

**Behavior:**
- `max_doc_count=1`: Crawl only the current page
- `max_doc_count>1`: Crawl current page + sub-pages + documents
- Stop when max document count is reached

### 2. Document Extraction

- **HTML Pages**: Extract title and content
- **PDF Documents**: Download and extract text
- **Excel/Word Files**: Process and extract content
- **Structured Output**: JSON format instead of raw HTML

### 3. Recursive Crawling

- **Sub-page Discovery**: Using `LinkExtractor`
- **Document Links**: Extract from multiple sources
- **Domain Filtering**: Only crawl same domain
- **Duplicate Prevention**: Track visited URLs

## 🔍 Monitoring

### CloudWatch Logs

Monitor crawler performance:

```bash
# View recent logs
aws logs tail /aws/lambda/crawlchat-crawler-function --follow

# View specific log stream
aws logs describe-log-streams \
  --log-group-name /aws/lambda/crawlchat-crawler-function \
  --order-by LastEventTime \
  --descending
```

### Key Metrics

- **Execution Time**: Target < 5 minutes
- **Memory Usage**: Target < 512 MB
- **Success Rate**: Target > 95%
- **Document Count**: Respects `max_doc_count`

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check if enhanced crawler service exists
   ls -la crawlchat-service/crawler-service/src/crawler/enhanced_crawler_service.py
   ```

2. **Docker Build Failures**
   ```bash
   # Test Docker build locally
   cd crawlchat-service
   docker build -f crawler-service/Dockerfile -t test-crawler .
   ```

3. **Lambda Timeout**
   - Increase timeout in CloudFormation template
   - Optimize crawler logic for faster execution

4. **Memory Issues**
   - Increase memory allocation
   - Implement pagination for large documents

### Debug Commands

```bash
# Test enhanced crawler locally
cd crawlchat-service/crawler-service
python -c "
import sys
sys.path.insert(0, 'src')
from crawler.enhanced_crawler_service import EnhancedCrawlerService
service = EnhancedCrawlerService('your-api-key')
result = service.crawl_with_max_docs('https://example.com', 1)
print(result)
"

# Test Lambda handler locally
python -c "
from lambda_handler import lambda_handler
event = {'url': 'https://example.com', 'max_doc_count': 1}
result = lambda_handler(event, None)
print(result)
"
```

## 📈 Performance Optimization

### Lambda Optimization

1. **Cold Start Reduction**
   - Use provisioned concurrency
   - Optimize imports (lazy loading)

2. **Memory Optimization**
   - Stream large documents
   - Implement cleanup in handlers

3. **Timeout Management**
   - Set appropriate timeouts
   - Implement progress tracking

### Cost Optimization

1. **ScrapingBee Credits**
   - Monitor usage in ScrapingBee dashboard
   - Implement caching for repeated requests

2. **Lambda Costs**
   - Optimize memory allocation
   - Use appropriate timeout values

## 🔐 Security

### API Key Management

- Store API keys in AWS Secrets Manager
- Rotate keys regularly
- Monitor usage for anomalies

### Access Control

- Use IAM roles with minimal permissions
- Implement request validation
- Monitor Lambda execution logs

## 📞 Support

For deployment issues:

1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Test locally with provided scripts
4. Verify environment variables

## 🎯 Success Criteria

Deployment is successful when:

- ✅ Enhanced crawler service builds without errors
- ✅ Lambda functions deploy successfully
- ✅ Test workflows pass
- ✅ Crawler respects `max_doc_count` parameter
- ✅ Documents are extracted in structured JSON format
- ✅ Performance meets requirements (< 5 min execution time)

---

**Ready to deploy?** Push to `main` branch or trigger manual deployment! 🚀 