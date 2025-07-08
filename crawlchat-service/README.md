# CrawlChat - AI Document Analysis Platform

A comprehensive AI-powered document analysis and chat platform with advanced web crawling capabilities, intelligent document processing, and conversational AI insights.

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- GitHub repository with secrets configured
- Docker (for local development)

### Deployment

This project uses **GitHub Actions** for automated deployment. Simply push to the `main` branch to trigger deployment:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Required GitHub Secrets

Configure these secrets in your GitHub repository:

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `MONGODB_URI` - MongoDB connection string
- `SCRAPINGBEE_API_KEY` - ScrapingBee API key
- `OPENAI_API_KEY` - OpenAI API key
- `SECRET_KEY` - JWT secret key
- `PROXY_API_KEY` - Proxy service API key
- `CERTIFICATE_ARN` - SSL certificate ARN (optional)

## 🏗️ Architecture

### Core Components
- **Lambda Functions**: Container-based serverless functions
- **API Gateway**: RESTful API endpoints
- **S3**: Document storage and caching
- **MongoDB**: Data persistence
- **CloudFormation**: Infrastructure as Code

### Services
- **Crawler Service**: Advanced web crawling with S3 caching
- **Document Service**: Intelligent document processing
- **Chat Service**: AI-powered conversational interface
- **Auth Service**: User authentication and authorization

## 📁 Project Structure

```
crawlchat-service/
├── common/                 # Shared code and utilities
├── crawler-service/        # Crawler implementation
├── lambda-service/         # Lambda function code
├── ui/                     # Web interface templates
├── infra/                  # CloudFormation templates
└── .github/workflows/      # GitHub Actions workflows
```

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start local server
python -m uvicorn main:app --reload
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/test_crawler.py
```

## 📚 Documentation

- [Crawler Documentation](CRAWLER_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [How It Works](HOW_IT_WORKS.md)
- [Implementation Analysis](IMPLEMENTATION_GAP_ANALYSIS.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Push to trigger deployment
6. Create a pull request

## 📄 License

This project is licensed under the MIT License. 