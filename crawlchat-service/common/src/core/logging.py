"""
Logging configuration for the application.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional

from .config import config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Use config values if not provided
    log_level = log_level or config.log_level
    log_file = log_file or config.log_file
    max_bytes = max_bytes or config.max_log_size_mb * 1024 * 1024
    backup_count = backup_count or config.backup_count
    
    # Check if we're running in AWS Lambda
    is_lambda = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (always add)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (only if not in Lambda and log_file is specified)
    if not is_lambda and log_file:
        try:
            log_path = Path(log_file)
            # Only try to create directory if it's not a Lambda environment
            if not is_lambda:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            # If we can't create the log file, just log to console
            logging.warning(f"Could not create log file {log_file}: {e}")
    
    # Set specific logger levels to reduce noise
    # External libraries - set to WARNING or ERROR only
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('boto3').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('s3transfer').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('httpcore').setLevel(logging.ERROR)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('redis').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    # Application-specific loggers - reduce verbose INFO logs
    logging.getLogger('src.crawler').setLevel(logging.WARNING)
    logging.getLogger('src.services.chat_service').setLevel(logging.WARNING)
    logging.getLogger('src.services.crawler_service').setLevel(logging.WARNING)
    logging.getLogger('src.services.auth_service').setLevel(logging.WARNING)
    logging.getLogger('src.services.document_service').setLevel(logging.WARNING)
    logging.getLogger('src.services.email_service').setLevel(logging.WARNING)
    logging.getLogger('src.services.aws_background_service').setLevel(logging.WARNING)
    logging.getLogger('src.utils.vector_store_demo').setLevel(logging.ERROR)
    
    # Only log important startup/shutdown messages
    if log_level.upper() == "INFO":
        logging.info(f"Logging configured - Level: {log_level}, File: {log_file if not is_lambda else 'console only'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Don't call setup_logging automatically - let the application decide when to call it
# setup_logging() 