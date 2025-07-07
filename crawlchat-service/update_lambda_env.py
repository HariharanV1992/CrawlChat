#!/usr/bin/env python3
"""
Script to update Lambda function environment variables
"""

import boto3
import json
import sys

def update_lambda_environment():
    """Update Lambda function environment variables"""
    
    # Configuration
    FUNCTION_NAME = "crawlchat-api-function"  # Replace with your actual function name
    REGION = "ap-south-1"  # Replace with your AWS region
    
    # Environment variables
    environment_variables = {
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
        "CORS_ORIGINS": '["https://crawlchat.site","https://www.crawlchat.site"]',
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
        "SCRAPINGBEE_API_KEY": "",
        "SCRAPINGBEE_OPTIONS": "{}",
        "PROXY_METHOD": "api_endpoint",
        "MIN_FILE_SIZE": "1024",
        "OUTPUT_DIR": "crawled_data",
        "SINGLE_PAGE_MODE": "false",
        "CONNECTION_LIMIT": "100",
        "TCP_CONNECTOR_LIMIT": "50",
        "KEEPALIVE_TIMEOUT": "30",
        "ENABLE_COMPRESSION": "true",
        "TOTAL_TIMEOUT": "1800",
        "PAGE_TIMEOUT": "60",
        "REQUEST_TIMEOOUT": "30",
        "MAX_PAGES_WITHOUT_DOCUMENTS": "20",
        "RELEVANT_KEYWORDS": "stock,market,financial,investor,earnings,revenue,profit,dividend,share,equity,trading,quote,annual,quarterly,report,statement,filing,sec,board,governance,corporate,news,announcement",
        "EXCLUDE_PATTERNS": "login,admin,private,internal,test,dev,temp,cache,session,cookie,tracking,advertisement,ad,banner,social,facebook,twitter,linkedin,youtube,instagram,subscribe,newsletter,contact,about,careers,jobs,support,help,faq",
        "DOCUMENT_EXTENSIONS": ".pdf,.doc,.docx,.xlsx,.xls,.ppt,.pptx,.txt,.csv",
    }
    
    try:
        print(f"Updating Lambda function environment variables...")
        print(f"Function: {FUNCTION_NAME}")
        print(f"Region: {REGION}")
        
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Update function configuration
        response = lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Environment={
                'Variables': environment_variables
            }
        )
        
        print("✅ Successfully updated Lambda function environment variables!")
        print()
        print("Updated variables:")
        for key, value in environment_variables.items():
            if key in ['MONGODB_URI', 'OPENAI_API_KEY', 'SECRET_KEY', 'PROXY_API_KEY']:
                print(f"- {key}: [configured]")
            else:
                print(f"- {key}: {value}")
        
        print()
        print("The function should now have access to all required environment variables.")
        print(f"Function ARN: {response['FunctionArn']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Lambda function configuration: {e}")
        print()
        print("Please check:")
        print("1. AWS credentials are configured properly")
        print("2. Function name is correct:", FUNCTION_NAME)
        print("3. Region is correct:", REGION)
        print("4. You have permission to update the Lambda function")
        return False

if __name__ == "__main__":
    success = update_lambda_environment()
    sys.exit(0 if success else 1) 