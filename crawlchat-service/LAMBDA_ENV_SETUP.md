# Lambda Environment Variables Setup

This directory contains scripts to update the Lambda function environment variables with all the required configuration.

## Prerequisites

1. **AWS CLI configured** with proper credentials
2. **Python 3.x** (for Python script)
3. **boto3** library (for Python script): `pip install boto3`

## Available Scripts

### 1. Bash Script (`update_lambda_env.sh`)
```bash
./update_lambda_env.sh
```

### 2. Python Script (`update_lambda_env.py`)
```bash
python3 update_lambda_env.py
```

## Configuration

Before running the scripts, make sure to update the following variables in the script files:

- `FUNCTION_NAME`: Your actual Lambda function name (default: "crawlchat-api-function")
- `REGION`: Your AWS region (default: "us-east-1")

## Environment Variables Being Set

The scripts will configure the following environment variables:

### Core Configuration
- `ENVIRONMENT`: production
- `S3_BUCKET`: crawlchat-data
- `MONGODB_URI`: MongoDB connection string
- `DB_NAME`: stock_market_crawler
- `COLLECTION_PREFIX`: crawler

### OpenAI Configuration
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: gpt-4o-mini
- `OPENAI_MAX_TOKENS`: 4000
- `OPENAI_TEMPERATURE`: 0.1

### Authentication
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30

### S3 Configuration
- `S3_DOCUMENTS_PREFIX`: documents/
- `S3_CRAWLED_DATA_PREFIX`: crawled_data/

### CORS Configuration
- `CORS_ORIGINS`: ["https://crawlchat.site","https://www.crawlchat.site"]

### Crawler Configuration
- `CRAWLER_MAX_WORKERS`: 10
- `CRAWLER_TIMEOUT`: 30
- `CRAWLER_DELAY`: 1.0
- `CRAWLER_MAX_PAGES`: 100
- `CRAWLER_MAX_DOCUMENTS`: 20
- `CRAWLER_USER_AGENT`: StockMarketCrawler/1.0

### Processing Configuration
- `MAX_FILE_SIZE_MB`: 50
- `PROCESSING_TIMEOUT`: 300
- `BATCH_SIZE`: 10

### Logging Configuration
- `LOG_LEVEL`: INFO
- `LOG_FILE`: /var/log/crawlchat/app.log

### Proxy Configuration
- `PROXY_API_KEY`: Your proxy API key
- `USE_PROXY`: true
- `SCRAPERAPI_BASE`: http://api.scraperapi.com/

## Usage

1. **Update the function name and region** in the script if needed
2. **Run the script**:
   ```bash
   # Using bash script
   ./update_lambda_env.sh
   
   # Or using Python script
   python3 update_lambda_env.py
   ```

3. **Verify the update** by checking the Lambda console or running:
   ```bash
   aws lambda get-function-configuration --function-name YOUR_FUNCTION_NAME
   ```

## Troubleshooting

### Common Issues

1. **AWS credentials not configured**
   ```bash
   aws configure
   ```

2. **Function not found**
   - Check the function name in the script
   - Verify the function exists in the specified region

3. **Permission denied**
   - Ensure your AWS user/role has Lambda update permissions
   - Required permissions: `lambda:UpdateFunctionConfiguration`

4. **Region mismatch**
   - Update the `REGION` variable in the script to match your function's region

### Verification

After running the script, you can verify the environment variables are set correctly:

```bash
aws lambda get-function-configuration \
  --function-name YOUR_FUNCTION_NAME \
  --query 'Environment.Variables'
```

## Security Notes

- The scripts contain sensitive information (API keys, database URIs)
- Consider using AWS Secrets Manager or Parameter Store for production
- Rotate API keys regularly
- Use IAM roles with minimal required permissions

## Next Steps

After updating the environment variables:

1. **Test the function** by making a request to your API
2. **Check the logs** for any remaining issues
3. **Monitor the function** performance and error rates
4. **Update the frontend** if needed to use the new configuration 