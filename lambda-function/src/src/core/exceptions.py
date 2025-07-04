"""
Custom exceptions for Stock Market Crawler.
"""

from typing import Optional, Any, Dict


class StockCrawlerException(Exception):
    """Base exception for Stock Market Crawler."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(StockCrawlerException):
    """Authentication related errors."""
    pass


class AuthorizationError(StockCrawlerException):
    """Authorization related errors."""
    pass


class ValidationError(StockCrawlerException):
    """Data validation errors."""
    pass


class DatabaseError(StockCrawlerException):
    """Database related errors."""
    pass


class CrawlerError(StockCrawlerException):
    """Crawler related errors."""
    pass


class DocumentProcessingError(StockCrawlerException):
    """Document processing related errors."""
    pass


class StorageError(StockCrawlerException):
    """Storage related errors."""
    pass


class ConfigurationError(StockCrawlerException):
    """Configuration related errors."""
    pass


class ServiceUnavailableError(StockCrawlerException):
    """Service unavailable errors."""
    pass


class RateLimitError(StockCrawlerException):
    """Rate limiting errors."""
    pass


class NetworkError(StockCrawlerException):
    """Network related errors."""
    pass


class FileError(StockCrawlerException):
    """File operation errors."""
    pass


class ChatError(StockCrawlerException):
    """Chat related errors."""
    pass 