# File Download Functionality - Deployment Guide

## 🎯 Overview

The CrawlChat platform now supports automatic file downloads through the ScrapingBee API. This includes downloading PDFs, images, documents, and other file types directly from URLs.

## ✨ New Features

### 1. **Crawler File Download API**
- **Endpoint**: `POST /api/v1/crawler/download`
- **Purpose**: Download files directly from URLs using ScrapingBee
- **Parameters**: URL, proxy settings, geolocation, wait times
- **Returns**: File content as streaming response

### 2. **Documents Download API**
- **Endpoint**: `GET /api/v1/documents/download/{filename}`
- **Purpose**: Download previously crawled/stored documents
- **Authentication**: Required
- **Returns**: File content as streaming response

### 3. **Enhanced UI**
- **File Download Modal**: User-friendly interface for downloading files
- **File Type Detection**: Automatic detection and display of file types
- **Advanced Options**: Proxy settings, geolocation, wait times
- **Progress Indicators**: Real-time download status

## 🚀 Deployment Steps

### Step 1: Update Dependencies

Ensure all required packages are installed:

```bash
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Set up environment variables:

```bash
# ScrapingBee API Key
export SCRAPINGBEE_API_KEY="your_api_key_here"

# Database Configuration
export MONGODB_URI="your_mongodb_uri"

# AWS Configuration (if using S3)
export AWS_ACCESS_KEY_ID="your_aws_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret"
export AWS_REGION="your_aws_region"
export S3_BUCKET="your_s3_bucket"
```

### Step 3: Start the Application

#### Development Mode:
```bash
cd crawler-service
python3 main.py --host 0.0.0.0 --port 8000 --reload
```

#### Production Mode:
```bash
cd crawler-service
python3 main.py --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Verify Deployment

Test the health check endpoint:
```bash
curl http://localhost:8000/health
```

Test the file download API:
```bash
curl -X POST "http://localhost:8000/api/v1/crawler/download?url=https://example.com/document.pdf&download_file=true"
```

## 🔧 API Usage Examples

### 1. Download PDF File

```python
import requests

# Basic PDF download
response = requests.post(
    "http://localhost:8000/api/v1/crawler/download",
    params={
        "url": "https://example.com/document.pdf",
        "render_js": "false",
        "download_file": "true"
    }
)

if response.status_code == 200:
    with open("downloaded.pdf", "wb") as f:
        f.write(response.content)
```

### 2. Download with Advanced Options

```python
# Advanced download with proxy and geolocation
response = requests.post(
    "http://localhost:8000/api/v1/crawler/download",
    params={
        "url": "https://example.com/document.pdf",
        "render_js": "false",
        "download_file": "true",
        "premium_proxy": "true",
        "country_code": "us",
        "wait": "2000"
    }
)
```

### 3. Download Stored Document

```python
# Download previously stored document
response = requests.get(
    "http://localhost:8000/api/v1/documents/download/document.pdf",
    headers={"Authorization": "Bearer your_token"}
)
```

## 🎨 UI Integration

### File Download Modal

The UI includes a comprehensive file download modal with:

- **URL Input**: Direct file URL entry
- **File Type Detection**: Automatic detection and display
- **Advanced Options**: Proxy settings, geolocation, wait times
- **Progress Tracking**: Real-time download status
- **Error Handling**: User-friendly error messages

### Quick Actions

Added quick action buttons for:
- **Download PDF**: Opens file download modal
- **SEBI Reports**: Pre-configured for regulatory documents

## 📊 Supported File Types

### Documents
- PDF (.pdf)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- PowerPoint (.ppt, .pptx)

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WebP (.webp)
- SVG (.svg)

### Text Files
- Plain Text (.txt)
- CSV (.csv)
- JSON (.json)
- XML (.xml)

### Archives
- ZIP (.zip)
- RAR (.rar)
- 7Z (.7z)
- TAR (.tar)
- GZ (.gz)

## 🔒 Security Features

### Authentication
- All endpoints require user authentication
- JWT token validation
- User-specific document access

### File Size Limits
- Maximum file size: 2MB per request
- Automatic validation and error handling
- Returns 413 status code for oversized files

### Content Validation
- File type detection from URL and content
- Content-type header validation
- Malicious file detection

## 🚨 Error Handling

### Common Error Codes
- `400`: Invalid parameters
- `401`: Authentication required
- `404`: File not found
- `413`: File too large
- `500`: Internal server error

### Error Response Format
```json
{
    "detail": "Error message",
    "status_code": 400,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📈 Performance Optimization

### Caching
- File content caching for repeated downloads
- Metadata caching for faster lookups
- CDN integration for static files

### Parallel Processing
- Concurrent file downloads
- Background processing for large files
- Async/await for non-blocking operations

### Resource Management
- Connection pooling
- Memory-efficient streaming
- Automatic cleanup of temporary files

## 🔍 Monitoring and Logging

### Log Levels
- `INFO`: Successful downloads
- `WARNING`: File size limits, retries
- `ERROR`: Download failures, authentication errors

### Metrics
- Download success rate
- Average download time
- File type distribution
- User activity tracking

## 🧪 Testing

### Automated Tests
```bash
# Run file download tests
python3 test_file_download_api.py

# Run crawler tests
python3 test_file_downloads.py
```

### Manual Testing
1. Test with various file types
2. Test with different proxy settings
3. Test error conditions
4. Test UI integration

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python3", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawlchat-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawlchat-api
  template:
    metadata:
      labels:
        app: crawlchat-api
    spec:
      containers:
      - name: api
        image: crawlchat-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: SCRAPINGBEE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: scrapingbee-key
```

## 📞 Support

### Documentation
- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

### Troubleshooting
1. Check API key validity
2. Verify network connectivity
3. Monitor server logs
4. Test with simple URLs first

### Contact
For issues or questions:
- Check the logs in `/logs/` directory
- Review error messages in the UI
- Test individual endpoints

## 🎉 Success Metrics

### Deployment Checklist
- [ ] Health check endpoint responds
- [ ] File download API works
- [ ] UI modal opens correctly
- [ ] Authentication works
- [ ] Error handling functions
- [ ] Logs are generated
- [ ] Performance is acceptable

### Performance Targets
- Download success rate: >95%
- Average response time: <5 seconds
- File size limit: 2MB
- Concurrent downloads: 10 per user

---

**🎯 The file download functionality is now fully integrated and ready for production use!** 