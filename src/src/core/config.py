"""
Configuration management for Stock Market Crawler.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Authentication
    secret_key: str = Field(default="your-secret-key-here", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Crawler Configuration
    max_workers: int = Field(default=10, description="Maximum crawler workers")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_pages: int = Field(default=100, description="Maximum pages to crawl")
    max_documents: int = Field(default=50, description="Maximum documents to download")
    crawler_delay: float = Field(default=1.0, description="Delay between requests")
    
    # Storage Configuration
    storage_type: str = Field(default="local", description="Storage type (local or s3)")
    local_storage_path: str = Field(default_factory=lambda: "/tmp/data" if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else "./data", description="Local storage path")
    s3_access_key: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID", description="S3 access key")
    s3_secret_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY", description="S3 secret key")
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET_NAME", description="S3 bucket name")
    s3_region: str = Field(default="us-east-1", alias="AWS_REGION", description="S3 region")
    
    # AWS S3 Configuration (for compatibility with existing code)
    AWS_S3_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS S3 access key")
    AWS_S3_SECRET_KEY: Optional[str] = Field(default=None, description="AWS S3 secret key")
    AWS_S3_BUCKET: Optional[str] = Field(default=None, description="AWS S3 bucket name")
    AWS_S3_REGION: str = Field(default="us-east-1", description="AWS S3 region")
    
    # AI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI model name")
    ai_max_tokens: int = Field(default=2000, description="Maximum tokens for AI responses")
    ai_temperature: float = Field(default=0.7, description="AI temperature setting")
    
    # Proxy Configuration
    use_proxy: bool = Field(default=False, description="Enable proxy support")
    proxy_api_key: Optional[str] = Field(default=None, description="Proxy API key")
    
    # Logging Configuration
    log_level: str = Field(default="WARNING", description="Logging level")
    log_file: str = Field(default_factory=lambda: "/tmp/app.log" if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else "./logs/app.log", description="Log file path")
    max_log_size_mb: int = Field(default=10, description="Maximum log file size in MB")
    backup_count: int = Field(default=5, description="Number of backup log files to keep")
    
    # CORS Configuration
    cors_allow_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # MongoDB Configuration
    mongodb_uri: str = Field(default="mongodb+srv://hariharanv:welcome030219@financedata.doarsxf.mongodb.net/?retryWrites=true&w=majority&appName=FinanceData", alias="MONGODB_URI", description="MongoDB connection URI")
    mongodb_db: str = Field(default="stock_market_crawler", alias="MONGODB_DB", description="MongoDB database name")
    
    # Email Configuration
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server for sending emails")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default="harito2do@gmail.com", description="SMTP username/email")
    smtp_password: Optional[str] = Field(default="xuls mlzo ygho hviv", description="SMTP password/app password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    email_from: str = Field(default="harito2do@gmail.com", description="From email address")
    app_url: str = Field(default="http://localhost:8000", description="Application URL for confirmation links")
    
    # Database settings
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "stock_market_crawler"
    
    # Redis settings for caching
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Celery settings for background tasks
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # AWS settings
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_account_id: str = ""
    
    # SQS settings
    sqs_queue_url: str = ""
    sqs_dead_letter_queue_url: str = ""
    
    # Lambda settings
    lambda_function_name: str = "stock-market-crawler-background-processor"
    
    # ElastiCache Redis settings
    redis_endpoint: str = ""
    redis_port: int = 6379
    
    # S3 settings
    s3_bucket_name: str = "stock-market-crawler-documents"
    
    # OpenAI settings
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return Path(self.local_storage_path)
    
    @property
    def effective_storage_type(self) -> str:
        """Get effective storage type based on available credentials."""
        if (self.s3_access_key and 
            self.s3_secret_key and 
            self.s3_bucket):
            return "s3"
        return self.storage_type
    
    def setup_directories(self):
        """Create necessary directories."""
        # In Lambda, only create /tmp directories
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            directories = [
                self.data_dir,
                self.data_dir / "crawled",
                self.data_dir / "processed", 
                self.data_dir / "uploads",
                self.data_dir / "temp",
            ]
        else:
            directories = [
                self.data_dir,
                self.data_dir / "crawled",
                self.data_dir / "processed", 
                self.data_dir / "uploads",
                self.data_dir / "temp",
                Path("logs"),
                Path("tests"),
                Path("docs")
            ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# Global configuration instance
config = Settings() 

def get_config() -> Dict[str, Any]:
    """Get configuration as dictionary."""
    return {
        "mongodb": {
            "url": config.mongodb_url,
            "database": config.mongodb_database
        },
        "redis": {
            "url": config.redis_url,
            "db": config.redis_db
        },
        "celery": {
            "broker_url": config.celery_broker_url,
            "result_backend": config.celery_result_backend
        },
        "aws": {
            "access_key_id": config.aws_access_key_id,
            "secret_access_key": config.aws_secret_access_key,
            "region": config.aws_region,
            "s3_bucket": config.s3_bucket_name
        },
        "openai": {
            "api_key": config.openai_api_key,
            "model": config.openai_model,
            "max_tokens": config.openai_max_tokens,
            "temperature": config.openai_temperature
        },
        "app": {
            "debug": config.debug,
            "log_level": config.log_level
        }
    }

# If you need the dict version elsewhere:
config_dict = get_config() 