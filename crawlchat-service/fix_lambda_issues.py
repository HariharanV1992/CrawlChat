#!/usr/bin/env python3
"""
Comprehensive fix for Lambda issues:
1. Missing ScrapingBee API key
2. Missing settings files
3. Read-only filesystem issues
4. Database connection problems
5. Environment variable configuration
"""

import boto3
import os
import json
import sys

def fix_lambda_environment():
    """Fix all Lambda environment issues."""
    
    print("🔧 Fixing Lambda environment issues...")
    
    # Configuration
    function_name = "crawlchat-crawler-function"
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    try:
        # Get Lambda client
        lambda_client = boto3.client("lambda", region_name=region)
        
        # Get current environment variables
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            current_env = response.get('Environment', {}).get('Variables', {})
            print(f"📋 Current environment variables: {list(current_env.keys())}")
        except Exception as e:
            print(f"❌ Error getting current configuration: {e}")
            current_env = {}
        
        # Define required environment variables
        required_env_vars = {
            # Database
            "MONGODB_URI": "mongodb+srv://your_username:your_password@your_cluster.mongodb.net/crawlchat?retryWrites=true&w=majority",
            
            # API Keys
            "OPENAI_API_KEY": "your_openai_api_key_here",
            "SCRAPINGBEE_API_KEY": "your_scrapingbee_api_key_here",
            
            # Security
            "SECRET_KEY": "your_secret_key_here",
            
            # SQS
            "CRAWLCHAT_SQS_QUEUE": "crawlchat-crawl-tasks",
            
            # AWS
            "AWS_REGION": region,
            
            # Application
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "INFO",
            
            # S3 (optional)
            "S3_BUCKET_NAME": "your-s3-bucket-name",
            
            # CORS
            "CORS_ORIGINS": '["https://api.crawlchat.site", "https://crawlchat.site"]'
        }
        
        # Merge with existing environment variables (don't overwrite if already set)
        updated_env = current_env.copy()
        for key, default_value in required_env_vars.items():
            if key not in updated_env:
                updated_env[key] = default_value
                print(f"➕ Added missing environment variable: {key}")
            else:
                print(f"✅ Environment variable already set: {key}")
        
        # Update Lambda function configuration
        print(f"⚙️  Updating Lambda function configuration...")
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': updated_env
            },
            Timeout=900,  # 15 minutes
            MemorySize=1024
        )
        
        print(f"✅ Lambda function configuration updated successfully!")
        print(f"📋 Function name: {function_name}")
        print(f"📋 Region: {region}")
        
        # Print instructions for manual configuration
        print("\n🔧 Manual Configuration Required:")
        print("1. Update the following environment variables in AWS Lambda Console:")
        print("   - MONGODB_URI: Your MongoDB connection string")
        print("   - OPENAI_API_KEY: Your OpenAI API key")
        print("   - SCRAPINGBEE_API_KEY: Your ScrapingBee API key")
        print("   - SECRET_KEY: A secure random string for JWT tokens")
        print("   - S3_BUCKET_NAME: Your S3 bucket name (optional)")
        
        print("\n2. Or use the update_lambda_env.py script to set them programmatically")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Lambda environment: {e}")
        return False

