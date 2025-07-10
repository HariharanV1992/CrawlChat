# CrawlChat Crawler - Production Ready

A clean, organized web crawler for the CrawlChat application.

## 📁 Project Structure

```
crawlchat-crawler/
├── src/                    # Source code
│   ├── crawler/           # Core crawler modules
│   │   ├── advanced_crawler.py
│   │   ├── enhanced_scrapingbee_manager.py
│   │   ├── file_downloader.py
│   │   ├── link_extractor.py
│   │   ├── proxy_manager.py
│   │   ├── s3_cache_manager.py
│   │   ├── settings_manager.py
│   │   ├── smart_scrapingbee_manager.py
│   │   └── utils.py
│   └── lambda_handler.py  # AWS Lambda handler
├── config/                # Configuration files
├── docs/                  # Documentation
│   ├── CRAWLER_DOCUMENTATION.md
│   └── SCRAPINGBEE_PARAMETERS.md
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- AWS Lambda environment
- ScrapingBee API key

### Installation
```bash
pip install -r requirements.txt
```

### Environment Variables
```bash
SCRAPINGBEE_API_KEY=your_api_key_here
AWS_REGION=ap-south-1
```

## 🔧 Usage

### Lambda Function
The crawler is designed to run as an AWS Lambda function. The main entry point is `src/lambda_handler.py`.

### Local Development
```python
from src.crawler.advanced_crawler import AdvancedCrawler

# Initialize crawler
crawler = AdvancedCrawler(api_key="your_scrapingbee_api_key")

# Crawl a URL
result = crawler.crawl_url("https://example.com")
print(result)
```

## 📚 Documentation

- [Crawler Documentation](docs/CRAWLER_DOCUMENTATION.md)
- [ScrapingBee Parameters](docs/SCRAPINGBEE_PARAMETERS.md)

## 🏗️ Architecture

### Core Components
1. **AdvancedCrawler**: Main crawler class with progressive proxy strategy
2. **EnhancedScrapingBeeManager**: Handles ScrapingBee API interactions
3. **ProxyManager**: Manages different proxy modes (premium, stealth, own)
4. **FileDownloader**: Handles file downloads from URLs
5. **LinkExtractor**: Extracts links from crawled content

### Features
- ✅ Progressive proxy strategy (premium → stealth → own)
- ✅ JavaScript rendering support
- ✅ File download capabilities
- ✅ Screenshot functionality
- ✅ S3 caching
- ✅ Error handling and retry logic
- ✅ Usage statistics and cost tracking

## 🔄 Deployment

### Docker
```bash
docker build -t crawlchat-crawler .
docker run -e SCRAPINGBEE_API_KEY=your_key crawlchat-crawler
```

### AWS Lambda
1. Package the `src/` directory
2. Upload to AWS Lambda
3. Set environment variables
4. Configure triggers (API Gateway, SQS, etc.)

## 🧪 Testing

The crawler includes comprehensive error handling and logging. For testing specific scenarios, refer to the documentation files.

## 📝 License

This project is part of the CrawlChat application. 