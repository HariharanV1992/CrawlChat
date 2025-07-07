#!/bin/bash

# Script to update Lambda function environment variables
# Make sure to replace YOUR_FUNCTION_NAME with your actual Lambda function name

FUNCTION_NAME="crawlchat-api-function"  # Replace with your actual function name
REGION="ap-south-1"  # Replace with your AWS region

echo "Updating Lambda function environment variables..."

# Create environment variables JSON
ENV_VARS='{
  "Variables": {
    "ENVIRONMENT": "production",
    "S3_BUCKET": "crawlchat-data",
    "MONGODB_URI": "YOUR_MONGODB_URI_HERE",
    "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
    "DB_NAME": "stock_market_crawler",
    "COLLECTION_PREFIX": "crawler",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_MAX_TOKENS": "4000",
    "OPENAI_TEMPERATURE": "0.1",
    "S3_DOCUMENTS_PREFIX": "documents/",
    "S3_CRAWLED_DATA_PREFIX": "crawled_data/",
    "SECRET_KEY": "YOUR_SECRET_KEY_HERE",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "CORS_ORIGINS": "[\"https://crawlchat.site\",\"https://www.crawlchat.site\"]",
    "CRAWLER_MAX_WORKERS": "10",
    "CRAWLER_TIMEOUT": "30",
    "CRAWLER_DELAY": "1.0",
    "CRAWLER_MAX_PAGES": "100",
    "CRAWLER_MAX_DOCUMENTS": "20",
    "CRAWLER_USER_AGENT": "StockMarketCrawler/1.0",
    "MAX_FILE_SIZE_MB": "50",
    "PROCESSING_TIMEOUT": "300",
    "BATCH_SIZE": "10",
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "/var/log/crawlchat/app.log",
    "PROXY_API_KEY": "YOUR_PROXY_API_KEY_HERE",
    "USE_PROXY": "true",
    "SCRAPERAPI_BASE": "http://api.scraperapi.com/"
  }
}'

# Update Lambda function configuration
echo "Updating function: $FUNCTION_NAME in region: $REGION"

aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --environment "$ENV_VARS"

if [ $? -eq 0 ]; then
    echo "✅ Successfully updated Lambda function environment variables!"
    echo ""
    echo "Updated variables:"
    echo "- ENVIRONMENT: production"
    echo "- S3_BUCKET: crawlchat-data"
    echo "- MONGODB_URI: [configured]"
    echo "- OPENAI_API_KEY: [configured]"
    echo "- DB_NAME: stock_market_crawler"
    echo "- COLLECTION_PREFIX: crawler"
    echo "- OPENAI_MODEL: gpt-4o-mini"
    echo "- OPENAI_MAX_TOKENS: 4000"
    echo "- OPENAI_TEMPERATURE: 0.1"
    echo "- And all other configuration variables..."
    echo ""
    echo "The function should now have access to all required environment variables."
else
    echo "❌ Failed to update Lambda function configuration"
    echo "Please check:"
    echo "1. AWS CLI is configured with proper credentials"
    echo "2. Function name is correct: $FUNCTION_NAME"
    echo "3. Region is correct: $REGION"
    echo "4. You have permission to update the Lambda function"
fi 