def create_default_settings_files():
    """Create default settings files that work in Lambda."""
    
    print("\n📄 Creating default settings files...")
    
    # Default stock market settings
    stock_market_settings = {
        "crawler_settings": {
            "max_pages": 5,
            "delay": 2,
            "min_year": 2015,
            "max_year": 2025,
            "max_workers": 3,
            "use_selenium": False,  # Disable in Lambda
            "max_documents": 10,
            "min_file_size_bytes": 1000,
            "selenium_timeout": 30,
            "selenium_wait_time": 3,
            "max_retries": 3,
            "retry_delay": 5
        },
        "proxy_settings": {
            "use_proxy": True,
            "timeout": 30,
            "proxy_api_key": "",
            "proxy_method": "api_endpoint",
            "min_file_size": 1024,
            "output_dir": "/tmp/crawled_data",  # Use /tmp in Lambda
            "single_page_mode": False,
            "connection_limit": 100,
            "tcp_connector_limit": 50,
            "keepalive_timeout": 30,
            "enable_compression": True,
            "total_timeout": 1800,
            "page_timeout": 60,
            "request_timeout": 30,
            "max_pages_without_documents": 20,
            "relevant_keywords": [
                "stock", "market", "financial", "investor", "earnings", "revenue",
                "profit", "dividend", "share", "equity", "trading", "quote",
                "annual", "quarterly", "report", "statement", "filing", "sec",
                "board", "governance", "corporate", "news", "announcement"
            ],
            "exclude_patterns": [
                "login", "admin", "private", "internal", "test", "dev",
                "temp", "cache", "session", "cookie", "tracking", "advertisement",
                "ad", "banner", "social", "facebook", "twitter", "linkedin",
                "youtube", "instagram", "subscribe", "newsletter", "contact",
                "about", "careers", "jobs", "support", "help", "faq"
            ],
            "document_extensions": [".pdf", ".doc", ".docx", ".xlsx", ".xls", ".ppt", ".pptx", ".txt", ".csv"],
            "scrapingbee_api_key": "",
            "scrapingbee_options": {
                "premium_proxy": True,
                "country_code": "us",
                "block_ads": True,
                "block_resources": False
            }
        },
        "keyword_settings": {
            "url_keywords": [],
            "content_keywords": [],
            "snippet_keywords": []
        }
    }
    
    # Default site JS requirements
    site_js_requirements = {
        "www.aboutamazon.com": True,
        "www.business-standard.com": False,
        "www.moneycontrol.com": False,
        "www.ndtv.com": False,
        "www.livemint.com": False,
        "www.financialexpress.com": False,
        "www.economictimes.indiatimes.com": False
    }
    
    # Save settings files to /tmp (writable in Lambda)
    try:
        # Create /tmp directory if it doesn't exist
        os.makedirs("/tmp", exist_ok=True)
        
        # Save stock market settings
        with open("/tmp/stock_market_settings.json", "w") as f:
            json.dump(stock_market_settings, f, indent=2)
        print("✅ Created /tmp/stock_market_settings.json")
        
        # Save site JS requirements
        with open("/tmp/site_js_requirements.json", "w") as f:
            json.dump(site_js_requirements, f, indent=2)
        print("✅ Created /tmp/site_js_requirements.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating settings files: {e}")
        return False

def update_crawler_code_for_lambda():
    """Update crawler code to work better in Lambda environment."""
    
    print("\n🔧 Updating crawler code for Lambda...")
    
    # Update settings manager to use /tmp directory
    settings_manager_path = "crawler-service/src/crawler/settings_manager.py"
    
    try:
        with open(settings_manager_path, "r") as f:
            content = f.read()
        
        # Update default settings file path to use /tmp
        content = content.replace(
            'def __init__(self, settings_file="stock_market_settings.json"):',
            'def __init__(self, settings_file="/tmp/stock_market_settings.json"):'
        )
        
        with open(settings_manager_path, "w") as f:
            f.write(content)
        
        print("✅ Updated settings manager to use /tmp directory")
        
        # Update ScrapingBee manager to use /tmp directory
        scrapingbee_path = "crawler-service/src/crawler/smart_scrapingbee_manager.py"
        
        with open(scrapingbee_path, "r") as f:
            content = f.read()
        
        # Update default file paths to use /tmp
        content = content.replace(
            'def save_site_requirements(self, filename: str = "site_js_requirements.json"):',
            'def save_site_requirements(self, filename: str = "/tmp/site_js_requirements.json"):'
        )
        content = content.replace(
            'def load_site_requirements(self, filename: str = "site_js_requirements.json"):',
            'def load_site_requirements(self, filename: str = "/tmp/site_js_requirements.json"):'
        )
        
        with open(scrapingbee_path, "w") as f:
            f.write(content)
        
        print("✅ Updated ScrapingBee manager to use /tmp directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating crawler code: {e}")
        return False

def main():
    """Main function to fix all Lambda issues."""
    
    print("🚀 Lambda Issues Fix Script")
    print("=" * 50)
    
    # Fix Lambda environment
    if not fix_lambda_environment():
        print("❌ Failed to fix Lambda environment")
        return False
    
    # Create default settings files
    if not create_default_settings_files():
        print("❌ Failed to create settings files")
        return False
    
    # Update crawler code for Lambda
    if not update_crawler_code_for_lambda():
        print("❌ Failed to update crawler code")
        return False
    
    print("\n✅ All Lambda issues fixed!")
    print("\n📋 Next steps:")
    print("1. Set your actual API keys in the Lambda environment variables")
    print("2. Commit and push the code changes")
    print("3. The GitHub Actions workflow will rebuild and deploy")
    print("4. Test the Lambda function")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 