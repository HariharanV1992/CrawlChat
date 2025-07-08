#!/usr/bin/env python3
"""
Set provided environment variables for Lambda function.
"""

import boto3
import os
import sys

def set_lambda_environment():
    """Set provided environment variables for Lambda."""
    
    print("🔧 Setting Lambda environment variables...")
    
    # Configuration
    function_name = "crawlchat-crawler-function"
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    # Get current environment variables
    lambda_client = boto3.client("lambda", region_name=region)
    
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        current_env = response.get('Environment', {}).get('Variables', {})
    except Exception as e:
        print(f"❌ Error getting current configuration: {e}")
        current_env = {}
    
    # Provided environment variables (excluding AWS reserved keys)
    provided_vars = {
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "ALGORITHM": "HS256",
        "BATCH_SIZE": "10",
        "COLLECTION_PREFIX": "crawler",
        "CORS_ORIGINS": '["https://crawlchat.site","https://www.crawlchat.site"]',
        "CRAWLER_DELAY": "1.0",
        "CRAWLER_MAX_DOCUMENTS": "20",
        "CRAWLER_MAX_PAGES": "100",
        "CRAWLER_MAX_WORKERS": "10",
        "CRAWLER_TIMEOUT": "30",
        "CRAWLER_USER_AGENT": "StockMarketCrawler/1.0",
        "DB_NAME": "stock_market_crawler",
        "ENVIRONMENT": "production",
        "LOG_FILE": "/var/log/crawlchat/app.log",
        "LOG_LEVEL": "INFO",
        "MAX_FILE_SIZE_MB": "50",
        "MONGODB_URI": "your_mongodb_uri_here",
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MAX_TOKENS": "4000",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENAI_TEMPERATURE": "0.1",
        "PROCESSING_TIMEOUT": "300",
        "PROXY_API_KEY": "YOUR_PROXY_API_KEY_HERE",
        "S3_BUCKET": "crawlchat-data",
        "S3_CRAWLED_DATA_PREFIX": "crawled_data/",
        "S3_DOCUMENTS_PREFIX": "documents/",
        "SCRAPERAPI_BASE": "http://api.scraperapi.com/",
        "SCRAPINGBEE_API_KEY": "your_scrapingbee_api_key_here",
        "SECRET_KEY": "eUEuO5za52XF7tUxKxChoVOvPYSeMtNouGU8Yi4SxLQ",
        "USE_PROXY": "true"
    }
    
    # Merge with existing environment variables
    updated_env = current_env.copy()
    for key, value in provided_vars.items():
        updated_env[key] = value
        print(f"➕ Set: {key}")
    
    # Update Lambda function
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment={
            'Variables': updated_env
        }
    )
    
    print(f"\n✅ Lambda environment updated!")
    print(f"\n🔧 Manual steps required:")
    print("1. Go to AWS Lambda Console if you want to verify.")
    print("2. Select function: crawlchat-crawler-function")
    print("3. Go to Configuration > Environment variables")
    print("4. All provided values should be set.")
    
    return True

if __name__ == "__main__":
    set_lambda_environment() 